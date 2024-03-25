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

  _CATEGORY_FOOTER_SIGNATURE = b'\xab\xfb\xbf\xba'

  _LNK_GUID = (
      b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46')

  def _ParseCategoryHeader(self, file_object, file_offset):
    """Parse a category header.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the category header relative to the start of
          the file.

    Returns:
      tuple[custom_category_header, int]: category header and the number of
          bytes read.

    Raises:
      ParseError: if the category header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('custom_category_header')

    category_header, bytes_read = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    if category_header.category_type > 2:
      raise errors.ParseError(
          f'Unsupported category type: {category_header.category_type:d}.')

    file_offset += bytes_read
    total_bytes_read = bytes_read

    data_type_map = self._GetDataTypeMap(
        f'custom_category_header_type_{category_header.category_type:d}')

    category_header_value, bytes_read = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    if category_header.category_type in (0, 2):
      setattr(category_header, 'number_of_entries',
              category_header_value.number_of_entries)

    total_bytes_read += bytes_read

    return category_header, total_bytes_read

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

    display_name = f'{file_entry.name:s} # 0x{file_offset:08x}'

    try:
      lnk_file_object = resolver.Resolver.OpenFileObject(
          path_spec, resolver_context=parser_mediator.resolver_context)
    except (dfvfs_errors.BackEndError, RuntimeError) as exception:
      parser_mediator.ProduceExtractionWarning((
          f'unable to open LNK file: {display_name:s} with error: '
          f'{exception!s}'))
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
    file_size = file_object.get_size()

    file_header_map = self._GetDataTypeMap('custom_file_header')

    try:
      file_header, file_offset = self._ReadStructureFromFileObject(
          file_object, 0, file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser((
          f'Invalid Custom Destination: {display_name:s} - unable to parse '
          f'file header with error: {exception!s}'))

    entry_header_data_type_map = self._GetDataTypeMap('custom_entry_header')
    category_footer_data_type_map = self._GetDataTypeMap(
        'custom_category_footer')

    for _ in range(file_header.number_of_categories):
      try:
        category_header, bytes_read = self._ParseCategoryHeader(
            file_object, file_offset)
      except (ValueError, errors.ParseError) as exception:
        raise errors.WrongParser((
            'Invalid Custom Destination: {display_name:s} - unable to parse '
            f'category header with error: {exception!s}'))

      file_offset += bytes_read

      number_of_entries = getattr(category_header, 'number_of_entries', 0)
      for entry_index in range(number_of_entries):
        if file_size - file_offset < 16:
          break

        try:
          entry_header, _ = self._ReadStructureFromFileObject(
              file_object, file_offset, entry_header_data_type_map)

        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning((
              f'unable to parse entry header at offset: 0x{file_offset:08x} '
              f'with error: {exception!s}'))
          break

        if entry_header.guid == self._LNK_GUID:
          file_offset += 16

          remaining_file_size = file_size - file_offset

          lnk_file_size = self._ParseLNKFile(
              parser_mediator, file_entry, file_offset, remaining_file_size)

          file_offset += lnk_file_size

        elif entry_header.guid[:4] != self._CATEGORY_FOOTER_SIGNATURE:
          parser_mediator.ProduceExtractionWarning((
              f'unsupported entry: {entry_index:d} at offset: '
              f'0x{file_offset:08x}'))
          break

        file_object.seek(file_offset, os.SEEK_SET)

      try:
        _, bytes_read = self._ReadStructureFromFileObject(
            file_object, file_offset, category_footer_data_type_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.WrongParser((
            f'Invalid Custom Destination: {display_name:s} - unable to parse '
            f'category footer with error: {exception!s}'))

      file_offset += 4


manager.ParsersManager.RegisterParser(CustomDestinationsParser)
