# -*- coding: utf-8 -*-
"""Parser for MacOS keychain database files."""

import codecs
import collections
import os

from dfdatetime import time_elements as dfdatetime_time_elements

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class KeychainInternetRecordEventData(events.EventData):
  """MacOS keychain internet record event data.

  Attributes:
    account_name (str): name of the account.
    comments (str): comments added by the user.
    creation_time (dfdatetime.DateTimeValues): creation date and time of
        the keychain record.
    entry_name (str): name of the entry.
    modification_time (dfdatetime.DateTimeValues): modification date and time
        of the keychain record.
    protocol (str): internet protocol used, for example "https".
    ssgp_hash (str): password/certificate hash formatted as a hexadecimal
        string.
    text_description (str): description.
    type_protocol (str): sub-protocol used, for example "form".
    where (str): domain name or IP where the password is used.
  """

  DATA_TYPE = 'macos:keychain:internet'

  def __init__(self):
    """Initializes event data."""
    super(KeychainInternetRecordEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.account_name = None
    self.comments = None
    self.creation_time = None
    self.entry_name = None
    self.modification_time = None
    self.protocol = None
    self.ssgp_hash = None
    self.text_description = None
    self.type_protocol = None
    self.where = None


# TODO: merge with KeychainInternetRecordEventData.
class KeychainApplicationRecordEventData(events.EventData):
  """MacOS keychain application password record event data.

  Attributes:
    account_name (str): name of the account.
    comments (str): comments added by the user.
    creation_time (dfdatetime.DateTimeValues): creation date and time of
        the keychain record.
    entry_name (str): name of the entry.
    modification_time (dfdatetime.DateTimeValues): modification date and time
        of the keychain record.
    ssgp_hash (str): password/certificate hash formatted as a hexadecimal
        string.
    text_description (str): description.
  """

  DATA_TYPE = 'macos:keychain:application'

  def __init__(self):
    """Initializes event data."""
    super(KeychainApplicationRecordEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.account_name = None
    self.comments = None
    self.creation_time = None
    self.entry_name = None
    self.modification_time = None
    self.ssgp_hash = None
    self.text_description = None


class KeychainDatabaseColumn(object):
  """MacOS keychain database column.

  Attributes:
    attribute_data_type (int): attribute (data) type.
    attribute_identifier (int): attribute identifier.
    attribute_name (str): attribute name.
  """

  def __init__(self):
    """Initializes a MacOS keychain database column."""
    super(KeychainDatabaseColumn, self).__init__()
    self.attribute_data_type = None
    self.attribute_identifier = None
    self.attribute_name = None


class KeychainDatabaseTable(object):
  """MacOS keychain database table.

  Attributes:
    columns (list[KeychainDatabaseColumn]): columns.
    records (list[dict[str, str]]): records.
    relation_identifier (int): relation identifier.
    relation_name (str): relation name.
  """

  def __init__(self):
    """Initializes a MacOS keychain database table."""
    super(KeychainDatabaseTable, self).__init__()
    self.columns = []
    self.records = []
    self.relation_identifier = None
    self.relation_name = None


class KeychainParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parser for MacOS keychain database files."""

  NAME = 'mac_keychain'
  DATA_FORMAT = 'MacOS keychain database file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'macos_keychain.yaml')

  _MAJOR_VERSION = 1
  _MINOR_VERSION = 0

  # TODO: add more protocols.
  _PROTOCOL_TRANSLATION_DICT = {
      'htps': 'https',
      'smtp': 'smtp',
      'imap': 'imap',
      'http': 'http'}

  _RECORD_TYPE_CSSM_DL_DB_SCHEMA_INFO = 0x00000000
  _RECORD_TYPE_CSSM_DL_DB_SCHEMA_INDEXES = 0x00000001
  _RECORD_TYPE_CSSM_DL_DB_SCHEMA_ATTRIBUTES = 0x00000002
  _RECORD_TYPE_APPLICATION_PASSWORD = 0x80000000
  _RECORD_TYPE_INTERNET_PASSWORD = 0x80000001

  _ATTRIBUTE_DATA_READ_FUNCTIONS = {
      0: '_ReadAttributeValueString',
      1: '_ReadAttributeValueInteger',
      2: '_ReadAttributeValueInteger',
      5: '_ReadAttributeValueDateTime',
      6: '_ReadAttributeValueBinaryData'}

  def _ReadAttributeValueBinaryData(
      self, attribute_values_data, record_offset, attribute_values_data_offset,
      attribute_value_offset):
    """Reads a binary data attribute value.

    Args:
      attribute_values_data (bytes): attribute values data.
      record_offset (int): offset of the record relative to the start of
          the file.
      attribute_values_data_offset (int): offset of the attribute values data
          relative to the start of the record.
      attribute_value_offset (int): offset of the attribute relative to
          the start of the record.

    Returns:
      bytes: binary data value or None if attribute value offset is not set.

    Raises:
      ParseError: if the attribute value cannot be read.
    """
    if attribute_value_offset == 0:
      return None

    data_type_map = self._GetDataTypeMap('keychain_blob')

    file_offset = (
        record_offset + attribute_values_data_offset + attribute_value_offset)

    attribute_value_offset -= attribute_values_data_offset + 1
    attribute_value_data = attribute_values_data[attribute_value_offset:]

    try:
      string_attribute_value = self._ReadStructureFromByteStream(
          attribute_value_data, file_offset, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map binary data attribute value data at offset: 0x{0:08x} '
          'with error: {1!s}').format(file_offset, exception))

    return string_attribute_value.blob

  def _ReadAttributeValueDateTime(
      self, attribute_values_data, record_offset, attribute_values_data_offset,
      attribute_value_offset):
    """Reads a date time attribute value.

    Args:
      attribute_values_data (bytes): attribute values data.
      record_offset (int): offset of the record relative to the start of
          the file.
      attribute_values_data_offset (int): offset of the attribute values data
          relative to the start of the record.
      attribute_value_offset (int): offset of the attribute relative to
          the start of the record.

    Returns:
      str: date and time values.

    Raises:
      ParseError: if the attribute value cannot be read.
    """
    if attribute_value_offset == 0:
      return None

    data_type_map = self._GetDataTypeMap('keychain_date_time')

    file_offset = (
        record_offset + attribute_values_data_offset + attribute_value_offset)

    attribute_value_offset -= attribute_values_data_offset + 1
    attribute_value_data = attribute_values_data[attribute_value_offset:]

    try:
      date_time_attribute_value = self._ReadStructureFromByteStream(
          attribute_value_data, file_offset, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map date time attribute value data at offset: 0x{0:08x} '
          'with error: {1!s}').format(file_offset, exception))

    return date_time_attribute_value.date_time.rstrip('\x00')

  def _ReadAttributeValueInteger(
      self, attribute_values_data, record_offset, attribute_values_data_offset,
      attribute_value_offset):
    """Reads an integer attribute value.

    Args:
      attribute_values_data (bytes): attribute values data.
      record_offset (int): offset of the record relative to the start of
          the file.
      attribute_values_data_offset (int): offset of the attribute values data
          relative to the start of the record.
      attribute_value_offset (int): offset of the attribute relative to
          the start of the record.

    Returns:
      int: integer value or None if attribute value offset is not set.

    Raises:
      ParseError: if the attribute value cannot be read.
    """
    if attribute_value_offset == 0:
      return None

    data_type_map = self._GetDataTypeMap('uint32be')

    file_offset = (
        record_offset + attribute_values_data_offset + attribute_value_offset)

    attribute_value_offset -= attribute_values_data_offset + 1
    attribute_value_data = attribute_values_data[attribute_value_offset:]

    try:
      return self._ReadStructureFromByteStream(
          attribute_value_data, file_offset, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map integer attribute value data at offset: 0x{0:08x} '
          'with error: {1!s}').format(file_offset, exception))

  def _ReadAttributeValueString(
      self, attribute_values_data, record_offset, attribute_values_data_offset,
      attribute_value_offset):
    """Reads a string attribute value.

    Args:
      attribute_values_data (bytes): attribute values data.
      record_offset (int): offset of the record relative to the start of
          the file.
      attribute_values_data_offset (int): offset of the attribute values data
          relative to the start of the record.
      attribute_value_offset (int): offset of the attribute relative to
          the start of the record.

    Returns:
      str: string value or None if attribute value offset is not set.

    Raises:
      ParseError: if the attribute value cannot be read.
    """
    if attribute_value_offset == 0:
      return None

    data_type_map = self._GetDataTypeMap('keychain_string')

    file_offset = (
        record_offset + attribute_values_data_offset + attribute_value_offset)

    attribute_value_offset -= attribute_values_data_offset + 1
    attribute_value_data = attribute_values_data[attribute_value_offset:]

    try:
      string_attribute_value = self._ReadStructureFromByteStream(
          attribute_value_data, file_offset, data_type_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map string attribute value data at offset: 0x{0:08x} '
          'with error: {1!s}').format(file_offset, exception))

    return string_attribute_value.string

  def _ReadFileHeader(self, file_object):
    """Reads the file header.

    Args:
      file_object (file): file-like object.

    Returns:
      keychain_file_header: file header.

    Raises:
      ParseError: if the file header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('keychain_file_header')

    file_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map)

    if (file_header.major_format_version != self._MAJOR_VERSION or
        file_header.minor_format_version != self._MINOR_VERSION):
      raise errors.ParseError('Unsupported format version: {0:s}.{1:s}'.format(
          file_header.major_format_version, file_header.minor_format_version))

    return file_header

  def _ReadRecord(self, tables, file_object, record_offset, record_type):
    """Reads the record.

    Args:
      tables (dict[int, KeychainDatabaseTable]): tables per identifier.
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.
      record_type (int): record type, which should correspond to a relation
          identifier of a table defined in the schema.

    Raises:
      ParseError: if the record cannot be read.
    """
    table = tables.get(record_type, None)
    if not table:
      raise errors.ParseError(
          'Missing table for relation identifier: 0x{0:08}'.format(record_type))

    record_header = self._ReadRecordHeader(file_object, record_offset)

    record = collections.OrderedDict()

    if table.columns:
      attribute_value_offsets = self._ReadRecordAttributeValueOffset(
          file_object, record_offset + 24, len(table.columns))

    file_offset = file_object.tell()
    record_data_offset = file_offset - record_offset
    record_data_size = record_header.data_size - (file_offset - record_offset)
    record_data = file_object.read(record_data_size)

    if record_header.key_data_size > 0:
      record['_key_'] = record_data[:record_header.key_data_size]

    if table.columns:
      for index, column in enumerate(table.columns):
        attribute_data_read_function = self._ATTRIBUTE_DATA_READ_FUNCTIONS.get(
            column.attribute_data_type, None)
        if attribute_data_read_function:
          attribute_data_read_function = getattr(
              self, attribute_data_read_function, None)

        if not attribute_data_read_function:
          attribute_value = None
        else:
          attribute_value = attribute_data_read_function(
              record_data, record_offset, record_data_offset,
              attribute_value_offsets[index])

        record[column.attribute_name] = attribute_value

    table.records.append(record)

  def _ReadRecordAttributeValueOffset(
      self, file_object, file_offset, number_of_attribute_values):
    """Reads the record attribute value offsets.

    Args:
      file_object (file): file-like object.
      file_offset (int): offset of the record attribute values offsets relative
          to the start of the file.
      number_of_attribute_values (int): number of attribute values.

    Returns:
      keychain_record_attribute_value_offsets: record attribute value offsets.

    Raises:
      ParseError: if the record attribute value offsets cannot be read.
    """
    offsets_data_size = number_of_attribute_values * 4

    offsets_data = file_object.read(offsets_data_size)

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'number_of_attribute_values': number_of_attribute_values})

    data_type_map = self._GetDataTypeMap(
        'keychain_record_attribute_value_offsets')

    try:
      attribute_value_offsets = self._ReadStructureFromByteStream(
          offsets_data, file_offset, data_type_map, context=context)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError((
          'Unable to map record attribute value offsets data at offset: '
          '0x{0:08x} with error: {1!s}').format(file_offset, exception))

    return attribute_value_offsets

  def _ReadRecordHeader(self, file_object, record_header_offset):
    """Reads the record header.

    Args:
      file_object (file): file-like object.
      record_header_offset (int): offset of the record header relative to
          the start of the file.

    Returns:
      keychain_record_header: record header.

    Raises:
      ParseError: if the record header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('keychain_record_header')

    record_header, _ = self._ReadStructureFromFileObject(
        file_object, record_header_offset, data_type_map)

    return record_header

  def _ReadRecordSchemaAttributes(self, tables, file_object, record_offset):
    """Reads a schema attributes (CSSM_DL_DB_SCHEMA_ATTRIBUTES) record.

    Args:
      tables (dict[int, KeychainDatabaseTable]): tables per identifier.
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Raises:
      ParseError: if the record cannot be read.
    """
    record_header = self._ReadRecordHeader(file_object, record_offset)

    attribute_value_offsets = self._ReadRecordAttributeValueOffset(
        file_object, record_offset + 24, 6)

    file_offset = file_object.tell()
    attribute_values_data_offset = file_offset - record_offset
    attribute_values_data_size = record_header.data_size - (
        file_offset - record_offset)
    attribute_values_data = file_object.read(attribute_values_data_size)

    relation_identifier = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[0])

    attribute_identifier = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[1])

    attribute_name_data_type = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[2])

    attribute_name = self._ReadAttributeValueString(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[3])

    # TODO: handle attribute_value_offsets[4]

    attribute_data_type = self._ReadAttributeValueInteger(
        attribute_values_data, record_offset, attribute_values_data_offset,
        attribute_value_offsets[5])

    table = tables.get(relation_identifier, None)
    if not table:
      raise errors.ParseError(
          'Missing table for relation identifier: 0x{0:08}'.format(
              relation_identifier))

    if attribute_name is None and attribute_value_offsets[1] != 0:
      attribute_value_offset = attribute_value_offsets[1]
      attribute_value_offset -= attribute_values_data_offset + 1
      attribute_name = attribute_values_data[
          attribute_value_offset:attribute_value_offset + 4]
      attribute_name = attribute_name.decode('ascii')

    column = KeychainDatabaseColumn()
    column.attribute_data_type = attribute_data_type
    column.attribute_identifier = attribute_identifier
    column.attribute_name = attribute_name

    table.columns.append(column)

    table = tables.get(self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_ATTRIBUTES, None)
    if not table:
      raise errors.ParseError('Missing CSSM_DL_DB_SCHEMA_ATTRIBUTES table.')

    record = collections.OrderedDict({
        'RelationID': relation_identifier,
        'AttributeID': attribute_identifier,
        'AttributeNameFormat': attribute_name_data_type,
        'AttributeName': attribute_name,
        'AttributeFormat': attribute_data_type})

    table.records.append(record)

  def _ReadRecordSchemaIndexes(self, tables, file_object, record_offset):
    """Reads a schema indexes (CSSM_DL_DB_SCHEMA_INDEXES) record.

    Args:
      tables (dict[int, KeychainDatabaseTable]): tables per identifier.
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Raises:
      ParseError: if the record cannot be read.
    """
    _ = self._ReadRecordHeader(file_object, record_offset)

    attribute_value_offsets = self._ReadRecordAttributeValueOffset(
        file_object, record_offset + 24, 5)

    if attribute_value_offsets != (0x2d, 0x31, 0x35, 0x39, 0x3d):
      raise errors.ParseError('Unsupported record attribute value offsets')

    file_offset = file_object.tell()
    data_type_map = self._GetDataTypeMap('keychain_record_schema_indexes')

    record_values, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    if record_values.relation_identifier not in tables:
      raise errors.ParseError(
          'CSSM_DL_DB_SCHEMA_INDEXES defines relation identifier not defined '
          'in CSSM_DL_DB_SCHEMA_INFO.')

    table = tables.get(self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_INDEXES, None)
    if not table:
      raise errors.ParseError('Missing CSSM_DL_DB_SCHEMA_INDEXES table.')

    record = collections.OrderedDict({
        'RelationID': record_values.relation_identifier,
        'IndexID': record_values.index_identifier,
        'AttributeID': record_values.attribute_identifier,
        'IndexType': record_values.index_type,
        'IndexedDataLocation': record_values.index_data_location})

    table.records.append(record)

  def _ReadRecordSchemaInformation(self, tables, file_object, record_offset):
    """Reads a schema information (CSSM_DL_DB_SCHEMA_INFO) record.

    Args:
      tables (dict[int, KeychainDatabaseTable]): tables per identifier.
      file_object (file): file-like object.
      record_offset (int): offset of the record relative to the start of
          the file.

    Raises:
      ParseError: if the record cannot be read.
    """
    _ = self._ReadRecordHeader(file_object, record_offset)

    attribute_value_offsets = self._ReadRecordAttributeValueOffset(
        file_object, record_offset + 24, 2)

    if attribute_value_offsets != (0x21, 0x25):
      raise errors.ParseError('Unsupported record attribute value offsets')

    file_offset = file_object.tell()
    data_type_map = self._GetDataTypeMap('keychain_record_schema_information')

    record_values, _ = self._ReadStructureFromFileObject(
        file_object, file_offset, data_type_map)

    relation_name = record_values.relation_name.decode('ascii')

    table = KeychainDatabaseTable()
    table.relation_identifier = record_values.relation_identifier
    table.relation_name = relation_name

    tables[table.relation_identifier] = table

    table = tables.get(self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_INFO, None)
    if not table:
      raise errors.ParseError('Missing CSSM_DL_DB_SCHEMA_INFO table.')

    record = collections.OrderedDict({
        'RelationID': record_values.relation_identifier,
        'RelationName': relation_name})

    table.records.append(record)

  def _ReadTable(self, tables, file_object, table_offset):
    """Reads the table.

    Args:
      tables (dict[int, KeychainDatabaseTable]): tables per identifier.
      file_object (file): file-like object.
      table_offset (int): offset of the table relative to the start of
          the file.

    Raises:
      ParseError: if the table cannot be read.
    """
    table_header = self._ReadTableHeader(file_object, table_offset)

    for record_offset in table_header.record_offsets:
      if record_offset == 0:
        continue

      record_offset += table_offset

      if table_header.record_type == self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_INFO:
        self._ReadRecordSchemaInformation(tables, file_object, record_offset)
      elif table_header.record_type == (
          self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_INDEXES):
        self._ReadRecordSchemaIndexes(tables, file_object, record_offset)
      elif table_header.record_type == (
          self._RECORD_TYPE_CSSM_DL_DB_SCHEMA_ATTRIBUTES):
        self._ReadRecordSchemaAttributes(tables, file_object, record_offset)
      else:
        self._ReadRecord(
            tables, file_object, record_offset, table_header.record_type)

  def _ReadTableHeader(self, file_object, table_header_offset):
    """Reads the table header.

    Args:
      file_object (file): file-like object.
      table_header_offset (int): offset of the tables header relative to
          the start of the file.

    Returns:
      keychain_table_header: table header.

    Raises:
      ParseError: if the table header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('keychain_table_header')

    table_header, _ = self._ReadStructureFromFileObject(
        file_object, table_header_offset, data_type_map)

    return table_header

  def _ReadTablesArray(self, file_object, tables_array_offset):
    """Reads the tables array.

    Args:
      file_object (file): file-like object.
      tables_array_offset (int): offset of the tables array relative to
          the start of the file.

    Returns:
      dict[int, KeychainDatabaseTable]: tables per identifier.

    Raises:
      ParseError: if the tables array cannot be read.
    """
    # TODO: implement https://github.com/libyal/dtfabric/issues/12 and update
    # keychain_tables_array definition.

    data_type_map = self._GetDataTypeMap('keychain_tables_array')

    tables_array, _ = self._ReadStructureFromFileObject(
        file_object, tables_array_offset, data_type_map)

    tables = collections.OrderedDict()
    for table_offset in tables_array.table_offsets:
      self._ReadTable(tables, file_object, tables_array_offset + table_offset)

    return tables

  def _ParseDateTimeValue(self, parser_mediator, date_time_value):
    """Parses a date time value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      date_time_value (str): date time value
          (CSSM_DB_ATTRIBUTE_FORMAT_TIME_DATE) in the format: "YYYYMMDDhhmmssZ".

    Returns:
      dfdatetime.TimeElements: date and time extracted from the value or None
          if the value does not represent a valid string.
    """
    if not date_time_value:
      return None

    if date_time_value[14] != 'Z':
      parser_mediator.ProduceExtractionWarning(
          'invalid date and time value: {0!s}'.format(date_time_value))
      return None

    try:
      year = int(date_time_value[0:4], 10)
      month = int(date_time_value[4:6], 10)
      day_of_month = int(date_time_value[6:8], 10)
      hours = int(date_time_value[8:10], 10)
      minutes = int(date_time_value[10:12], 10)
      seconds = int(date_time_value[12:14], 10)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'invalid date and time value: {0!s}'.format(date_time_value))
      return None

    time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    try:
      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date and time value: {0!s}'.format(date_time_value))
      return None

  def _ParseBinaryDataAsString(self, parser_mediator, binary_data_value):
    """Parses a binary data value as string.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      binary_data_value (bytes): binary data value
          (CSSM_DB_ATTRIBUTE_FORMAT_BLOB)

    Returns:
      str: binary data value formatted as a string or None if no string could
          be extracted or binary data value is None (NULL).
    """
    if not binary_data_value:
      return None

    try:
      return binary_data_value.decode('utf-8')
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'invalid binary data string value: {0:s}'.format(
              repr(binary_data_value)))
      return None

  def _ParseIntegerTagString(self, integer_value):
    """Parses an integer value as a tag string.

    Args:
      integer_value (int): integer value (CSSM_DB_ATTRIBUTE_FORMAT_SINT32,
          CSSM_DB_ATTRIBUTE_FORMAT_UINT32) that represents a tag string.

    Returns:
      str: integer value formatted as a tag string or None if integer value is
          None (NULL).
    """
    if not integer_value:
      return None

    tag_string = codecs.decode('{0:08x}'.format(integer_value), 'hex')
    return codecs.decode(tag_string, 'utf-8')

  def _ParseApplicationPasswordRecord(self, parser_mediator, record):
    """Extracts the information from an application password record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      record (dict[str, object]): database record.

    Raises:
      ParseError: if Internet password record cannot be parsed.
    """
    key = record.get('_key_', None)
    if not key or not key.startswith(b'ssgp'):
      raise errors.ParseError((
          'Unsupported application password record key value does not start '
          'with: "ssgp".'))

    ssgp_hash = codecs.encode(key[4:], 'hex')

    event_data = KeychainApplicationRecordEventData()
    event_data.account_name = self._ParseBinaryDataAsString(
        parser_mediator, record['acct'])
    event_data.comments = self._ParseIntegerTagString(record['crtr'])
    event_data.creation_time = self._ParseDateTimeValue(
        parser_mediator, record['cdat'])
    event_data.entry_name = self._ParseBinaryDataAsString(
        parser_mediator, record['PrintName'])
    event_data.modification_time = self._ParseDateTimeValue(
        parser_mediator, record['mdat'])
    event_data.ssgp_hash = codecs.decode(ssgp_hash, 'utf-8')
    event_data.text_description = self._ParseBinaryDataAsString(
        parser_mediator, record['desc'])

    parser_mediator.ProduceEventData(event_data)

  def _ParseInternetPasswordRecord(self, parser_mediator, record):
    """Extracts the information from an Internet password record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      record (dict[str, object]): database record.

    Raises:
      ParseError: if Internet password record cannot be parsed.
    """
    key = record.get('_key_', None)
    if not key or not key.startswith(b'ssgp'):
      raise errors.ParseError((
          'Unsupported Internet password record key value does not start '
          'with: "ssgp".'))

    protocol_string = codecs.decode('{0:08x}'.format(record['ptcl']), 'hex')
    protocol_string = codecs.decode(protocol_string, 'utf-8')

    event_data = KeychainInternetRecordEventData()
    event_data.account_name = self._ParseBinaryDataAsString(
        parser_mediator, record['acct'])
    event_data.comments = self._ParseIntegerTagString(record['crtr'])
    event_data.creation_time = self._ParseDateTimeValue(
        parser_mediator, record['cdat'])
    event_data.entry_name = self._ParseBinaryDataAsString(
        parser_mediator, record['PrintName'])
    event_data.modification_time = self._ParseDateTimeValue(
        parser_mediator, record['mdat'])
    event_data.protocol = self._PROTOCOL_TRANSLATION_DICT.get(
        protocol_string, protocol_string)
    ssgp_hash = codecs.encode(key[4:], 'hex')
    event_data.ssgp_hash = codecs.decode(ssgp_hash, 'utf-8')
    event_data.text_description = self._ParseBinaryDataAsString(
        parser_mediator, record['desc'])
    event_data.type_protocol = self._ParseBinaryDataAsString(
        parser_mediator, record['atyp'])
    event_data.where = self._ParseBinaryDataAsString(
        parser_mediator, record['srvr'])

    parser_mediator.ProduceEventData(event_data)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'kych', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a MacOS keychain file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    try:
      file_header = self._ReadFileHeader(file_object)
    except (ValueError, errors.ParseError):
      raise errors.WrongParser('Unable to parse file header.')

    tables = self._ReadTablesArray(file_object, file_header.tables_array_offset)

    table = tables.get(self._RECORD_TYPE_APPLICATION_PASSWORD, None)
    if table:
      for record in table.records:
        self._ParseApplicationPasswordRecord(parser_mediator, record)

    table = tables.get(self._RECORD_TYPE_INTERNET_PASSWORD, None)
    if table:
      for record in table.records:
        self._ParseInternetPasswordRecord(parser_mediator, record)


manager.ParsersManager.RegisterParser(KeychainParser)
