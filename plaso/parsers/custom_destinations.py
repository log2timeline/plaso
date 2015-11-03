# -*- coding: utf-8 -*-
"""Parser for .customDestinations-ms files."""

import logging
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

  NAME = u'custom_destinations'
  DESCRIPTION = u'Parser for *.customDestinations-ms files.'

  # We cannot use the parser registry here since winlnk could be disabled.
  # TODO: see if there is a more elegant solution for this.
  _WINLNK_PARSER = winlnk.WinLnkParser()

  _LNK_GUID = (
      b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46')

  _FOOTER_SIGNATURE = 0xbabffbab

  _FILE_HEADER = construct.Struct(
      u'file_header',
      construct.ULInt32(u'unknown1'),
      construct.ULInt32(u'unknown2'),
      construct.ULInt32(u'unknown3'),
      construct.ULInt32(u'header_values_type'))

  _HEADER_VALUE_TYPE_0 = construct.Struct(
      u'header_value_type_0',
      construct.ULInt32(u'number_of_characters'),
      construct.String(u'string', lambda ctx: ctx.number_of_characters * 2),
      construct.ULInt32(u'unknown1'))

  _HEADER_VALUE_TYPE_1_OR_2 = construct.Struct(
      u'header_value_type_1_or_2',
      construct.ULInt32(u'unknown1'))

  _ENTRY_HEADER = construct.Struct(
      u'entry_header',
      construct.String(u'guid', 16))

  _FILE_FOOTER = construct.Struct(
      u'file_footer',
      construct.ULInt32(u'signature'))

  def _ParseLNKFile(
      self, parser_mediator, file_entry, file_offset, remaining_file_size):
    """Parses a LNK file stored within the .customDestinations-ms file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      file_offset: The offset of the LNK file data.
      remaining_file_size: The size of the data remaining in the
                           .customDestinations-ms file.

    Returns:
      The size of the LNK file data or 0 if the LNK file could not be read.
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_DATA_RANGE, range_offset=file_offset,
        range_size=remaining_file_size, parent=file_entry.path_spec)

    display_name = u'{0:s} # 0x{1:08x}'.format(file_entry.name, file_offset)

    try:
      lnk_file_object = resolver.Resolver.OpenFileObject(path_spec)
    except (dfvfs_errors.BackEndError, RuntimeError) as exception:
      message = (
          u'Unable to open LNK file: {0:s} with error {1:s}').format(
              display_name, exception)
      parser_mediator.ProduceParseError(message)
      return 0

    self._WINLNK_PARSER.Parse(
        parser_mediator, lnk_file_object, display_name=display_name)

    # We cannot trust the file size in the LNK data so we get the last offset
    # that was read instead.
    lnk_file_size = lnk_file_object.get_offset()

    lnk_file_object.close()

    return lnk_file_size

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a .customDestinations-ms file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

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
          u'Invalid Custom Destination: {0:s} - unable to parse '
          u'file header with error: {1:s}').format(display_name, exception))

    if file_header.unknown1 != 2:
      raise errors.UnableToParseFile((
          u'Unsupported Custom Destination file: {0:s} - invalid unknown1: '
          u'{1:d}.').format(display_name, file_header.unknown1))

    if file_header.header_values_type > 2:
      raise errors.UnableToParseFile((
          u'Unsupported Custom Destination file: {0:s} - invalid header value '
          u'type: {1:d}.').format(display_name, file_header.header_values_type))

    if file_header.header_values_type == 0:
      data_structure = self._HEADER_VALUE_TYPE_0
    else:
      data_structure = self._HEADER_VALUE_TYPE_1_OR_2

    try:
      _ = data_structure.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile((
          u'Invalid Custom Destination file: {0:s} - unable to parse '
          u'header value with error: {1:s}').format(
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
        error_message = (
            u'Invalid Custom Destination file: {0:s} - unable to parse '
            u'entry header with error: {1:s}').format(
                display_name, exception)

        if not first_guid_checked:
          raise errors.UnableToParseFile(error_message)

        logging.warning(error_message)
        break

      if entry_header.guid != self._LNK_GUID:
        error_message = (
            u'Unsupported Custom Destination file: {0:s} - invalid entry '
            u'header.').format(display_name)

        if not first_guid_checked:
          raise errors.UnableToParseFile(error_message)

        file_object.seek(-16, os.SEEK_CUR)
        try:
          file_footer = self._FILE_FOOTER.parse_stream(file_object)
        except (IOError, construct.FieldError) as exception:
          raise IOError((
              u'Unable to parse file footer at offset: 0x{0:08x} '
              u'with error: {1:s}').format(file_offset, exception))

        if file_footer.signature != self._FOOTER_SIGNATURE:
          logging.warning(error_message)

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
    except (IOError, construct.FieldError) as exception:
      logging.warning((
          u'Invalid Custom Destination file: {0:s} - unable to parse '
          u'footer with error: {1:s}').format(display_name, exception))

    if file_footer.signature != self._FOOTER_SIGNATURE:
      logging.warning((
          u'Unsupported Custom Destination file: {0:s} - invalid footer '
          u'signature.').format(display_name))


manager.ParsersManager.RegisterParser(CustomDestinationsParser)
