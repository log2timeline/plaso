#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Psteal (Plaso SýndarheimsTímalína sem Er ALgjörlega sjálfvirk).

Psteal combines the log2timeline and psort tools into a single tool.
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
  """Entry point of console script to extract and output events.

  Returns:
    int: exit code that is provided to sys.exit().
  """
  tool = psteal_tool.PstealTool()

  if not tool.ParseArguments(sys.argv[1:]):
    return 1

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
    return 0

  try:
    tool.CheckOutDated()
  except KeyboardInterrupt:
    return 1

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
    return 0

  if tool.dependencies_check and not dependencies.CheckDependencies(
      verbose_output=False):
    return 1

  try:
    tool.ExtractEventsFromSources()
    tool.ProcessStorage()

  # Writing to stdout and stderr will raise BrokenPipeError if it
  # receives a SIGPIPE.
  except BrokenPipeError:
    pass

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return 1

  except errors.SourceScannerError as exception:
    logging.warning(exception)
    return 1

  return 0


if __name__ == '__main__':
  # For PyInstaller sake we need to define this directly after "__main__".
  # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
  multiprocessing.freeze_support()

  sys.exit(Main())
