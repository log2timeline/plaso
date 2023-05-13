# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) timesync database file parser."""

import os

from plaso.lib import dtfabric_helper
from plaso.lib import errors


class TimesyncDatabaseFileParser(dtfabric_helper.DtFabricHelper):
  """Timesync database file parser.

  Attributes:
    records (List[timesync_boot_record]): timesync boot records.
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'timesync.yaml')

  _BOOT_RECORD_SIGNATURE = b'\xb0\xbb'
  _SYNC_RECORD_SIGNATURE = b'Ts'

  def __init__(self):
    """Initialises a timesync database file parser."""
    super(TimesyncDatabaseFileParser, self).__init__()
    self._boot_record_data_map = self._GetDataTypeMap('timesync_boot_record')
    self._sync_record_data_map = self._GetDataTypeMap('timesync_sync_record')
    self.records = []

  def ParseFileObject(self, file_object):
    """Parses a timesync database file-like object.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: when the file cannot be parsed.
    """
    file_offset = 0
    file_size = file_object.get_size()

    file_object.seek(file_offset, os.SEEK_SET)

    current_boot_record = None

    while file_offset < file_size:
      try:
        signature_data = file_object.read(2)

        if signature_data == self._BOOT_RECORD_SIGNATURE:
          boot_record, _ = self._ReadStructureFromFileObject(
              file_object, file_offset, self._boot_record_data_map)

          file_offset += boot_record.record_size

          current_boot_record = boot_record
          current_boot_record.sync_records = []

          self.records.append(current_boot_record)

        elif signature_data == self._SYNC_RECORD_SIGNATURE:
          sync_record, _ = self._ReadStructureFromFileObject(
              file_object, file_offset, self._sync_record_data_map)

          file_offset += sync_record.record_size

          if current_boot_record:
            current_boot_record.sync_records.append(sync_record)

        else:
          raise errors.ParseError(
              'Unsupported timesync record at offset: 0x{0:08x}'.format(
                  file_offset))

      except (IOError, errors.ParseError) as exception:
        raise errors.ParseError((
            'Unable to parse timesync record at offset: 0x{0:08x} with error: '
            '{1!s}').format(file_offset, exception))
