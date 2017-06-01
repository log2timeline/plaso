#!/usr/bin/python
# -*- coding: utf-8 -*-
"""A simple dump information gathered from a plaso storage container.

pinfo stands for Plaso INniheldurFleiriOrd or plaso contains more words.
"""

import logging
import sys

from plaso.cli import pinfo_tool
from plaso.lib import errors


def Main():
  """The main function."""
  tool = pinfo_tool.PinfoTool()

  if not tool.ParseArguments():
    return False

  result = True
  try:
    if tool.compare_storage_information:
      result = tool.CompareStorages()
    else:
      tool.PrintStorageInformation()

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return False

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
