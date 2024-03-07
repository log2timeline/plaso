#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The image export command line tool."""

import logging
import multiprocessing
import os
import sys

from plaso import dependencies
from plaso.cli import image_export_tool
from plaso.lib import errors


def Main():
  """Entry point of console script to extract files from images.

  Returns:
    int: exit code that is provided to sys.exit().
  """
  tool = image_export_tool.ImageExportTool()

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

  if tool.list_signature_identifiers:
    try:
      tool.ListSignatureIdentifiers()

    # BadConfigOption will be raised if signatures.conf cannot be found.
    except errors.BadConfigOption as exception:
      logging.warning(exception)
      return 1

    return 0

  if not tool.has_filters:
    logging.warning('No filter defined exporting all files.')

  # TODO: print more status information like PrintOptions.
  tool.PrintFilterCollection()

  try:
    tool.ProcessSource()

  # Writing to stdout and stderr will raise BrokenPipeError if it
  # receives a SIGPIPE.
  except BrokenPipeError:
    pass

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning('Aborted by user.')
    return 1

  except errors.BadConfigOption as exception:
    logging.warning(exception)
    return 1

  except errors.SourceScannerError as exception:
    logging.warning((
        'Unable to scan for a supported file system with error: {0!s}\n'
        'Most likely the image format is not supported by the '
        'tool.').format(exception))
    return 1

  return 0


if __name__ == '__main__':
  # For PyInstaller sake we need to define this directly after "__main__".
  # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
  multiprocessing.freeze_support()

  sys.exit(Main())
