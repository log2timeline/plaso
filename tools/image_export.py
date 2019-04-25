#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The image export command line tool."""

from __future__ import unicode_literals

import logging
import sys

from plaso.cli import image_export_tool
from plaso.lib import errors


def Main():
  """The main function.

  Returns:
    bool: True if successful or False otherwise.
  """
  tool = image_export_tool.ImageExportTool()

  if not tool.ParseArguments():
    return False

  if tool.list_signature_identifiers:
    tool.ListSignatureIdentifiers()
    return True

  if not tool.has_filters:
    logging.warning('No filter defined exporting all files.')

  # TODO: print more status information like PrintOptions.
  tool.PrintFilterCollection()

  try:
    tool.ProcessSources()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return False

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return False

  except errors.SourceScannerError as exception:
    logging.warning((
        'Unable to scan for a supported filesystem with error: {0!s}\n'
        'Most likely the image format is not supported by the '
        'tool.').format(exception))
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
