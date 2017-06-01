# -*- coding: utf-8 -*-
"""Parser for Mac OS X Keychain files."""

# INFO: Only supports internet and application passwords,
#       because it is the only data that contains timestamp events.
#       Keychain can also store "secret notes". These notes are stored
#       in the same type than the application format, then, they are already
#       supported. The stored wifi are also application passwords.

# TODO: the AccessControl for each entry has not been implemented. Until now,
#       I know that the AccessControl from Internet and App password are stored
#       using other tables (Symmetric, certificates, etc). Access Control
#       indicates which specific tool, or all, is able to use this entry.


import binascii
import os

import construct

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import specification
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class KeychainInternetRecordEventData(events.EventData):
  """Mac OS X keychain internet record event data.

  Attributes:
    account_name (str): name of the account.
    comments (str): comments added by the user.
    entry_name (str): name of the entry.
    protocol (str): internet protocol used, for example "https".
    ssgp_hash (str): hexadecimal values from the password / cert hash.
    text_description (str): description.
    type_protocol (str): sub-protocol used, for example "form".
    where (str): domain name or IP where the password is used.
  """

  DATA_TYPE = u'mac:keychain:internet'

  def __init__(self):
    """Initializes event data."""
    super(KeychainInternetRecordEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.account_name = None
    self.comments = None
    self.entry_name = None
    self.protocol = None
    self.ssgp_hash = None
    self.text_description = None
    self.type_protocol = None
    self.where = None


# TODO: merge with KeychainInternetRecordEventData.
class KeychainApplicationRecordEventData(events.EventData):
  """Mac OS X keychain application password record event data.

  Attributes:
    account_name (str): name of the account.
    comments (str): comments added by the user.
    entry_name (str): name of the entry.
    ssgp_hash (str): hexadecimal values from the password / cert hash.
    text_description (str): description.
  """

  DATA_TYPE = u'mac:keychain:application'

  def __init__(self):
    """Initializes event data."""
    super(KeychainApplicationRecordEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.account_name = None
    self.comments = None
    self.entry_name = None
    self.ssgp_hash = None
    self.text_description = None


class KeychainParser(interface.FileObjectParser):
  """Parser for Keychain files."""

  NAME = u'mac_keychain'
  DESCRIPTION = u'Parser for Mac OS X Keychain files.'

  KEYCHAIN_SIGNATURE = b'kych'
  KEYCHAIN_MAJOR_VERSION = 1
  KEYCHAIN_MINOR_VERSION = 0

  RECORD_TYPE_APPLICATION = 0x80000000
  RECORD_TYPE_INTERNET = 0x80000001

  # DB HEADER.
  KEYCHAIN_DB_HEADER = construct.Struct(
      u'db_header',
      construct.Bytes(u'signature', 4),
      construct.UBInt16(u'major_version'),
      construct.UBInt16(u'minor_version'),
      construct.UBInt32(u'header_size'),
      construct.UBInt32(u'schema_offset'),
      construct.Padding(4))

  # DB SCHEMA.
  KEYCHAIN_DB_SCHEMA = construct.Struct(
      u'db_schema',
      construct.UBInt32(u'size'),
      construct.UBInt32(u'number_of_tables'))

  # For each number_of_tables, the schema has a TABLE_OFFSET with the
  # offset starting in the DB_SCHEMA.
  TABLE_OFFSET = construct.UBInt32(u'table_offset')

  TABLE_HEADER = construct.Struct(
      u'table_header',
      construct.UBInt32(u'table_size'),
      construct.UBInt32(u'record_type'),
      construct.UBInt32(u'number_of_records'),
      construct.UBInt32(u'first_record'),
      construct.UBInt32(u'index_offset'),
      construct.Padding(4),
      construct.UBInt32(u'recordnumbercount'))

  RECORD_HEADER = construct.Struct(
      u'record_header',
      construct.UBInt32(u'entry_length'),
      construct.Padding(12),
      construct.UBInt32(u'ssgp_length'),
      construct.Padding(4),
      construct.UBInt32(u'creation_time'),
      construct.UBInt32(u'last_modification_time'),
      construct.UBInt32(u'text_description'),
      construct.Padding(4),
      construct.UBInt32(u'comments'),
      construct.Padding(8),
      construct.UBInt32(u'entry_name'),
      construct.Padding(20),
      construct.UBInt32(u'account_name'),
      construct.Padding(4))

  RECORD_HEADER_APP = construct.Struct(
      u'record_entry_app',
      RECORD_HEADER,
      construct.Padding(4))

  RECORD_HEADER_INET = construct.Struct(
      u'record_entry_inet',
      RECORD_HEADER,
      construct.UBInt32(u'where'),
      construct.UBInt32(u'protocol'),
      construct.UBInt32(u'type'),
      construct.Padding(4),
      construct.UBInt32(u'url'))

  TEXT = construct.PascalString(
      u'text', length_field=construct.UBInt32(u'length'))

  TIME = construct.Struct(
      u'timestamp',
      construct.String(u'year', 4),
      construct.String(u'month', 2),
      construct.String(u'day', 2),
      construct.String(u'hour', 2),
      construct.String(u'minute', 2),
      construct.String(u'second', 2),
      construct.Padding(2))

  TYPE_TEXT = construct.String(u'type', 4)

  # TODO: add more protocols.
  _PROTOCOL_TRANSLATION_DICT = {
      u'htps': u'https',
      u'smtp': u'smtp',
      u'imap': u'imap',
      u'http': u'http'}

  def _ReadEntryApplication(self, parser_mediator, file_object):
    """Extracts the information from an application password entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    record_offset = file_object.tell()
    try:
      record_struct = self.RECORD_HEADER_APP.parse_stream(file_object)
    except (IOError, construct.FieldError):
      parser_mediator.ProduceExtractionError(
          u'unable to parse record structure at offset: 0x{0:08x}'.format(
              record_offset))
      return

    (ssgp_hash, creation_time, last_modification_time, text_description,
     comments, entry_name, account_name) = self._ReadEntryHeader(
         parser_mediator, file_object, record_struct.record_header,
         record_offset)

    # Move to the end of the record.
    next_record_offset = (
        record_offset + record_struct.record_header.entry_length)
    file_object.seek(next_record_offset, os.SEEK_SET)

    event_data = KeychainApplicationRecordEventData()
    event_data.account_name = account_name
    event_data.comments = comments
    event_data.entry_name = entry_name
    event_data.ssgp_hash = ssgp_hash
    event_data.text_description = text_description

    if creation_time:
      event = time_events.DateTimeValuesEvent(
          creation_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if last_modification_time:
      event = time_events.DateTimeValuesEvent(
          last_modification_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ReadEntryHeader(
      self, parser_mediator, file_object, record, record_offset):
    """Read the common record attributes.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_entry (dfvfs.FileEntry): a file entry object.
      file_object (dfvfs.FileIO): a file-like object.
      record (construct.Struct): record header structure.
      record_offset (int): offset of the start of the record.

    Returns:
      A tuple containing:
        ssgp_hash: Hash of the encrypted data (passwd, cert, note).
        creation_time (dfdatetime.TimeElements): entry creation time or None.
        last_modification_time ((dfdatetime.TimeElements): entry last
            modification time or None.
        text_description: A brief description of the entry.
        entry_name: Name of the entry
        account_name: Name of the account.
    """
    # TODO: reduce number of seeks and/or offset calculations needed
    # for parsing.

    # Info: The hash header always start with the string ssgp follow by
    #       the hash. Furthermore The fields are always a multiple of four.
    #       Then if it is not multiple the value is padded by 0x00.
    ssgp_hash = binascii.hexlify(file_object.read(record.ssgp_length)[4:])

    creation_time = None

    structure_offset = record_offset + record.creation_time - 1
    file_object.seek(structure_offset, os.SEEK_SET)

    try:
      time_structure = self.TIME.parse_stream(file_object)
    except construct.FieldError as exception:
      time_structure = None
      parser_mediator.ProduceExtractionError(
          u'unable to parse creation time with error: {0:s}'.format(exception))

    if time_structure:
      time_elements_tuple = (
          time_structure.year, time_structure.month, time_structure.day,
          time_structure.hour, time_structure.minute, time_structure.second)

      creation_time = dfdatetime_time_elements.TimeElements()
      try:
        creation_time.CopyFromStringTuple(
            time_elements_tuple=time_elements_tuple)
      except ValueError:
        creation_time = None
        parser_mediator.ProduceExtractionError(
            u'invalid creation time value: {0!s}'.format(time_elements_tuple))

    last_modification_time = None

    structure_offset = record_offset + record.last_modification_time - 1
    file_object.seek(structure_offset, os.SEEK_SET)

    try:
      time_structure = self.TIME.parse_stream(file_object)
    except construct.FieldError as exception:
      time_structure = None
      parser_mediator.ProduceExtractionError(
          u'unable to parse last modification time with error: {0:s}'.format(
              exception))

    if time_structure:
      time_elements_tuple = (
          time_structure.year, time_structure.month, time_structure.day,
          time_structure.hour, time_structure.minute, time_structure.second)

      last_modification_time = dfdatetime_time_elements.TimeElements()
      try:
        last_modification_time.CopyFromStringTuple(
            time_elements_tuple=time_elements_tuple)
      except ValueError:
        last_modification_time = None
        parser_mediator.ProduceExtractionError(
            u'invalid last modification time value: {0!s}'.format(
                time_elements_tuple))

    text_description = u'N/A'
    if record.text_description:
      structure_offset = record_offset + record.text_description - 1
      file_object.seek(structure_offset, os.SEEK_SET)

      try:
        text_description = self.TEXT.parse_stream(file_object)
      except construct.FieldError as exception:
        parser_mediator.ProduceExtractionError(
            u'unable to parse text description with error: {0:s}'.format(
                exception))

    comments = u'N/A'
    if record.comments:
      structure_offset = record_offset + record.comments - 1
      file_object.seek(structure_offset, os.SEEK_SET)

      try:
        comments = self.TEXT.parse_stream(file_object)
      except construct.FieldError as exception:
        parser_mediator.ProduceExtractionError(
            u'unable to parse comments with error: {0:s}'.format(exception))

    structure_offset = record_offset + record.entry_name - 1
    file_object.seek(structure_offset, os.SEEK_SET)

    try:
      entry_name = self.TEXT.parse_stream(file_object)
    except construct.FieldError as exception:
      entry_name = u'N/A'
      parser_mediator.ProduceExtractionError(
          u'unable to parse entry name with error: {0:s}'.format(exception))

    structure_offset = record_offset + record.account_name - 1
    file_object.seek(structure_offset, os.SEEK_SET)

    try:
      account_name = self.TEXT.parse_stream(file_object)
    except construct.FieldError as exception:
      account_name = u'N/A'
      parser_mediator.ProduceExtractionError(
          u'unable to parse account name with error: {0:s}'.format(exception))

    return (
        ssgp_hash, creation_time, last_modification_time,
        text_description, comments, entry_name, account_name)

  def _ReadEntryInternet(self, parser_mediator, file_object):
    """Extracts the information from an Internet password entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    record_offset = file_object.tell()
    try:
      record_header_struct = self.RECORD_HEADER_INET.parse_stream(file_object)
    except (IOError, construct.FieldError):
      parser_mediator.ProduceExtractionError((
          u'unable to parse record header structure at offset: '
          u'0x{0:08x}').format(record_offset))
      return

    (ssgp_hash, creation_time, last_modification_time, text_description,
     comments, entry_name, account_name) = self._ReadEntryHeader(
         parser_mediator, file_object, record_header_struct.record_header,
         record_offset)

    if not record_header_struct.where:
      where = u'N/A'
      protocol = u'N/A'
      type_protocol = u'N/A'

    else:
      offset = record_offset + record_header_struct.where - 1
      file_object.seek(offset, os.SEEK_SET)
      where = self.TEXT.parse_stream(file_object)

      offset = record_offset + record_header_struct.protocol - 1
      file_object.seek(offset, os.SEEK_SET)
      protocol = self.TYPE_TEXT.parse_stream(file_object)

      offset = record_offset + record_header_struct.type - 1
      file_object.seek(offset, os.SEEK_SET)
      type_protocol = self.TEXT.parse_stream(file_object)
      type_protocol = self._PROTOCOL_TRANSLATION_DICT.get(
          type_protocol, type_protocol)

      if record_header_struct.url:
        offset = record_offset + record_header_struct.url - 1
        file_object.seek(offset, os.SEEK_SET)
        url = self.TEXT.parse_stream(file_object)
        where = u'{0:s}{1:s}'.format(where, url)

    # Move to the end of the record.
    next_record_offset = (
        record_offset + record_header_struct.record_header.entry_length)
    file_object.seek(next_record_offset, os.SEEK_SET)

    event_data = KeychainInternetRecordEventData()
    event_data.account_name = account_name
    event_data.comments = comments
    event_data.entry_name = entry_name
    event_data.protocol = protocol
    event_data.ssgp_hash = ssgp_hash
    event_data.text_description = text_description
    event_data.type_protocol = type_protocol
    event_data.where = where

    if creation_time:
      event = time_events.DateTimeValuesEvent(
          creation_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if last_modification_time:
      event = time_events.DateTimeValuesEvent(
          last_modification_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ReadTableOffsets(self, parser_mediator, file_object):
    """Reads the table offsets.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Returns:
      list[int]: table offsets.
    """
    # INFO: The HEADER KEYCHAIN:
    # [DBHEADER] + [DBSCHEMA] + [OFFSET TABLE A] + ... + [OFFSET TABLE Z]
    # Where the table offset is relative to the first byte of the DB Schema,
    # then we must add to this offset the size of the [DBHEADER].
    # Read the database schema and extract the offset for all the tables.
    # They are ordered by file position from the top to the bottom of the file.
    table_offsets = []

    try:
      db_schema_struct = self.KEYCHAIN_DB_SCHEMA.parse_stream(file_object)
    except (IOError, construct.FieldError):
      parser_mediator.ProduceExtractionError(
          u'unable to parse database schema structure')
      return []

    for index in range(db_schema_struct.number_of_tables):
      try:
        table_offset = self.TABLE_OFFSET.parse_stream(file_object)
      except (IOError, construct.FieldError):
        parser_mediator.ProduceExtractionError(
            u'unable to parse table offsets: {0:d}'.format(index))
        return

      table_offsets.append(table_offset + self.KEYCHAIN_DB_HEADER.sizeof())

    return table_offsets

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        cls.KEYCHAIN_SIGNATURE, offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Mac OS X keychain file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      db_header = self.KEYCHAIN_DB_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError):
      raise errors.UnableToParseFile(u'Unable to parse file header.')

    if db_header.signature != self.KEYCHAIN_SIGNATURE:
      raise errors.UnableToParseFile(u'Not a Mac OS X keychain file.')

    if (db_header.major_version != self.KEYCHAIN_MAJOR_VERSION or
        db_header.minor_version != self.KEYCHAIN_MINOR_VERSION):
      parser_mediator.ProduceExtractionError(
          u'unsupported format version: {0:s}.{1:s}'.format(
              db_header.major_version, db_header.minor_version))
      return

    # TODO: document format and deterime if -1 offset correction is needed.
    table_offsets = self._ReadTableOffsets(parser_mediator, file_object)
    for table_offset in table_offsets:
      # Skipping X bytes, unknown data at this point.
      file_object.seek(table_offset, os.SEEK_SET)

      try:
        table = self.TABLE_HEADER.parse_stream(file_object)
      except (IOError, construct.FieldError):
        parser_mediator.ProduceExtractionError(
            u'unable to parse table structure at offset: 0x{0:08x}'.format(
                table_offset))
        continue

      # Table_offset: absolute byte in the file where the table starts.
      # table.first_record: first record in the table, relative to the
      #                     first byte of the table.
      file_object.seek(table_offset + table.first_record, os.SEEK_SET)

      if table.record_type == self.RECORD_TYPE_INTERNET:
        for _ in range(table.number_of_records):
          self._ReadEntryInternet(parser_mediator, file_object)

      elif table.record_type == self.RECORD_TYPE_APPLICATION:
        for _ in range(table.number_of_records):
          self._ReadEntryApplication(parser_mediator, file_object)


manager.ParsersManager.RegisterParser(KeychainParser)
