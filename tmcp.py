#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
tmcp --- Copy files/directories from a Time Machine backup

Written 2016-12-10 by Jadrian Miles (jadrian.org)

Please submit patches to https://github.com/jadrian/time-machine-copy
"""

from __future__ import print_function
import errno
import os
import os.path
import shutil
import sys

def tmcp(src, dst, archive=None):
  """Copies sources from a Time Machine directory into a destination.
  
  Arguments:
  - src (list of strings)
  - dst (string)
  - archive (string)
  
  Everything's a path: dst, archive, and all elements of src.  Each src path
  must be an existing file or directory.  If dst does not exist, it is created
  as a directory.  If archive is None, it is auto-detected from src.
  """
  # Ignore slashes and convert all arguments to absolute paths.
  src = [os.path.realpath(f) for f in src]
  dst = os.path.realpath(dst)
  
  # Find the archive directory.
  if archive is None:
    archive = _findArchive(src)
  elif not _isArchiveDir(archive):
    raise OSError('{0} is not an archive directory.'.format(archive))
  
  # Create dst if necessary.
  try:
    os.makedirs(dst)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(dst):
      pass  # Directory already exists.
    else:
      raise OSError(
        'Some portion of destination path {0} is an existing file.'.format(dst))
  
  # Make recursive copies for each src.
  for f in src:
    _copy(f, dst, archive)

def _copy(src, dst, archive):
  """Copies a single file or directory "src" into existing directory "dst"."""
  real_src = getOriginal(src, archive)
  if real_src is None:
    return
  
  copy_name = os.path.join(dst, os.path.basename(src))
  
  if os.path.isfile(real_src):
    shutil.copy2(real_src, copy_name)
  elif os.path.isdir(real_src):
    os.mkdir(copy_name)
    contents = os.listdir(real_src)
    for child in contents:
      _copy(os.path.join(real_src, child), copy_name, archive)
    shutil.copystat(real_src, copy_name)

def getOriginal(src, archive):
  if not os.path.exists(src):
    print('Path {0} does not exist.'.format(src), file=sys.stderr)
    return None
  return src

def _isArchiveDir(arch):
  return True

def _findArchive(src):
  return None

def _cliMain():
  """Parses command-line arguments and passes them into tmcp()."""
  import argparse
  
  # Check for the -H flag before parsing other arguments.
  prelim_parser = argparse.ArgumentParser(add_help=False)
  prelim_parser.add_argument(
    '-H', '--examples',
    action = 'store_true',
    help = 'print detailed help and exit')
  (args, _) = prelim_parser.parse_known_args()
  do_print_tutorial = args.examples
  
  # Build the parser for the complete set of arguments.
  parser = argparse.ArgumentParser(
    parents = [prelim_parser],
    description = 'Copy files/directories from a Time Machine backup.',
    formatter_class = argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
    'src', nargs = '+',
    help = 'source of copy')
  parser.add_argument(
    'dst',
    help = 'destination for copy')
  parser.add_argument(
    '-D', metavar = 'inodes_dir',
    help = 'path to Time Machine fake inode directory')
  
  # Print messages in special cases.
  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)
  if do_print_tutorial:
    parser.print_help()
    print(_tutorial(sys.argv[0]), file=sys.stderr)
    sys.exit(0)
  
  # Parse args and call the real function.
  args = parser.parse_args()
  try:
    tmcp(args.src, args.dst, args.D)
  except BaseException as exc:
    print('{0}: {1}'.format(type(exc).__name__, exc), file=sys.stderr)
    sys.exit(1)

def _tutorial(progname):
  import textwrap
  return textwrap.dedent("""
    If any "src" argument is a directory, the script recurses within that
    directory.
    
    The "dst" argument must be a directory.  If it does not already exist, it
    will be created automatically.  All copied files (and directory trees)
    will be written within the "dst" directory.  (Note that this means there is
    no mechanism for renaming the destination copy, even if only a single "src"
    file is given.)
    
    Trailing slashes are ignored (and unnecessary) on all arguments.
    
    To explore some usage examples, say we have the following directory
    hierarchy:
    
      .
      ├╴tmbackup
      │ ├╴.HFS+ Private Directory Data?
      │ └╴2012-01-31-083451
      │   ├╴Foo.txt
      │   ├╴Bar.txt              **
      │   └╴Music
      │     ├╴Nirvana
      │     │ ├╴in_bloom.mp3     **
      │     │ └╴teen_spirit.mp3
      │     └╴U2                 **
      └╴rescue
    
    In our example, the files marked with asterisks are empty placeholder files
    that refer to real files stored within the ".HFS+ Private..." directory.
    The file "U2" is a placeholder for a whole directory, which (on the original
    backed-up computer) had two files in it: bloody_sunday.mp3 and
    with_or_without_you.mp3.
    
    Each of the following usage examples is a command, followed by the directory
    hierarchy that results from running that command.
    
    {0} tmbackup/2012-01-31-083451/Music/Nirvana rescue
      .
      ├╴tmbackup      (unchanged)
      └╴rescue
        └╴Nirvana
          ├╴in_bloom.mp3
          └╴teen_spirit.mp3
    
    {0} tmbackup/2012-01-31-083451/Music .
      .
      ├╴tmbackup      (unchanged)
      ├╴rescue        (unchanged; empty)
      └╴Music
        ├╴Nirvana
        │ ├╴in_bloom.mp3
        │ └╴teen_spirit.mp3
        └╴U2
          ├╴bloody_sunday.mp3
          └╴with_or_without_you.mp3
    
    {0} tmbackup/2012-01-31-083451 full_backup
      .
      ├╴tmbackup      (unchanged)
      ├╴rescue        (unchanged; empty)
      └╴full_backup   (newly-created dir)
        └╴2012-01-31-083451
          ├╴Foo.txt
          ├╴Bar.txt
          └╴Music
            ├╴Nirvana
            │ ├╴in_bloom.mp3
            │ └╴teen_spirit.mp3
            └╴U2
              ├╴bloody_sunday.mp3
              └╴with_or_without_you.mp3
    """).format(progname)

if __name__ == '__main__':
  _cliMain()
