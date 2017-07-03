#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Psort (Plaso Síar Og Raðar Þessu) - Makes output from Plaso Storage files.

Sample Usage:
  psort.py /tmp/mystorage.dump "date > '01-06-2012'"

See additional details here:
  https://github.com/log2timeline/plaso/wiki/Using-psort
"""

import multiprocessing
import logging
import sys

from plaso.cli import tools as cli_tools
from plaso.cli import psort_tool
from plaso.lib import errors


def Main():
  """The main function."""
  multiprocessing.freeze_support()

  input_reader = cli_tools.StdinInputReader()
  tool = psort_tool.PsortTool(input_reader=input_reader)

  if not tool.ParseArguments():
    return False

  have_list_option = False
  if tool.list_analysis_plugins:
    tool.ListAnalysisPlugins()
    have_list_option = True

  if tool.list_output_modules:
    tool.ListOutputModules()
    have_list_option = True

  if tool.list_language_identifiers:
    tool.ListLanguageIdentifiers()
    have_list_option = True

  if tool.list_timezones:
    tool.ListTimeZones()
    have_list_option = True

  if have_list_option:
    return True

  try:
    tool.ProcessStorage()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
