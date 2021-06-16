#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A simple dump information gathered from a plaso storage container.

pinfo stands for Plaso INniheldurFleiriOrd or plaso contains more words.
"""

import logging
import multiprocessing
import os
import sys

from plaso import dependencies
from plaso.cli import pinfo_tool
from plaso.lib import errors


def Main():
  """The main function."""
  tool = pinfo_tool.PinfoTool()

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
  if tool.list_reports:
    tool.ListReports()
    have_list_option = True

  if tool.list_sections:
    tool.ListSections()
    have_list_option = True

  if have_list_option:
    return True

  result = True
  try:
    if tool.compare_storage_information:
      result = tool.CompareStores()
    elif tool.generate_report:
      tool.GenerateReport()
    else:
      tool.PrintStorageInformation()

  # Writing to stdout and stderr will raise BrokenPipeError if it
  # receives a SIGPIPE.
  except BrokenPipeError:
    pass

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return False

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return False

  return result


if __name__ == '__main__':
  # For PyInstaller sake we need to define this directly after "__main__".
  # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
  multiprocessing.freeze_support()

  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
