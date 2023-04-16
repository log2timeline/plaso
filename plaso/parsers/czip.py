# -*- coding: utf-8 -*-
"""This file contains a parser for compound ZIP files."""

import zipfile

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class CompoundZIPParser(interface.FileObjectParser):
  """Shared functionality for parsing compound ZIP files.

  Compound ZIP files are ZIP files used as containers to create another file
  format, as opposed to archives of unrelated files.
  """

  NAME = 'czip'
  DATA_FORMAT = 'Compound ZIP file'

  _plugin_classes = {}

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a compound ZIP file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    display_name = parser_mediator.GetDisplayName()

    if not zipfile.is_zipfile(file_object):
      raise errors.WrongParser(
          '[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, display_name, 'Not a Zip file.'))

    try:
      zip_file = zipfile.ZipFile(file_object, 'r', allowZip64=True)  # pylint: disable=consider-using-with

    # Some non-ZIP files return true for is_zipfile but will fail with another
    # error like a negative seek (IOError). Note that this function can raise
    # many different exceptions.
    except Exception as exception:  # pylint: disable=broad-except
      raise errors.WrongParser(
          '[{0:s}] unable to parse file: {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))

    for plugin_name, plugin in self._plugins_per_name.items():
      if parser_mediator.abort:
        break

      profiling_name = '/'.join([self.NAME, plugin.NAME])

      parser_mediator.SampleFormatCheckStartTiming(profiling_name)

      try:
        result = plugin.CheckRequiredPaths(zip_file)
      finally:
        parser_mediator.SampleFormatCheckStopTiming(profiling_name)

      if not result:
        logger.debug('Skipped parsing file: {0:s} with plugin: {1:s}'.format(
            display_name, plugin_name))
        continue

      logger.debug('Parsing file: {0:s} with plugin: {1:s}'.format(
          display_name, plugin_name))

      parser_mediator.SampleStartTiming(profiling_name)

      try:
        plugin.UpdateChainAndProcess(parser_mediator, zip_file=zip_file)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse ZIP file: {1:s} with error: '
            '{2!s}').format(plugin_name, display_name, exception))

      finally:
        parser_mediator.SampleStopTiming(profiling_name)

    zip_file.close()


manager.ParsersManager.RegisterParser(CompoundZIPParser)
