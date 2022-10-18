# -*- coding: utf-8 -*-
"""Parser for NTFS metadata files."""

import os
import uuid

from dfdatetime import filetime as dfdatetime_filetime

import pyfsntfs

from plaso.containers import events
from plaso.containers import windows_events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class NTFSFileStatEventData(events.EventData):
  """NTFS file system stat event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): file entry last access date
        and time.
    attribute_type (int): attribute type for example "0x00000030", which
        represents "$FILE_NAME".
    creation_time (dfdatetime.DateTimeValues): file entry creation date
        and time.
    display_name (str): display name.
    entry_modification_time (dfdatetime.DateTimeValues): file entry
         modification date and time.
    file_attribute_flags (int): NTFS file attribute flags.
    file_reference (int): NTFS file reference.
    file_system_type (str): file system type.
    filename (str): name of the file.
    is_allocated (bool): True if the MFT entry is allocated (marked as in use).
    modification_time (dfdatetime.DateTimeValues): file entry last modification
        date and time.
    name (str): name associated with the stat event, for example that of
        a $FILE_NAME attribute or None if not available.
    parent_file_reference (int): NTFS file reference of the parent.
    path_hints (list[str]): hints about the full path of the file.
    symbolic_link_target (str): path of the symbolic link target.
  """

  DATA_TYPE = 'fs:stat:ntfs'

  def __init__(self):
    """Initializes event data."""
    super(NTFSFileStatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.attribute_type = None
    self.creation_time = None
    self.display_name = None
    self.entry_modification_time = None
    self.file_attribute_flags = None
    self.file_reference = None
    self.file_system_type = 'NTFS'
    self.filename = None
    self.is_allocated = None
    self.modification_time = None
    self.name = None
    self.parent_file_reference = None
    self.path_hints = None
    self.symbolic_link_target = None


class NTFSUSNChangeEventData(events.EventData):
  """NTFS USN change event data.

  Attributes:
    file_attribute_flags (int): NTFS file attribute flags.
    filename (str): name of the file associated with the event.
    file_reference (int): NTFS file reference.
    file_system_type (str): file system type.
    parent_file_reference (int): NTFS file reference of the parent.
    offset (int): offset of the USN record relative to the start of the $J data
        stream, from which the event data was extracted.
    update_reason_flags (int): update reason flags.
    update_sequence_number (int): update sequence number.
    update_source_flags (int): update source flags.
    update_time (dfdatetime.DateTimeValues): update date and time.
  """

  DATA_TYPE = 'fs:ntfs:usn_change'

  def __init__(self):
    """Initializes event data."""
    super(NTFSUSNChangeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.file_attribute_flags = None
    self.filename = None
    self.file_reference = None
    self.parent_file_reference = None
    self.offset = None
    self.update_reason_flags = None
    self.update_sequence_number = None
    self.update_source_flags = None
    self.update_time = None


class NTFSMFTParser(interface.FileObjectParser):
  """Parses a NTFS $MFT metadata file."""

  NAME = 'mft'
  DATA_FORMAT = 'NTFS $MFT metadata file'

  _INITIAL_FILE_OFFSET = None

  _MFT_ATTRIBUTE_STANDARD_INFORMATION = 0x00000010
  _MFT_ATTRIBUTE_FILE_NAME = 0x00000030
  _MFT_ATTRIBUTE_OBJECT_ID = 0x00000040
  _MFT_ATTRIBUTE_DATA = 0x00000080

  _NAMESPACE_DOS = 2

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'FILE', offset=0)
    return format_specification

  def _GetDateTime(self, filetime):
    """Retrieves the date and time from a FILETIME timestamp.

    Args:
      filetime (int): FILETIME timestamp.

    Returns:
      dfdatetime.DateTimeValues: date and time or None if not set.
    """
    if not filetime:
      return None

    return dfdatetime_filetime.Filetime(timestamp=filetime)

  def _ParseDistributedTrackingIdentifier(
      self, parser_mediator, uuid_string, origin):
    """Extracts data from a Distributed Tracking identifier.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      uuid_string (str): UUID string of the Distributed Tracking identifier.
      origin (str): origin of the event (event source).
    """
    uuid_object = uuid.UUID(uuid_string)

    if uuid_object.version == 1:
      event_data = windows_events.WindowsDistributedLinkTrackingEventData(
          uuid_object, origin)
      parser_mediator.ProduceEventData(event_data)

  def _ParseFileStatAttribute(
      self, parser_mediator, mft_entry, mft_attribute, path_hints):
    """Extract data from a NFTS $STANDARD_INFORMATION or $FILE_NAME attribute.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      mft_entry (pyfsntfs.file_entry): MFT entry.
      mft_attribute (pyfsntfs.attribute): MFT attribute.
      path_hints (list[str]): hints about the full path of the file.
    """
    event_data = NTFSFileStatEventData()
    event_data.attribute_type = mft_attribute.attribute_type
    event_data.display_name = parser_mediator.GetDisplayName()
    event_data.file_reference = mft_entry.file_reference
    event_data.filename = parser_mediator.GetRelativePath()
    event_data.is_allocated = mft_entry.is_allocated()
    event_data.path_hints = path_hints or None
    event_data.symbolic_link_target = mft_entry.get_symbolic_link_target()

    if mft_attribute.attribute_type == self._MFT_ATTRIBUTE_FILE_NAME:
      event_data.file_attribute_flags = mft_attribute.file_attribute_flags
      event_data.name = mft_attribute.name
      event_data.parent_file_reference = mft_attribute.parent_file_reference

    try:
      filetime = mft_attribute.get_access_time_as_integer()
      event_data.access_time = self._GetDateTime(filetime)
    except OverflowError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read the access timestamp from MFT attribute: '
          '0x{0:08x} with error: {1!s}').format(
              exception, mft_attribute.attribute_type))

    try:
      filetime = mft_attribute.get_creation_time_as_integer()
      event_data.creation_time = self._GetDateTime(filetime)
    except OverflowError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read the creation timestamp from MFT attribute: '
          '0x{0:08x} with error: {1!s}').format(
              mft_attribute.attribute_type, exception))

    try:
      filetime = mft_attribute.get_entry_modification_time_as_integer()
      event_data.entry_modification_time = self._GetDateTime(filetime)
    except OverflowError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read the entry modification timestamp from MFT '
          'attribute: 0x{0:08x} with error: {1!s}').format(
              mft_attribute.attribute_type, exception))

    try:
      filetime = mft_attribute.get_modification_time_as_integer()
      event_data.modification_time = self._GetDateTime(filetime)
    except OverflowError as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to read the modification timestamp from MFT attribute: '
          '0x{0:08x} with error: {1!s}').format(
              mft_attribute.attribute_type, exception))

    parser_mediator.ProduceEventData(event_data)

  def _ParseObjectIDAttribute(
      self, parser_mediator, mft_entry, mft_attribute):
    """Extract data from a NFTS $OBJECT_ID attribute.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      mft_entry (pyfsntfs.file_entry): MFT entry.
      mft_attribute (pyfsntfs.attribute): MFT attribute.
    """
    display_name = '$MFT: {0:d}-{1:d}'.format(
        mft_entry.file_reference & 0xffffffffffff,
        mft_entry.file_reference >> 48)

    if mft_attribute.droid_file_identifier:
      try:
        self._ParseDistributedTrackingIdentifier(
            parser_mediator, mft_attribute.droid_file_identifier,
            display_name)

      except (TypeError, ValueError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read droid file identifier from attribute: 0x{0:08x} '
            'with error: {1!s}').format(
                mft_attribute.attribute_type, exception))

    if mft_attribute.birth_droid_file_identifier:
      try:
        self._ParseDistributedTrackingIdentifier(
            parser_mediator, mft_attribute.droid_file_identifier,
            display_name)

      except (TypeError, ValueError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read birth droid file identifier from attribute: '
            '0x{0:08x} with error: {1!s}').format(
                mft_attribute.attribute_type, exception))

  def _ParseMFTEntry(self, parser_mediator, mft_entry):
    """Extracts data from a NFTS $MFT entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      mft_entry (pyfsntfs.file_entry): MFT entry.
    """
    data_stream_names = []
    path_hints = []
    standard_information_attribute = None
    standard_information_attribute_index = None

    for attribute_index in range(0, mft_entry.number_of_attributes):
      try:
        mft_attribute = mft_entry.get_attribute(attribute_index)
        if mft_attribute.attribute_type == (
            self._MFT_ATTRIBUTE_STANDARD_INFORMATION):
          standard_information_attribute = mft_attribute
          standard_information_attribute_index = attribute_index

        elif mft_attribute.attribute_type == self._MFT_ATTRIBUTE_FILE_NAME:
          path_hint = mft_entry.get_path_hint(attribute_index)
          self._ParseFileStatAttribute(
              parser_mediator, mft_entry, mft_attribute, [path_hint])
          if mft_attribute.name_space != self._NAMESPACE_DOS:
            path_hints.append(path_hint)

        elif mft_attribute.attribute_type == self._MFT_ATTRIBUTE_OBJECT_ID:
          self._ParseObjectIDAttribute(
              parser_mediator, mft_entry, mft_attribute)

        elif mft_attribute.attribute_type == self._MFT_ATTRIBUTE_DATA:
          data_stream_names.append(mft_attribute.attribute_name)

      except IOError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MFT attribute: {0:d} with error: {1!s}').format(
                attribute_index, exception))

    if standard_information_attribute:
      path_hints_with_data_streams = []
      for path_hint in path_hints:
        if not path_hint:
          path_hint = '\\'

        if not data_stream_names:
          path_hints_with_data_streams.append(path_hint)
        else:
          for data_stream_name in data_stream_names:
            if not data_stream_name:
              path_hint_with_data_stream = path_hint
            else:
              path_hint_with_data_stream = '{0:s}:{1:s}'.format(
                  path_hint, data_stream_name)

            path_hints_with_data_streams.append(path_hint_with_data_stream)

      try:
        self._ParseFileStatAttribute(
            parser_mediator, mft_entry, standard_information_attribute,
            path_hints_with_data_streams)
      except IOError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MFT attribute: {0:d} with error: {1!s}').format(
                standard_information_attribute_index, exception))

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a NTFS $MFT metadata file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    mft_metadata_file = pyfsntfs.mft_metadata_file()

    try:
      mft_metadata_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open $MFT file with error: {0!s}'.format(exception))
      return

    for entry_index in range(0, mft_metadata_file.number_of_file_entries):
      try:
        mft_entry = mft_metadata_file.get_file_entry(entry_index)
        if (not mft_entry.is_empty() and
            mft_entry.base_record_file_reference == 0):
          self._ParseMFTEntry(parser_mediator, mft_entry)

      except IOError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MFT entry: {0:d} with error: {1!s}').format(
                entry_index, exception))

    mft_metadata_file.close()


class NTFSUsnJrnlParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parses a NTFS USN change journal."""

  NAME = 'usnjrnl'
  DATA_FORMAT = (
      'NTFS USN change journal ($UsnJrnl:$J) file system metadata file')

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'ntfs.yaml')

  _INITIAL_FILE_OFFSET = None

  # TODO: add support for USN_RECORD_V3 and USN_RECORD_V4 when actually
  # seen to be used.

  def _GetDateTime(self, filetime):
    """Retrieves the date and time from a FILETIME timestamp.

    Args:
      filetime (int): FILETIME timestamp.

    Returns:
      dfdatetime.DateTimeValues: date and time or None if not set.
    """
    if not filetime:
      return None

    return dfdatetime_filetime.Filetime(timestamp=filetime)

  def _ParseUSNChangeJournal(self, parser_mediator, usn_change_journal):
    """Parses an USN change journal.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      usn_change_journal (pyfsntsfs.usn_change_journal): USN change journal.

    Raises:
      ParseError: if an USN change journal record cannot be parsed.
    """
    if not usn_change_journal:
      return

    usn_record_map = self._GetDataTypeMap('usn_record_v2')

    usn_record_data = usn_change_journal.read_usn_record()
    while usn_record_data:
      current_offset = usn_change_journal.get_offset()

      try:
        usn_record = self._ReadStructureFromByteStream(
            usn_record_data, current_offset, usn_record_map)
      except (ValueError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to parse USN record at offset: 0x{0:08x} with error: '
            '{1!s}').format(current_offset, exception))

      # Per MSDN we need to use name offset for forward compatibility.
      name_offset = usn_record.name_offset - 60
      utf16_stream = usn_record.name[name_offset:usn_record.name_size]

      try:
        name_string = utf16_stream.decode('utf-16-le')
      except (UnicodeDecodeError, UnicodeEncodeError) as exception:
        name_string = utf16_stream.decode('utf-16-le', errors='replace')
        parser_mediator.ProduceExtractionWarning((
            'unable to decode USN record name string with error: '
            '{0:s}. Characters that cannot be decoded will be replaced '
            'with "?" or "\\ufffd".').format(exception))

      event_data = NTFSUSNChangeEventData()
      event_data.file_attribute_flags = usn_record.file_attribute_flags
      event_data.file_reference = usn_record.file_reference
      event_data.filename = name_string
      event_data.offset = current_offset
      event_data.parent_file_reference = usn_record.parent_file_reference
      event_data.update_time = self._GetDateTime(usn_record.update_date_time)
      event_data.update_reason_flags = usn_record.update_reason_flags
      event_data.update_sequence_number = usn_record.update_sequence_number
      event_data.update_source_flags = usn_record.update_source_flags

      parser_mediator.ProduceEventData(event_data)

      usn_record_data = usn_change_journal.read_usn_record()

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a NTFS $UsnJrnl metadata file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    fsntfs_volume = pyfsntfs.volume()
    try:
      fsntfs_volume.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open NTFS volume with error: {0!s}'.format(exception))
      return

    try:
      usn_change_journal = fsntfs_volume.get_usn_change_journal()
      self._ParseUSNChangeJournal(parser_mediator, usn_change_journal)
    finally:
      fsntfs_volume.close()


manager.ParsersManager.RegisterParsers([NTFSMFTParser, NTFSUsnJrnlParser])
