# -*- coding: utf-8 -*-
"""Parser for custom destinations jump list (.customDestinations-ms) files."""

import os

from dfvfs.lib import definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver

from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import winlnk


class CustomDestinationsParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parses custom destinations jump list (.customDestinations-ms) files."""

  NAME = 'custom_destinations'
  DATA_FORMAT = 'Custom destinations jump list (.customDestinations-ms) file'

  _INITIAL_FILE_OFFSET = None

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'custom_destinations.yaml')

  # We cannot use the parser registry here since winlnk could be disabled.
  # TODO: see if there is a more elegant solution for this.
  _WINLNK_PARSER = winlnk.WinLnkParser()

  _LNK_GUID = (
      b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46')

  def _ParseLNKFile(
      self, parser_mediator, file_entry, file_offset, remaining_file_size):
    """Parses a LNK file stored within the .customDestinations-ms file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_entry (dfvfs.FileEntry): a file entry.
      file_offset (int): offset to the LNK file, relative to the start of the
          .customDestinations-ms file.
      remaining_file_size (int): size of the data remaining in the
          .customDestinations-ms file.

    Returns:
      int: size of the LNK file data or 0 if the LNK file could not be read.
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_DATA_RANGE, range_offset=file_offset,
        range_size=remaining_file_size, parent=file_entry.path_spec)

    display_name = '{0:s} # 0x{1:08x}'.format(file_entry.name, file_offset)

    try:
      lnk_file_object = resolver.Resolver.OpenFileObject(
          path_spec, resolver_context=parser_mediator.resolver_context)
    except (dfvfs_errors.BackEndError, RuntimeError) as exception:
      message = (
          'unable to open LNK file: {0:s} with error: {1!s}').format(
              display_name, exception)
      parser_mediator.ProduceExtractionWarning(message)
      return 0

    parser_mediator.AppendToParserChain(self._WINLNK_PARSER.NAME)
    try:
      lnk_file_object.seek(0, os.SEEK_SET)
      self._WINLNK_PARSER.ParseFileLNKFile(
          parser_mediator, lnk_file_object, display_name)
    finally:
      parser_mediator.PopFromParserChain()

    # We cannot trust the file size in the LNK data so we get the last offset
    # that was read instead.
    return lnk_file_object.get_offset()

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\xab\xfb\xbf\xba', offset=-4)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a .customDestinations-ms file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    file_entry = parser_mediator.GetFileEntry()
    display_name = parser_mediator.GetDisplayName()

    file_header_map = self._GetDataTypeMap('custom_file_header')

    try:
      file_header, file_offset = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser((
          'Invalid Custom Destination: {0:s} - unable to parse file header '
          'with error: {1!s}').format(display_name, exception))

    if file_header.unknown1 != 2:
      raise errors.WrongParser((
          'Unsupported Custom Destination file: {0:s} - invalid unknown1: '
          '{1:d}.').format(display_name, file_header.unknown1))

    if file_header.header_values_type > 2:
      raise errors.WrongParser((
          'Unsupported Custom Destination file: {0:s} - invalid header value '
          'type: {1:d}.').format(display_name, file_header.header_values_type))

    if file_header.header_values_type == 0:
      data_map_name = 'custom_file_header_value_type_0'
    else:
      data_map_name = 'custom_file_header_value_type_1_or_2'

    file_header_value_map = self._GetDataTypeMap(data_map_name)

    try:
      _, value_data_size = self._ReadStructureFromFileObject(
          file_object, file_offset, file_header_value_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser((
          'Invalid Custom Destination: {0:s} - unable to parse file header '
          'value with error: {1!s}').format(display_name, exception))

    file_offset += value_data_size
    file_size = file_object.get_size()
    remaining_file_size = file_size - file_offset

    entry_header_map = self._GetDataTypeMap('custom_entry_header')
    file_footer_map = self._GetDataTypeMap('custom_file_footer')

    # The Custom Destination file does not have a unique signature in
    # the file header that is why we use the first LNK class identifier (GUID)
    # as a signature.
    first_guid_checked = False
    while remaining_file_size > 4:
      try:
        entry_header, entry_data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, entry_header_map)

      except (ValueError, errors.ParseError) as exception:
        if not first_guid_checked:
          raise errors.WrongParser((
              'Invalid Custom Destination file: {0:s} - unable to parse '
              'entry header with error: {1!s}').format(
                  display_name, exception))

        parser_mediator.ProduceExtractionWarning(
            'unable to parse entry header with error: {0!s}'.format(
                exception))
        break

      if entry_header.guid != self._LNK_GUID:
        if not first_guid_checked:
          raise errors.WrongParser((
              'Unsupported Custom Destination file: {0:s} - invalid entry '
              'header signature offset: 0x{1:08x}.').format(
                  display_name, file_offset))

        try:
          # Check if we found the footer instead of an entry header.
          self._ReadStructureFromFileObject(
              file_object, file_offset, file_footer_map)

        except (ValueError, errors.ParseError) as exception:
          parser_mediator.ProduceExtractionWarning((
              'unable to parse footer at offset: 0x{0:08x} with error: '
              '{1!s}').format(file_offset, exception))
          break

        # TODO: add support for Jump List LNK file recovery.
        break

      first_guid_checked = True
      file_offset += entry_data_size
      remaining_file_size -= entry_data_size

      lnk_file_size = self._ParseLNKFile(
          parser_mediator, file_entry, file_offset, remaining_file_size)

      file_offset += lnk_file_size
      remaining_file_size -= lnk_file_size

    try:
      self._ReadStructureFromFileObject(
          file_object, file_offset, file_footer_map)

    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to parse footer at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))


manager.ParsersManager.RegisterParser(CustomDestinationsParser)
