# -*- coding: utf-8 -*-
"""Parser for NTFS metadata files."""

from __future__ import unicode_literals

import uuid

import pyfsntfs  # pylint: disable=wrong-import-order

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import uuid_time as dfdatetime_uuid_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import dtfabric_parser
from plaso.parsers import interface
from plaso.parsers import manager


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class NTFSFileStatEventData(events.EventData):
  """NTFS file system stat event data.

  Attributes:
    attribute_type (int): attribute type e.g. 0x00000030 which represents
        $FILE_NAME.
    file_attribute_flags (int): NTFS file attribute flags.
    file_reference (int): NTFS file reference.
    file_system_type (str): file system type.
    is_allocated (bool): True if the MFT entry is allocated (marked as in use).
    name (str): name associated with the stat event, e.g. that of
        a $FILE_NAME attribute or None if not available.
    parent_file_reference (int): NTFS file reference of the parent.
    path_hint (str): A path to the NTFS file constructed from the
        `parent_file_reference`
  """

  DATA_TYPE = 'fs:stat:ntfs'

  def __init__(self):
    """Initializes event data."""
    super(NTFSFileStatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.attribute_type = None
    self.file_attribute_flags = None
    self.file_reference = None
    self.file_system_type = 'NTFS'
    self.is_allocated = None
    self.name = None
    self.parent_file_reference = None
    self.path_hint = None


class NTFSUSNChangeEventData(events.EventData):
  """NTFS USN change event data.

  Attributes:
    file_attribute_flags (int): NTFS file attribute flags.
    filename (str): name of the file associated with the event.
    file_reference (int): NTFS file reference.
    file_system_type (str): file system type.
    parent_file_reference (int): NTFS file reference of the parent.
    update_reason_flags (int): update reason flags.
    update_sequence_number (int): update sequence number.
    update_source_flags (int): update source flags.
  """

  DATA_TYPE = 'fs:ntfs:usn_change'

  def __init__(self):
    """Initializes event data."""
    super(NTFSUSNChangeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.file_attribute_flags = None
    self.filename = None
    self.file_reference = None
    self.parent_file_reference = None
    self.update_reason_flags = None
    self.update_sequence_number = None
    self.update_source_flags = None


class NTFSMFTParser(interface.FileObjectParser):
  """Parses a NTFS $MFT metadata file."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'mft'
  DESCRIPTION = 'Parser for NTFS $MFT metadata files.'

  _MFT_ATTRIBUTE_STANDARD_INFORMATION = 0x00000010
  _MFT_ATTRIBUTE_FILE_NAME = 0x00000030
  _MFT_ATTRIBUTE_OBJECT_ID = 0x00000040
  _PATH_SEPARATOR = '/'
  _PATH_NO_NAME_REPLACEMENT = '???'
  _PATH_NAME_ORPHAN = '$Orphan'

  def __init__(self):
    """Intializes the NTFS MFT Parser"""
    super(NTFSMFTParser, self).__init__()
    self.path_info = dict()

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'BAAD', offset=0)
    format_specification.AddNewSignature(b'FILE', offset=0)
    return format_specification

  def _GetDateTime(self, filetime):
    """Retrieves the date and time from a FILETIME timestamp.

    Args:
      filetime (int): FILETIME timestamp.

    Returns:
      dfdatetime.DateTimeValues: date and time.
    """
    if filetime == 0:
      return dfdatetime_semantic_time.SemanticTime('Not set')

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
      date_time = dfdatetime_uuid_time.UUIDTime(timestamp=uuid_object.time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseMFTAttribute(self, parser_mediator, mft_entry, mft_attribute):
    """Extract data from a NFTS $MFT attribute.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      mft_entry (pyfsntfs.file_entry): MFT entry.
      mft_attribute (pyfsntfs.attribute): MFT attribute.
    """
    if mft_entry.is_empty() or mft_entry.base_record_file_reference != 0:
      return

    if mft_attribute.attribute_type in [
        self._MFT_ATTRIBUTE_STANDARD_INFORMATION,
        self._MFT_ATTRIBUTE_FILE_NAME]:

      file_attribute_flags = getattr(
          mft_attribute, 'file_attribute_flags', None)
      name = getattr(mft_attribute, 'name', None)
      parent_file_reference = getattr(
          mft_attribute, 'parent_file_reference', None)

      event_data = NTFSFileStatEventData()
      event_data.attribute_type = mft_attribute.attribute_type
      event_data.file_attribute_flags = file_attribute_flags
      event_data.file_reference = mft_entry.file_reference
      event_data.is_allocated = mft_entry.is_allocated()
      event_data.name = name
      event_data.parent_file_reference = parent_file_reference

      if mft_attribute.attribute_type == self._MFT_ATTRIBUTE_FILE_NAME:
        parent_record_number = parent_file_reference & 0xffffffffffff
        parent_sequence_number = parent_file_reference >> 48
        event_data.path_hint = self._GetPathForFile(
            parser_mediator, name, parent_record_number, parent_sequence_number)
      else:
        # Even though $SI attributes do not carry a name, we are
        # opportunistic and use the most descriptive name available
        (name, parent_record_number,
         parent_sequence_number) = self._GetNameAndParentFromEntry(mft_entry)
        event_data.path_hint = self._GetPathForFile(
            parser_mediator, name, parent_record_number, parent_sequence_number)

      try:
        creation_time = mft_attribute.get_creation_time_as_integer()
      except OverflowError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read the creation timestamp from MFT attribute: '
            '0x{0:08x} with error: {1!s}').format(
                mft_attribute.attribute_type, exception))
        creation_time = None

      if creation_time is not None:
        date_time = self._GetDateTime(creation_time)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      try:
        modification_time = mft_attribute.get_modification_time_as_integer()
      except OverflowError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read the modification timestamp from MFT attribute: '
            '0x{0:08x} with error: {1!s}').format(
                mft_attribute.attribute_type, exception))
        modification_time = None

      if modification_time is not None:
        date_time = self._GetDateTime(modification_time)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      try:
        access_time = mft_attribute.get_access_time_as_integer()
      except OverflowError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read the access timestamp from MFT attribute: '
            '0x{0:08x} with error: {1!s}').format(
                exception, mft_attribute.attribute_type))
        access_time = None

      if access_time is not None:
        date_time = self._GetDateTime(access_time)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      try:
        entry_modification_time = (
            mft_attribute.get_entry_modification_time_as_integer())
      except OverflowError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read the entry modification timestamp from MFT '
            'attribute: 0x{0:08x} with error: {1!s}').format(
                mft_attribute.attribute_type, exception))
        entry_modification_time = None

      if entry_modification_time is not None:
        date_time = self._GetDateTime(entry_modification_time)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    elif mft_attribute.attribute_type == self._MFT_ATTRIBUTE_OBJECT_ID:
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
    for attribute_index in range(0, mft_entry.number_of_attributes):
      try:
        mft_attribute = mft_entry.get_attribute(attribute_index)
        self._ParseMFTAttribute(parser_mediator, mft_entry, mft_attribute)

      except IOError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MFT attribute: {0:d} with error: {1!s}').format(
                attribute_index, exception))

  def _GetFNAttributeInfos(self, mft_entry):
    """Returns a list of tuples containing information required to derive
    the most descriptive name for a record.

    Args:
      mft_entry (pyfsntfs.file_entry): MFT entry

    Returns:
      list[tuple]: List of tuples with (name, attribute_index,
          parent_record_number, parent_sequence_number)

    """
    attribute_info = []
    for attribute_index in range(0, mft_entry.number_of_attributes):
      mft_attribute = mft_entry.get_attribute(attribute_index)
      if mft_attribute.attribute_type == self._MFT_ATTRIBUTE_FILE_NAME:
        parent_file_reference = mft_attribute.parent_file_reference
        parent_record_number = parent_file_reference & 0xFFFFFFFFFFFF
        parent_sequence_number = parent_file_reference >> 48
        attribute_info.append((getattr(mft_attribute, 'name', ''),
                               attribute_index,
                               parent_record_number,
                               parent_sequence_number))
    return attribute_info

  def _GetNameAndParentFromAttributeInfos(self, attribute_infos):
    """Returns the most descriptive name, parent entry record number and
    sequence number from the return value of `GetFNAttributeInfos`.

    Each $MFT entry can have multiple $FILE_NAME attributes containing
    different names. One prominent example is when a file/folder name
    exceeds 8 characters, the $MFT will then contain two entries, one
    "normal" entry with the "full" name, and a DOS-compatible one
    (8.3). Each $FN attribute has a namespace value that denotes the
    name's type:

    0x0: POSIX (Case sensitive; all unicode except '/' and NULL)
    0x1: Win32 (Case insensitive; all unicode except '/', '\', ':',
         '>', '<', '?')
    0x2: DOS (Case insensitive; all upper case and no special characters.
         Must be 8 or fewer for name, 3 or less for the extension)
    0x3: Win32 & DOS (When the name is Win32 but does already fit in
         the DOS namespace)

    Rule of precedence for this function is: "0x3 > 0x1 > 0x0 > 0x2".
    On same value entries, the lower attribute index wins

    TODO: `namespace` (byte 65 of the $FILE_NAME attribute) is not
    available in `pyfsntfs.file_name_attribute`. For now we "guess"
    and go with the "longest string is best string, with lower
    attribute index preference"

    Args:
      attribute_infos (list[tuple]): A list of tuples produced by
          `_GetFNAttributeInfos`

    Returns:
      tuple: A tuple of (name, parent_record_number, parent_sequence_number)

    """

    name = None
    parent_record_number = None
    parent_sequence_number = None

    # Sort the attributes by re-mapping the `namespace` values
    # ns_map = {
    #   0x0: 0x2,
    #   0x1: 0x1,
    #   0x2: 0x3,
    #   0x3: 0x0
    # }
    # file_name_attributes.sort(key=lambda a: (ns_map[a[4]], a[1]))

    # Sort by name length and attribute index
    attribute_infos.sort(key=lambda a: (len(a[0]), a[1]), reverse=True)

    # Go through the sorted attribute infos, first one that fulfills
    # our criteria wins (criteria being name must not be empty)
    for (attribute_name, _, attribute_parent_num,
         attribute_parent_seq) in attribute_infos:
      if attribute_name:
        name = attribute_name
        parent_record_number = attribute_parent_num
        parent_sequence_number = attribute_parent_seq
        break

    # If we have not found suitable entry and there are entries, we take
    # the first one as last resort
    if attribute_infos and name is None:
      name, _, parent_record_number, parent_sequence_number = attribute_infos[0]

    return (name, parent_record_number, parent_sequence_number)

  def _GetNameAndParentFromEntry(self, mft_entry):
    """Returns the most descriptive name, its parent entry record number
    and sequence number from a given MFT record entry

    Args:
      mft_entry (pyfsntfs.file_entry): MFT entry

    Returns:
      tuple: A tuple of (name, parent_record_number parent_sequence_number)

    """

    attribute_infos = self._GetFNAttributeInfos(mft_entry)
    return self._GetNameAndParentFromAttributeInfos(attribute_infos)


  def _CollectMFTEntryPathInfo(self, mft_entry):
    """Extracts data from a given $MFT entry and stores it for lookup in
    order to be able to build a parent path of a file entry. This
    creates a map of the entries' record number to its sequence number,
    allocation status and a list of its names an parents.

    Args:
      mft_entry (pyfsntfs.file_entry): MFT entry.

    Raises:
      IOError: if MFT is not readable

    """

    if mft_entry.is_empty() or mft_entry.base_record_file_reference != 0:
      return

    entry_reference = mft_entry.file_reference
    entry_record_number = entry_reference & 0xFFFFFFFFFFFF
    entry_sequence_number = entry_reference >> 48
    entry_allocated = mft_entry.is_allocated()

    self.path_info[entry_record_number] = (
        entry_sequence_number,
        entry_allocated,
        self._GetFNAttributeInfos(mft_entry))

  def _GetPathForFile(self, parser_mediator, filename, parent_record_number,
                      parent_sequence_number):
    """Crafts a full path for a given filename, given its parent
    record and sequence number.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      filename (str): The filename
      parent_record_number (int): The parent record number to craft
          the path (from the files $FN)
      parent_sequence_number (int): The sequence number of the parent
          (from the files $FN)

    Returns:
      str: The full path of the entry

    """

    path_parents = self._ResolvePath(
        parser_mediator, parent_record_number, parent_sequence_number)
    if not path_parents:
      return filename
    path_parents.reverse()
    path_parents.append(filename)
    return self._PATH_SEPARATOR.join(path_parents)

  def _ResolvePath(self, parser_mediator, record_number, sequence_number,
                   path_parts=None, used_records=None):
    """Constructs a path for an entry by looking up the
    `record_number`, comparing the expected `sequence_number` (for
    orphaned files). Crafts the parents by appending to a list, which
    is why the return value is in reverse order!

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      record_number (int): The record number to start the path resolution
      sequence_number (int): The expected sequence number
      path_parts (list): A list that gets appended the path parts in
          recursive calls
      used_records (set): A set used to track which entries have been
          used in order to break cyclic paths

    Returns:
      list: List of parent path objects in reverse order

    """
    if path_parts is None:
      path_parts = []

    if used_records is None:
      used_records = set()

    if not record_number or \
       not sequence_number or \
       record_number not in self.path_info:
      return path_parts

    # Get the info from the map for the next parent
    (parent_sequence_number, parent_entry_allocated,
     parent_entry_attributes) = self.path_info.get(
         record_number, (None, None, ()))

    # If the entry does not have a legitimate parent, it's orphaned.
    # This is the case when the parent sequence number is higher than
    # the entry expects and the parent is allocated: The parent record
    # was reused.
    if (parent_sequence_number > sequence_number and parent_entry_allocated):
      path_parts.append(self._PATH_NAME_ORPHAN)
      return path_parts

    # Since we are a parent (a folder), there should only be one
    # reasonable $FN entry and all parent record numbers must be the
    # same. Warn if this is not the case
    if len(set(map(lambda i: i[2], parent_entry_attributes))) > 1:
      parser_mediator.ProduceExtractionWarning((
          '$MFT entry {0!s} is parent but carries multiple $FILE_NAME'
          'attributes with different parents!').format(record_number))
    (parent_name, parent_number,
     parent_sequence) = self._GetNameAndParentFromAttributeInfos(
         parent_entry_attributes)

    if parent_name:
      path_parts.append(parent_name)
    elif parent_number:
      # For some reason we have no name but a parent
      path_parts.append(self._PATH_NO_NAME_REPLACEMENT)

    if record_number != parent_number and parent_number not in used_records:
      used_records.add(parent_number)
      self._ResolvePath(parser_mediator, parent_number, parent_sequence,
                        path_parts, used_records)
    return path_parts

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
          'unable to open file with error: {0!s}'.format(exception))

    # Collect path information in a first round of parsing
    for entry_index in range(0, mft_metadata_file.number_of_file_entries):
      try:
        mft_entry = mft_metadata_file.get_file_entry(entry_index)
        self._CollectMFTEntryPathInfo(mft_entry)
      except IOError as exception:
        # We ignore the exception as it will be raised again in the
        # MFT entry processing below
        pass

    for entry_index in range(0, mft_metadata_file.number_of_file_entries):
      try:
        mft_entry = mft_metadata_file.get_file_entry(entry_index)
        self._ParseMFTEntry(parser_mediator, mft_entry)

      except IOError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MFT entry: {0:d} with error: {1!s}').format(
                entry_index, exception))

    mft_metadata_file.close()


class NTFSUsnJrnlParser(dtfabric_parser.DtFabricBaseParser):
  """Parses a NTFS USN change journal."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'usnjrnl'
  DESCRIPTION = 'Parser for NTFS USN change journal ($UsnJrnl).'

  _DEFINITION_FILE = 'ntfs.yaml'

  # TODO: add support for USN_RECORD_V3 and USN_RECORD_V4 when actually
  # seen to be used.

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
      event_data.update_reason_flags = usn_record.update_reason_flags
      event_data.update_sequence_number = usn_record.update_sequence_number
      event_data.update_source_flags = usn_record.update_source_flags

      if not usn_record.update_date_time:
        date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      else:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=usn_record.update_date_time)

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      usn_record_data = usn_change_journal.read_usn_record()

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a NTFS $UsnJrnl metadata file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    volume = pyfsntfs.volume()
    try:
      volume.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open NTFS volume with error: {0!s}'.format(exception))

    try:
      usn_change_journal = volume.get_usn_change_journal()
      self._ParseUSNChangeJournal(parser_mediator, usn_change_journal)
    finally:
      volume.close()


manager.ParsersManager.RegisterParsers([NTFSMFTParser, NTFSUsnJrnlParser])
