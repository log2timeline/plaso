#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The image export command line tool."""

import logging
import sys

from plaso.cli import image_export_tool
from plaso.lib import errors


def Main():
  """The main function."""
  tool = image_export_tool.ImageExportTool()

  if not tool.ParseArguments():
    return False

  if tool.list_signature_identifiers:
    tool.ListSignatureIdentifiers()
    return True

  if not tool.has_filters:
    logging.warning(u'No filter defined exporting all files.')

  # TODO: print more status information like PrintOptions.
  tool.PrintFilterCollection()

  try:
    tool.ProcessSources()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return False

  except errors.SourceScannerError as exception:
    logging.warning((
        u'Unable to scan for a supported filesystem with error: {0:s}\n'
        u'Most likely the image format is not supported by the '
        u'tool.').format(exception))
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
