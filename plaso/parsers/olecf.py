# -*- coding: utf-8 -*-
"""Parser for OLE Compound Files (OLECF)."""

import pyolecf

from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class OLECFParser(interface.FileObjectParser):
  """Parses OLE Compound Files (OLECF)."""

  # pylint: disable=no-member

  NAME = 'olecf'
  DATA_FORMAT = 'OLE Compound File (OLECF) format'

  _INITIAL_FILE_OFFSET = None

  _plugin_classes = {}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)

    # OLECF
    format_specification.AddNewSignature(
        b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', offset=0)

    # OLECF beta
    format_specification.AddNewSignature(
        b'\x0e\x11\xfc\x0d\xd0\xcf\x11\x0e', offset=0)

    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an OLE Compound File (OLECF) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.
    """
    code_page = parser_mediator.GetCodePage()

    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(code_page)

    try:
      olecf_file.open_file_object(file_object)
    except (IOError, TypeError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    root_item = olecf_file.root_item
    if not root_item:
      return

    display_name = parser_mediator.GetDisplayName()

    # Get a list of all items in the root item from the OLECF file.
    item_names = [item.name for item in root_item.sub_items]

    # Compare the list of available plugin objects.
    # We will try to use every plugin against the file (except
    # the default plugin) and run it. Only if none of the plugins
    # works will we use the default plugin.

    item_names = frozenset(item_names)

    try:
      for plugin_name, plugin in self._plugins_per_name.items():
        if parser_mediator.abort:
          break

        profiling_name = '/'.join([self.NAME, plugin.NAME])

        parser_mediator.SampleFormatCheckStartTiming(profiling_name)

        try:
          result = plugin.REQUIRED_ITEMS.issubset(item_names)
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
          plugin.UpdateChainAndProcess(parser_mediator, root_item=root_item)

        except Exception as exception:  # pylint: disable=broad-except
          parser_mediator.ProduceExtractionWarning((
              'plugin: {0:s} unable to parse OLECF file with error: '
              '{1!s}').format(plugin_name, exception))

        finally:
          parser_mediator.SampleStopTiming(profiling_name)

      if self._default_plugin and not parser_mediator.abort:
        profiling_name = '/'.join([self.NAME, self._default_plugin.NAME])

        parser_mediator.SampleStartTiming(profiling_name)

        try:
          self._default_plugin.UpdateChainAndProcess(
              parser_mediator, root_item=root_item)

        except Exception as exception:  # pylint: disable=broad-except
          parser_mediator.ProduceExtractionWarning((
              'plugin: {0:s} unable to parse OLECF file with error: '
              '{1!s}').format(self._default_plugin_name, exception))

        finally:
          parser_mediator.SampleStopTiming(profiling_name)

    finally:
      olecf_file.close()


manager.ParsersManager.RegisterParser(OLECFParser)
