# -*- coding: utf-8 -*-
"""Parser for NTFS metadata files."""

import uuid

import construct
import pyfsntfs

from plaso import dependencies
from plaso.containers import file_system_events
from plaso.containers import windows_events
from plaso.lib import eventdata
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


dependencies.CheckModuleVersion(u'pyfsntfs')


class NTFSMFTParser(interface.FileObjectParser):
  """Parses a NTFS $MFT metadata file."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'mft'
  DESCRIPTION = u'Parser for NTFS $MFT metadata files.'

  _MFT_ATTRIBUTE_STANDARD_INFORMATION = 0x00000010
  _MFT_ATTRIBUTE_FILE_NAME = 0x00000030
  _MFT_ATTRIBUTE_OBJECT_ID = 0x00000040

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'BAAD', offset=0)
    format_specification.AddNewSignature(b'FILE', offset=0)
    return format_specification

  def _ParseMFTAttribute(self, parser_mediator, mft_entry, mft_attribute):
    """Extract data from a NFTS $MFT attribute.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      mft_entry: The MFT entry (instance of pyfsntfs.file_entry).
      mft_attribute: The MFT attribute (instance of pyfsntfs.attribute).
    """
    if mft_entry.is_empty() or mft_entry.base_record_file_reference != 0:
      return

    if mft_attribute.attribute_type in [
        self._MFT_ATTRIBUTE_STANDARD_INFORMATION,
        self._MFT_ATTRIBUTE_FILE_NAME]:

      file_attribute_flags = getattr(
          mft_attribute, u'file_attribute_flags', None)
      name = getattr(mft_attribute, u'name', None)
      parent_file_reference = getattr(
          mft_attribute, u'parent_file_reference', None)

      try:
        creation_time = mft_attribute.get_creation_time_as_integer()
      except OverflowError as exception:
        parser_mediator.ProduceParseError((
            u'unable to read the creation timestamp from MFT attribute: '
            u'0x{0:08x} with error: {1:s}').format(
                mft_attribute.attribute_type, exception))
        creation_time = None

      if creation_time is not None:
        event_object = file_system_events.NTFSFileStatEvent(
            creation_time, eventdata.EventTimestamp.CREATION_TIME,
            mft_entry.file_reference, mft_attribute.attribute_type,
            file_attribute_flags=file_attribute_flags,
            is_allocated=mft_entry.is_allocated(), name=name,
            parent_file_reference=parent_file_reference)
        parser_mediator.ProduceEvent(event_object)

      try:
        modification_time = mft_attribute.get_modification_time_as_integer()
      except OverflowError as exception:
        parser_mediator.ProduceParseError((
            u'unable to read the modification timestamp from MFT attribute: '
            u'0x{0:08x} with error: {1:s}').format(
                mft_attribute.attribute_type, exception))
        modification_time = None

      if modification_time is not None:
        event_object = file_system_events.NTFSFileStatEvent(
            modification_time, eventdata.EventTimestamp.MODIFICATION_TIME,
            mft_entry.file_reference, mft_attribute.attribute_type,
            file_attribute_flags=file_attribute_flags,
            is_allocated=mft_entry.is_allocated(), name=name,
            parent_file_reference=parent_file_reference)
        parser_mediator.ProduceEvent(event_object)

      try:
        access_time = mft_attribute.get_access_time_as_integer()
      except OverflowError as exception:
        parser_mediator.ProduceParseError((
            u'unable to read the access timestamp from MFT attribute: '
            u'0x{0:08x} with error: {1:s}').format(
                exception, mft_attribute.attribute_type))
        access_time = None

      if access_time is not None:
        event_object = file_system_events.NTFSFileStatEvent(
            access_time, eventdata.EventTimestamp.ACCESS_TIME,
            mft_entry.file_reference, mft_attribute.attribute_type,
            file_attribute_flags=file_attribute_flags,
            is_allocated=mft_entry.is_allocated(), name=name,
            parent_file_reference=parent_file_reference)
        parser_mediator.ProduceEvent(event_object)

      try:
        entry_modification_time = (
            mft_attribute.get_entry_modification_time_as_integer())
      except OverflowError as exception:
        parser_mediator.ProduceParseError((
            u'unable to read the entry modification timestamp from MFT '
            u'attribute: 0x{0:08x} with error: {1:s}').format(
                mft_attribute.attribute_type, exception))
        entry_modification_time = None

      if entry_modification_time is not None:
        event_object = file_system_events.NTFSFileStatEvent(
            entry_modification_time,
            eventdata.EventTimestamp.ENTRY_MODIFICATION_TIME,
            mft_entry.file_reference, mft_attribute.attribute_type,
            file_attribute_flags=file_attribute_flags,
            is_allocated=mft_entry.is_allocated(), name=name,
            parent_file_reference=parent_file_reference)
        parser_mediator.ProduceEvent(event_object)

    elif mft_attribute.attribute_type == self._MFT_ATTRIBUTE_OBJECT_ID:
      display_name = u'$MFT: {0:d}-{1:d}'.format(
          mft_entry.file_reference & 0xffffffffffff,
          mft_entry.file_reference >> 48)

      if mft_attribute.droid_file_identifier:
        try:
          uuid_object = uuid.UUID(mft_attribute.droid_file_identifier)
          if uuid_object.version == 1:
            event_object = (
                windows_events.WindowsDistributedLinkTrackingCreationEvent(
                    uuid_object, display_name))
            parser_mediator.ProduceEvent(event_object)

        except (TypeError, ValueError) as exception:
          parser_mediator.ProduceParseError((
              u'unable to read droid file identifier from attribute: 0x{0:08x} '
              u'with error: {1:s}').format(
                  mft_attribute.attribute_type, exception))

      if mft_attribute.birth_droid_file_identifier:
        try:
          uuid_object = uuid.UUID(mft_attribute.birth_droid_file_identifier)
          if uuid_object.version == 1:
            event_object = (
                windows_events.WindowsDistributedLinkTrackingCreationEvent(
                    uuid_object, display_name))
            parser_mediator.ProduceEvent(event_object)

        except (TypeError, ValueError) as exception:
          parser_mediator.ProduceParseError((
              u'unable to read birth droid file identifier from attribute: '
              u'0x{0:08x} with error: {1:s}').format(
                  mft_attribute.attribute_type, exception))

  def _ParseMFTEntry(self, parser_mediator, mft_entry):
    """Extract data from a NFTS $MFT entry.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      mft_entry: The MFT entry (instance of pyfsntfs.file_entry).
    """
    for attribute_index in range(0, mft_entry.number_of_attributes):
      try:
        mft_attribute = mft_entry.get_attribute(attribute_index)
        self._ParseMFTAttribute(parser_mediator, mft_entry, mft_attribute)

      except IOError as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse MFT attribute: {0:d} with error: {1:s}').format(
                attribute_index, exception))

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a NTFS $MFT metadata file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.
    """
    mft_metadata_file = pyfsntfs.mft_metadata_file()

    try:
      mft_metadata_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceParseError(
          u'unable to open file with error: {0:s}'.format(exception))

    for entry_index in range(0, mft_metadata_file.number_of_file_entries):
      try:
        mft_entry = mft_metadata_file.get_file_entry(entry_index)
        self._ParseMFTEntry(parser_mediator, mft_entry)

      except IOError as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse MFT entry: {0:d} with error: {1:s}').format(
                entry_index, exception))

    mft_metadata_file.close()


class NTFSUsnJrnlParser(interface.FileObjectParser):
  """Parses a NTFS USN change journal."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'usnjrnl'
  DESCRIPTION = u'Parser for NTFS USN change journal ($UsnJrnl).'

  _USN_RECORD_V2 = construct.Struct(
      u'usn_record_v2',
      construct.ULInt32(u'size'),
      construct.ULInt16(u'major_version'),
      construct.ULInt16(u'minor_version'),
      construct.ULInt64(u'file_reference'),
      construct.ULInt64(u'parent_file_reference'),
      construct.ULInt64(u'update_sequence_number'),
      construct.ULInt64(u'update_date_time'),
      construct.ULInt32(u'update_reason_flags'),
      construct.ULInt32(u'update_source_flags'),
      construct.ULInt32(u'security_descriptor_identifier'),
      construct.ULInt32(u'file_attribute_flags'),
      construct.ULInt16(u'name_size'),
      construct.ULInt16(u'name_offset'),
      construct.String(u'name', lambda ctx: ctx.size - 60))

  # TODO: add support for USN_RECORD_V3 when actually seen to be used.

  def _ParseUSNChangeJournal(self, parser_mediator, usn_change_journal):
    """Parses an USN change journal.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      usn_change_journal: An USN change journal object (instance of
                          pyfsntsfs.usn_change_journal).
    """
    if not usn_change_journal:
      return

    usn_record_data = usn_change_journal.read_usn_record()
    while usn_record_data:
      current_offset = usn_change_journal.get_offset()

      try:
        usn_record_struct = self._USN_RECORD_V2.parse(usn_record_data)
      except (IOError, construct.FieldError) as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse USN record at offset: 0x{0:08x} '
            u'with error: {1:s}').format(current_offset, exception))
        continue

      name_offset = usn_record_struct.name_offset - 60
      utf16_stream = usn_record_struct.name[
          name_offset:usn_record_struct.name_size]

      try:
        name_string = utf16_stream.decode(u'utf-16-le')
      except (UnicodeDecodeError, UnicodeEncodeError) as exception:
        name_string = utf16_stream.decode(u'utf-16-le', errors=u'replace')
        parser_mediator.ProduceParseError((
            u'unable to decode USN record name string with error: '
            u'{0:s}. Characters that cannot be decoded will be replaced '
            u'with "?" or "\\ufffd".').format(exception))

      event_object = file_system_events.NTFSUSNChangeEvent(
          usn_record_struct.update_date_time, current_offset,
          name_string, usn_record_struct.file_reference,
          usn_record_struct.update_sequence_number,
          usn_record_struct.update_source_flags,
          usn_record_struct.update_reason_flags,
          file_attribute_flags=usn_record_struct.file_attribute_flags,
          parent_file_reference=usn_record_struct.parent_file_reference)
      parser_mediator.ProduceEvent(event_object)

      usn_record_data = usn_change_journal.read_usn_record()

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a NTFS $UsnJrnl metadata file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.
    """
    volume = pyfsntfs.volume()
    try:
      volume.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceParseError(
          u'unable to open NTFS volume with error: {0:s}'.format(exception))

    try:
      usn_change_journal = volume.get_usn_change_journal()
      self._ParseUSNChangeJournal(parser_mediator, usn_change_journal)
    finally:
      volume.close()


manager.ParsersManager.RegisterParsers([NTFSMFTParser, NTFSUsnJrnlParser])
