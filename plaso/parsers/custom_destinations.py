# -*- coding: utf-8 -*-
"""Parser for .customDestinations-ms files."""

import logging
import os

import construct
from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import winlnk


class CustomDestinationsParser(interface.SingleFileBaseParser):
  """Parses .customDestinations-ms files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'custom_destinations'
  DESCRIPTION = u'Parser for *.customDestinations-ms files.'

  # We cannot use the parser registry here since winlnk could be disabled.
  # TODO: see if there is a more elegant solution for this.
  _WINLNK_PARSER = winlnk.WinLnkParser()

  _LNK_GUID = '\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46'

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


  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    # There's a backslash in the class docstring, so as not to confuse Sphinx.
    # pylint: disable=anomalous-backslash-in-string
    """Parses a \*.customDestinations-ms file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)
    try:
      file_header = self._FILE_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile((
          u'Unable to parse Custom Destination file header with error: '
          u'{0:s}').format(exception))

    if file_header.unknown1 != 2:
      raise errors.UnableToParseFile((
          u'Unsupported Custom Destination file - invalid unknown1: '
          u'{0:d}.').format(file_header.unknown1))

    if file_header.header_values_type > 2:
      raise errors.UnableToParseFile((
          u'Unsupported Custom Destination file - invalid header value type: '
          u'{0:d}.').format(file_header.header_values_type))

    if file_header.header_values_type == 0:
      data_structure = self._HEADER_VALUE_TYPE_0
    else:
      data_structure = self._HEADER_VALUE_TYPE_1_OR_2

    try:
      _ = data_structure.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile((
          u'Unable to parse Custom Destination file header value with error: '
          u'{0:s}').format(exception))

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
              u'Unable to parse Custom Destination file entry header with '
              u'error: {0:s}').format(exception))
        else:
          logging.warning((
              u'Unable to parse Custom Destination file entry header with '
              u'error: {0:s}').format(exception))
        break

      if entry_header.guid != self._LNK_GUID:
        if not first_guid_checked:
          raise errors.UnableToParseFile(
              u'Unsupported Custom Destination file - invalid entry header.')
        else:
          logging.warning(
              u'Unsupported Custom Destination file - invalid entry header.')
        break

      first_guid_checked = True
      file_offset += 16
      remaining_file_size -= 16

      path_spec = path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_DATA_RANGE, range_offset=file_offset,
          range_size=remaining_file_size,
          parent=parser_mediator.GetFileEntry().path_spec)

      try:
        lnk_file_object = resolver.Resolver.OpenFileObject(path_spec)
      except RuntimeError as exception:
        message = u'Unable to open LNK file with error {0:s}'.format(exception)
        parser_mediator.ProduceParseError(message)
        return

      display_name = u'{0:s} # 0x{1:08x}'.format(
          parser_mediator.GetFileEntry().name, file_offset)

      self._WINLNK_PARSER.UpdateChainAndParseFileObject(
          parser_mediator, lnk_file_object, display_name=display_name)

      # We cannot trust the file size in the LNK data so we get the last offset
      # that was read instead.
      lnk_file_size = lnk_file_object.get_offset()

      lnk_file_object.close()

      file_offset += lnk_file_size
      remaining_file_size -= lnk_file_size

      file_object.seek(file_offset, os.SEEK_SET)

    try:
      file_footer = self._FILE_FOOTER.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      logging.warning((
          u'Unable to parse Custom Destination file footer with error: '
          u'{0:s}').format(exception))

    if file_footer.signature != 0xbabffbab:
      logging.warning(
          u'Unsupported Custom Destination file - invalid footer signature.')


manager.ParsersManager.RegisterParser(CustomDestinationsParser)
