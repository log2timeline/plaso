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

from __future__ import unicode_literals

import multiprocessing
import logging
import sys

from plaso.cli import psteal_tool
from plaso.lib import errors


def Main():
  """The main function."""
  multiprocessing.freeze_support()

  tool = psteal_tool.PstealTool()
  if not tool.ParseArguments():
    return False

  have_list_option = False

  if tool.list_timezones:
    tool.ListTimeZones()
    have_list_option = True

  if tool.list_output_modules:
    tool.ListOutputModules()
    have_list_option = True

  if tool.list_timezones:
    tool.ListTimeZones()
    have_list_option = True

  if tool.list_parsers_and_plugins:
    tool.ListParsersAndPlugins()
    have_list_option = True

  if tool.list_hashers:
    tool.ListHashers()
    have_list_option = True

  if tool.list_language_identifiers:
    tool.ListLanguageIdentifiers()
    have_list_option = True

  if have_list_option:
    return True

  try:
    tool.ExtractEventsFromSources()
    tool.AnalyzeEvents()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return False

  except errors.SourceScannerError as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
