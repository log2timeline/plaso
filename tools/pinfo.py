#!/usr/bin/python
# -*- coding: utf-8 -*-
"""A simple dump information gathered from a plaso storage container.

pinfo stands for Plaso INniheldurFleiriOrd or plaso contains more words.
"""

import argparse
import logging
import sys

from plaso.frontend import pinfo
from plaso.lib import errors


def Main():
  """Start the tool."""
  front_end = pinfo.PinfoFrontend()

  usage = """
Gives you information about the storage file, how it was
collected, what information was gained from the image, etc.
  """
  arg_parser = argparse.ArgumentParser(description=usage)

  format_str = '[%(levelname)s] %(message)s'
  logging.basicConfig(level=logging.INFO, format=format_str)

  arg_parser.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help='Be extra verbose in the information printed out.')

  front_end.AddStorageFileOptions(arg_parser)

  options = arg_parser.parse_args()

  try:
    front_end.ParseOptions(options)
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error(u'{0:s}'.format(exception))
    return False

  storage_information_found = False
  for storage_information in front_end.GetStorageInformation():
    storage_information_found = True
    print storage_information.encode(front_end.preferred_encoding)

  if not storage_information_found:
    print u'No Plaso storage information found.'

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
