#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Psteal (Plaso SýndarheimsTímalína sem Er ALgjörlega sjálfvirk).

Psteal Combines the log2timeline and psort tools into a single tool.
Currently doesn't support any of the two tools flags.

Sample Usage:
  psteal.py --source=/tmp/mystorage.dump --write=/tmp/mystorage_timeline.csv

See additional details here:
  https://plaso.readthedocs.io/en/latest/sources/user/Creating-a-timeline.html#using-psteal
"""

import multiprocessing
import logging
import os
import sys

from plaso import dependencies
from plaso.cli import psteal_tool
from plaso.lib import errors


def Main():
  """The main function."""
  tool = psteal_tool.PstealTool()

  if not tool.ParseArguments(sys.argv[1:]):
    return False

  if tool.show_troubleshooting:
    print('Using Python version {0!s}'.format(sys.version))
    print()
    print('Path: {0:s}'.format(os.path.abspath(__file__)))
    print()
    print(tool.GetVersionInformation())
    print()
    dependencies.CheckDependencies(verbose_output=True)

    print('Also see: https://plaso.readthedocs.io/en/latest/sources/user/'
          'Troubleshooting.html')
    return True

  try:
    tool.CheckOutDated()
  except KeyboardInterrupt:
    return False

  have_list_option = False
  if tool.list_archive_types:
    tool.ListArchiveTypes()
    have_list_option = True

  if tool.list_hashers:
    tool.ListHashers()
    have_list_option = True

  if tool.list_language_tags:
    tool.ListLanguageTags()
    have_list_option = True

  if tool.list_output_modules:
    tool.ListOutputModules()
    have_list_option = True

  if tool.list_parsers_and_plugins:
    tool.ListParsersAndPlugins()
    have_list_option = True

  if tool.list_time_zones:
    tool.ListTimeZones()
    have_list_option = True

  if have_list_option:
    return True

  if tool.dependencies_check and not dependencies.CheckDependencies(
      verbose_output=False):
    return False

  try:
    tool.ExtractEventsFromSources()
    tool.ProcessStorage()

  # Writing to stdout and stderr will raise BrokenPipeError if it
  # receives a SIGPIPE.
  except BrokenPipeError:
    pass

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return False

  except errors.SourceScannerError as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  # For PyInstaller sake we need to define this directly after "__main__".
  # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
  multiprocessing.freeze_support()

  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
