# -*- coding: utf-8 -*-
"""Parser for .customDestinations-ms files."""

from __future__ import unicode_literals

import os

import construct
from dfvfs.lib import definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import winlnk


class CustomDestinationsParser(interface.FileObjectParser):
  """Parses .customDestinations-ms files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'custom_destinations'
  DESCRIPTION = 'Parser for *.customDestinations-ms files.'

  # We cannot use the parser registry here since winlnk could be disabled.
  # TODO: see if there is a more elegant solution for this.
  _WINLNK_PARSER = winlnk.WinLnkParser()

  _LNK_GUID = (
      b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46')

  _FOOTER_SIGNATURE = 0xbabffbab

  _FILE_HEADER = construct.Struct(
      'file_header',
      construct.ULInt32('unknown1'),
      construct.ULInt32('unknown2'),
      construct.ULInt32('unknown3'),
      construct.ULInt32('header_values_type'))

  _HEADER_VALUE_TYPE_0 = construct.Struct(
      'header_value_type_0',
      construct.ULInt32('number_of_characters'),
      construct.String('string', lambda ctx: ctx.number_of_characters * 2),
      construct.ULInt32('unknown1'))

  _HEADER_VALUE_TYPE_1_OR_2 = construct.Struct(
      'header_value_type_1_or_2',
      construct.ULInt32('unknown1'))

  _ENTRY_HEADER = construct.Struct(
      'entry_header',
      construct.String('guid', 16))

  _FILE_FOOTER = construct.Struct(
      'file_footer',
      construct.ULInt32('signature'))

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
      lnk_file_object = resolver.Resolver.OpenFileObject(path_spec)
    except (dfvfs_errors.BackEndError, RuntimeError) as exception:
      message = (
          'unable to open LNK file: {0:s} with error: {1!s}').format(
              display_name, exception)
      parser_mediator.ProduceExtractionError(message)
      return 0

    parser_mediator.AppendToParserChain(self._WINLNK_PARSER)
    try:
      lnk_file_object.seek(0, os.SEEK_SET)
      self._WINLNK_PARSER.ParseFileLNKFile(
          parser_mediator, lnk_file_object, display_name)
    finally:
      parser_mediator.PopFromParserChain()

    # We cannot trust the file size in the LNK data so we get the last offset
    # that was read instead.
    lnk_file_size = lnk_file_object.get_offset()

    lnk_file_object.close()

    return lnk_file_size

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a .customDestinations-ms file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_entry = parser_mediator.GetFileEntry()
    display_name = parser_mediator.GetDisplayName()

    file_object.seek(0, os.SEEK_SET)
    try:
      file_header = self._FILE_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile((
          'Invalid Custom Destination: {0:s} - unable to parse '
          'file header with error: {1!s}').format(display_name, exception))

    if file_header.unknown1 != 2:
      raise errors.UnableToParseFile((
          'Unsupported Custom Destination file: {0:s} - invalid unknown1: '
          '{1:d}.').format(display_name, file_header.unknown1))

    if file_header.header_values_type > 2:
      raise errors.UnableToParseFile((
          'Unsupported Custom Destination file: {0:s} - invalid header value '
          'type: {1:d}.').format(display_name, file_header.header_values_type))

    if file_header.header_values_type == 0:
      data_structure = self._HEADER_VALUE_TYPE_0
    else:
      data_structure = self._HEADER_VALUE_TYPE_1_OR_2

    try:
      data_structure.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile((
          'Invalid Custom Destination file: {0:s} - unable to parse '
          'header value with error: {1!s}').format(
              display_name, exception))

    file_size = file_object.get_size()
    file_offset = file_object.get_offset()
    remaining_file_size = file_size - file_offset

    # The Custom Destination file does not have a unique signature in
    # the file header that is why we use the first LNK class identifier (GUID)
    # as a signature.
    first_guid_checked = False
    while remaining_file_size > 4:
      try:
        entry_header = self._ENTRY_HEADER.parse_stream(file_object)
      except (IOError, construct.FieldError) as exception:
        if not first_guid_checked:
          raise errors.UnableToParseFile((
              'Invalid Custom Destination file: {0:s} - unable to parse '
              'entry header with error: {1!s}').format(
                  display_name, exception))

        parser_mediator.ProduceExtractionError(
            'unable to parse entry header with error: {0!s}'.format(
                exception))
        break

      if entry_header.guid != self._LNK_GUID:
        if not first_guid_checked:
          raise errors.UnableToParseFile((
              'Unsupported Custom Destination file: {0:s} - invalid entry '
              'header signature offset: 0x{1:08x}.').format(
                  display_name, file_offset))

        try:
          # Check if we found the footer instead of an entry header.
          file_object.seek(-16, os.SEEK_CUR)

          file_footer = self._FILE_FOOTER.parse_stream(file_object)

          if file_footer.signature != self._FOOTER_SIGNATURE:
            parser_mediator.ProduceExtractionError(
                'invalid entry header signature at offset: 0x{0:08x}'.format(
                    file_offset))

        except (IOError, construct.FieldError) as exception:
          parser_mediator.ProduceExtractionError((
              'unable to parse footer at offset: 0x{0:08x} with error: '
              '{1!s}').format(file_offset, exception))
          break

        file_object.seek(-4, os.SEEK_CUR)

        # TODO: add support for Jump List LNK file recovery.
        break

      first_guid_checked = True
      file_offset += 16
      remaining_file_size -= 16

      lnk_file_size = self._ParseLNKFile(
          parser_mediator, file_entry, file_offset, remaining_file_size)

      file_offset += lnk_file_size
      remaining_file_size -= lnk_file_size

      file_object.seek(file_offset, os.SEEK_SET)

    try:
      file_footer = self._FILE_FOOTER.parse_stream(file_object)

      if file_footer.signature != self._FOOTER_SIGNATURE:
        parser_mediator.ProduceExtractionError(
            'invalid footer signature at offset: 0x{0:08x}'.format(file_offset))

    except (IOError, construct.FieldError) as exception:
      parser_mediator.ProduceExtractionError((
          'unable to parse footer at offset: 0x{0:08x} with error: '
          '{1!s}').format(file_offset, exception))


manager.ParsersManager.RegisterParser(CustomDestinationsParser)
