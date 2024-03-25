#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The log2timeline command line tool."""

import logging
import multiprocessing
import os
import sys

from plaso import dependencies
from plaso.cli import log2timeline_tool
from plaso.lib import errors


def Main():
  """Entry point of console script to extract events.

  Returns:
    int: exit code that is provided to sys.exit().
  """
  tool = log2timeline_tool.Log2TimelineTool()

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

  if tool.show_info:
    tool.ShowInfo()
    return 0

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

  if tool.list_parsers_and_plugins:
    tool.ListParsersAndPlugins()
    have_list_option = True

  if tool.list_profilers:
    tool.ListProfilers()
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

  # Writing to stdout and stderr will raise BrokenPipeError if it
  # receives a SIGPIPE.
  except BrokenPipeError:
    pass

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return 1

  except (IOError, errors.BadConfigOption,
          errors.SourceScannerError) as exception:
    # Display message on stdout as well as the log file.
    print(exception)
    logging.error(exception)
    return 1

  return 0


if __name__ == '__main__':
  # For PyInstaller sake we need to define this directly after "__main__".
  # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
  multiprocessing.freeze_support()

  sys.exit(Main())
