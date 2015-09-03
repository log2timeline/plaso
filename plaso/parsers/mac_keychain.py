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
import construct
import logging
import os

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class KeychainInternetRecordEvent(event.EventObject):
  """Convenience class for an keychain internet record event."""

  DATA_TYPE = u'mac:keychain:internet'

  def __init__(
      self, timestamp, timestamp_description, entry_name, account_name,
      text_description, comments, where, protocol, type_protocol, ssgp_hash):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an interger containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: The usage string for the timestamp value.
      entry_name: Name of the entry.
      account_name: Name of the account.
      text_description: Short description about the entry.
      comments: String that contains the comments added by the user.
      where: The domain name or IP where the password is used.
      protocol: The internet protocol used (eg. https).
      type_protocol: The sub-protocol used (eg. form).
      ssgp_hash: String with hexadecimal values from the password / cert hash.
    """
    super(KeychainInternetRecordEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = timestamp_description
    self.entry_name = entry_name
    self.account_name = account_name
    self.text_description = text_description
    self.where = where
    self.protocol = protocol
    self.type_protocol = type_protocol
    self.comments = comments
    self.ssgp_hash = ssgp_hash


class KeychainApplicationRecordEvent(event.EventObject):
  """Convenience class for an keychain application password record event."""
  DATA_TYPE = u'mac:keychain:application'

  def __init__(
      self, timestamp, timestamp_description, entry_name,
      account_name, text_description, comments, ssgp_hash):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an interger containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: The usage string for the timestamp value.
      entry_name: Name of the entry.
      account_name: Name of the account.
      text_description: Short description about the entry.
      comments: String that contains the comments added by the user.
      ssgp_hash: String with hexadecimal values from the password / cert hash.
    """
    super(KeychainApplicationRecordEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = timestamp_description
    self.entry_name = entry_name
    self.account_name = account_name
    self.text_description = text_description
    self.comments = comments
    self.ssgp_hash = ssgp_hash


class KeychainParser(interface.SingleFileBaseParser):
  """Parser for Keychain files."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'mac_keychain'
  DESCRIPTION = u'Parser for Mac OS X Keychain files.'

  KEYCHAIN_MAGIC_HEADER = b'kych'
  KEYCHAIN_MAJOR_VERSION = 1
  KEYCHAIN_MINOR_VERSION = 0

  RECORD_TYPE_APPLICATION = 0x80000000
  RECORD_TYPE_INTERNET = 0x80000001

  # DB HEADER.
  KEYCHAIN_DB_HEADER = construct.Struct(
      u'db_header',
      construct.String(u'magic', 4),
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
      construct.UBInt32(u'last_mod_time'),
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

  def _GetTimestampFromEntry(self, parser_mediator, structure):
    """Parses a timestamp from a TIME entry structure.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      structure: TIME entry structure:
                 year: String with the number of the year.
                 month: String with the number of the month.
                 day: String with the number of the day.
                 hour: String with the number of the month.
                 minute: String with the number of the minute.
                 second: String with the number of the second.

    Returns:
      The timestamp which is an interger containing the number of micro seconds
      since January 1, 1970, 00:00:00 UTC.
    """
    try:
      return timelib.Timestamp.FromTimeParts(
          int(structure.year, 10), int(structure.month, 10),
          int(structure.day, 10), int(structure.hour, 10),
          int(structure.minute, 10), int(structure.second, 10))
    except ValueError:
      logging.warning(
          u'[{0:s}] Invalid keychain time {1!s} in file: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), structure))
      return 0

  def _ReadEntryApplication(self, parser_mediator, file_object):
    """Extracts the information from an application password entry.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object that points to an Keychain file.
    """
    offset = file_object.tell()
    try:
      record = self.RECORD_HEADER_APP.parse_stream(file_object)
    except (IOError, construct.FieldError):
      logging.warning((
          u'[{0:s}] Unsupported record header at 0x{1:08x} in file: '
          u'{2:s}').format(
              self.NAME, offset, parser_mediator.GetDisplayName()))
      return

    (ssgp_hash, creation_time, last_mod_time, text_description,
     comments, entry_name, account_name) = self._ReadEntryHeader(
         parser_mediator, file_object, record.record_header, offset)

    # Move to the end of the record, and then, prepared for the next record.
    file_object.seek(
        record.record_header.entry_length + offset - file_object.tell(),
        os.SEEK_CUR)
    event_object = KeychainApplicationRecordEvent(
        creation_time, eventdata.EventTimestamp.CREATION_TIME,
        entry_name, account_name, text_description, comments, ssgp_hash)
    parser_mediator.ProduceEvent(event_object)

    if creation_time != last_mod_time:
      event_object = KeychainApplicationRecordEvent(
          last_mod_time, eventdata.EventTimestamp.MODIFICATION_TIME,
          entry_name, account_name, text_description, comments, ssgp_hash)
      parser_mediator.ProduceEvent(event_object)

  def _ReadEntryHeader(
      self, parser_mediator, file_object, record, offset):
    """Read the common record attributes.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      file_object: A file-like object that points to an Keychain file.
      record: Structure with the header of the record.
      offset: First byte of the record.

    Returns:
      A tuple containing:
        ssgp_hash: Hash of the encrypted data (passwd, cert, note).
        creation_time: When the entry was created.
        last_mod_time: Last time the entry was updated.
        text_description: A brief description of the entry.
        entry_name: Name of the entry
        account_name: Name of the account.
    """
    # Info: The hash header always start with the string ssgp follow by
    #       the hash. Furthermore The fields are always a multiple of four.
    #       Then if it is not multiple the value is padded by 0x00.
    ssgp_hash = binascii.hexlify(file_object.read(record.ssgp_length)[4:])

    file_object.seek(
        record.creation_time - file_object.tell() + offset - 1, os.SEEK_CUR)
    creation_time = self._GetTimestampFromEntry(
        parser_mediator, self.TIME.parse_stream(file_object))

    file_object.seek(
        record.last_mod_time - file_object.tell() + offset - 1, os.SEEK_CUR)
    last_mod_time = self._GetTimestampFromEntry(
        parser_mediator, self.TIME.parse_stream(file_object))

    # The comment field does not always contain data.
    if record.text_description:
      file_object.seek(
          record.text_description - file_object.tell() + offset -1,
          os.SEEK_CUR)
      try:
        text_description = self.TEXT.parse_stream(file_object)
      except construct.FieldError:
        text_description = u'N/A (error)'
    else:
      text_description = u'N/A'

    # The comment field does not always contain data.
    if record.comments:
      file_object.seek(
          record.text_description - file_object.tell() + offset -1,
          os.SEEK_CUR)
      try:
        comments = self.TEXT.parse_stream(file_object)
      except construct.FieldError:
        comments = u'N/A (error)'
    else:
      comments = u'N/A'

    file_object.seek(
        record.entry_name - file_object.tell() + offset - 1, os.SEEK_CUR)
    try:
      entry_name = self.TEXT.parse_stream(file_object)
    except construct.FieldError:
      entry_name = u'N/A (error)'

    file_object.seek(
        record.account_name - file_object.tell() + offset - 1, os.SEEK_CUR)
    try:
      account_name = self.TEXT.parse_stream(file_object)
    except construct.FieldError:
      account_name = u'N/A (error)'

    return (
        ssgp_hash, creation_time, last_mod_time,
        text_description, comments, entry_name, account_name)

  def _ReadEntryInternet(self, parser_mediator, file_object):
    """Extracts the information from an Internet password entry.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object that points to an Keychain file.
    """
    offset = file_object.tell()
    try:
      record = self.RECORD_HEADER_INET.parse_stream(file_object)
    except (IOError, construct.FieldError):
      logging.warning((
          u'[{0:s}] Unsupported record header at 0x{1:08x} in file: '
          u'{2:s}').format(
              self.NAME, offset, parser_mediator.GetDisplayName()))
      return

    (ssgp_hash, creation_time, last_mod_time, text_description,
     comments, entry_name, account_name) = self._ReadEntryHeader(
         parser_mediator, file_object, record.record_header, offset)
    if not record.where:
      where = u'N/A'
      protocol = u'N/A'
      type_protocol = u'N/A'
    else:
      file_object.seek(
          record.where - file_object.tell() + offset - 1, os.SEEK_CUR)
      where = self.TEXT.parse_stream(file_object)
      file_object.seek(
          record.protocol - file_object.tell() + offset - 1, os.SEEK_CUR)
      protocol = self.TYPE_TEXT.parse_stream(file_object)
      file_object.seek(
          record.type - file_object.tell() + offset - 1, os.SEEK_CUR)
      type_protocol = self.TEXT.parse_stream(file_object)
      type_protocol = self._PROTOCOL_TRANSLATION_DICT.get(
          type_protocol, type_protocol)
      if record.url:
        file_object.seek(
            record.url - file_object.tell() + offset - 1, os.SEEK_CUR)
        url = self.TEXT.parse_stream(file_object)
        where = u'{0:s}{1:s}'.format(where, url)

    # Move to the end of the record, and then, prepared for the next record.
    file_object.seek(
        record.record_header.entry_length + offset - file_object.tell(),
        os.SEEK_CUR)

    event_object = KeychainInternetRecordEvent(
        creation_time, eventdata.EventTimestamp.CREATION_TIME,
        entry_name, account_name, text_description,
        comments, where, protocol, type_protocol, ssgp_hash)
    parser_mediator.ProduceEvent(event_object)

    if creation_time != last_mod_time:
      event_object = KeychainInternetRecordEvent(
          last_mod_time, eventdata.EventTimestamp.MODIFICATION_TIME,
          entry_name, account_name, text_description,
          comments, where, protocol, type_protocol, ssgp_hash)
      parser_mediator.ProduceEvent(event_object)

  def _VerifyStructure(self, file_object):
    """Verify that we are dealing with an Keychain entry.

    Args:
      file_object: A file-like object that points to an Keychain file.

    Returns:
      A list of table positions if it is a keychain, None otherwise.
    """
    # INFO: The HEADER KEYCHAIN:
    # [DBHEADER] + [DBSCHEMA] + [OFFSET TABLE A] + ... + [OFFSET TABLE Z]
    # Where the table offset is relative to the first byte of the DB Schema,
    # then we must add to this offset the size of the [DBHEADER].
    try:
      db_header = self.KEYCHAIN_DB_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return
    if (db_header.minor_version != self.KEYCHAIN_MINOR_VERSION or
        db_header.major_version != self.KEYCHAIN_MAJOR_VERSION or
        db_header.magic != self.KEYCHAIN_MAGIC_HEADER):
      return

    # Read the database schema and extract the offset for all the tables.
    # They are ordered by file position from the top to the bottom of the file.
    try:
      db_schema = self.KEYCHAIN_DB_SCHEMA.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return
    table_offsets = []
    for _ in range(db_schema.number_of_tables):
      try:
        table_offset = self.TABLE_OFFSET.parse_stream(file_object)
      except (IOError, construct.FieldError):
        return
      table_offsets.append(table_offset + self.KEYCHAIN_DB_HEADER.sizeof())
    return table_offsets

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Mac OS X keychain file-like object.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)

    table_offsets = self._VerifyStructure(file_object)
    if not table_offsets:
      raise errors.UnableToParseFile(u'The file is not a Keychain file.')

    for table_offset in table_offsets:
      # Skipping X bytes, unknown data at this point.
      file_object.seek(table_offset - file_object.tell(), os.SEEK_CUR)
      try:
        table = self.TABLE_HEADER.parse_stream(file_object)
      except construct.FieldError as exception:
        logging.warning((
            u'[{0:s}] Unable to parse table header in file: {1:s} '
            u'with error: {2:s}.').format(
                self.NAME, parser_mediator.GetDisplayName(),
                exception))
        continue

      # Table_offset: absolute byte in the file where the table starts.
      # table.first_record: first record in the table, relative to the
      #                     first byte of the table.
      file_object.seek(
          table_offset + table.first_record - file_object.tell(), os.SEEK_CUR)

      if table.record_type == self.RECORD_TYPE_INTERNET:
        for _ in range(table.number_of_records):
          self._ReadEntryInternet(parser_mediator, file_object)

      elif table.record_type == self.RECORD_TYPE_APPLICATION:
        for _ in range(table.number_of_records):
          self._ReadEntryApplication(parser_mediator, file_object)


manager.ParsersManager.RegisterParser(KeychainParser)
