#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Psteal (Plaso SýndarheimsTímalína sem Er ALgjörlega sjálfvirk).

Psteal Combines the log2timeline and psort tools into a single tool.
Currently doesn't support any of the two tools flags.

Sample Usage:
  psteal.py --source=/tmp/mystorage.dump --write=/tmp/mystorage_timeline.csv

See additional details here:
  https://github.com/log2timeline/plaso/wiki/Using-psteal
"""

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

  try:
    tool.ExtractEventsFromSources()
    tool.AnalyzeEvents()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
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
