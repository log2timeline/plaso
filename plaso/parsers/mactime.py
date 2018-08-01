# -*- coding: utf-8 -*-
"""Parser for the Sleuthkit (TSK) bodyfile or mactime format.

The format specifications can be read here:
  http://wiki.sleuthkit.org/index.php?title=Body_file
"""

from __future__ import unicode_literals

import re

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import dsv_parser
from plaso.parsers import manager


# TODO: refactor to pass user_sid as an int.
class MactimeEventData(events.EventData):
  """Mactime event data.

  Attributes:
    filename (str): name of the file.
    inode (int): "inode" of the file. Note that inode is an overloaded term
        in the context of mactime and used for MFT entry index values as well.
    md5 (str): MD5 hash of the file content, formatted as a hexadecimal string.
    mode_as_string (str): protection mode.
    offset (int): number of the corresponding line.
    size (int): size of the file content.
    user_gid (int): user group identifier (GID).
    user_sid (str): user security identifier (SID).
  """

  DATA_TYPE = 'fs:mactime:line'

  def __init__(self):
    """Initializes event data."""
    super(MactimeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.filename = None
    self.inode = None
    self.md5 = None
    self.mode_as_string = None
    self.offset = None
    self.size = None
    self.user_gid = None
    self.user_sid = None


class MactimeParser(dsv_parser.DSVParser):
  """SleuthKit bodyfile parser."""

  NAME = 'mactime'
  DESCRIPTION = 'Parser for SleuthKit version 3 bodyfiles.'

  COLUMNS = [
      'md5', 'name', 'inode', 'mode_as_string', 'uid', 'gid', 'size',
      'atime', 'mtime', 'ctime', 'btime']
  DELIMITER = b'|'

  _MD5_RE = re.compile(r'^[0-9a-fA-F]{32}$')

  # Mapping according to:
  # http://wiki.sleuthkit.org/index.php?title=Mactime_output
  _TIMESTAMP_DESC_MAP = {
      'atime': definitions.TIME_DESCRIPTION_LAST_ACCESS,
      'btime': definitions.TIME_DESCRIPTION_CREATION,
      'ctime': definitions.TIME_DESCRIPTION_CHANGE,
      'mtime': definitions.TIME_DESCRIPTION_MODIFICATION,
  }

  def _GetIntegerValue(self, row, value_name):
    """Converts a specific value of the row to an integer.

    Args:
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
      value_name (str): name of the value within the row.

    Returns:
      int: value or None if the value cannot be converted.
    """
    value = row.get(value_name, None)
    try:
      return int(value, 10)
    except (TypeError, ValueError):
      return None

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): number of the corresponding line.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    filename = row.get('name', None)
    md5_hash = row.get('md5', None)
    mode = row.get('mode_as_string', None)

    inode_number = row.get('inode', None)
    if '-' in inode_number:
      inode_number, _, _ = inode_number.partition('-')

    try:
      inode_number = int(inode_number, 10)
    except (TypeError, ValueError):
      inode_number = None

    data_size = self._GetIntegerValue(row, 'size')
    user_uid = self._GetIntegerValue(row, 'uid')
    user_gid = self._GetIntegerValue(row, 'gid')

    event_data = MactimeEventData()
    event_data.filename = filename
    event_data.inode = inode_number
    event_data.md5 = md5_hash
    event_data.mode_as_string = mode
    event_data.offset = row_offset
    event_data.size = data_size
    event_data.user_gid = user_gid

    if user_uid is None:
      event_data.user_sid = None
    else:
      # Note that the user_sid value is expected to be a string.
      event_data.user_sid = '{0:d}'.format(user_uid)

    for value_name, timestamp_description in iter(
        self._TIMESTAMP_DESC_MAP.items()):
      posix_time = self._GetIntegerValue(row, value_name)
      # mactime will return 0 if the timestamp is not set.
      if not posix_time:
        continue

      date_time = dfdatetime_posix_time.PosixTime(timestamp=posix_time)
      event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  # pylint: disable=unused-argument
  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    # Sleuthkit version 3 format:
    # MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
    # 0|/lost+found|11|d/drwx------|0|0|12288|1337961350|1337961350|1337961350|0

    if row['md5'] != '0' and not self._MD5_RE.match(row['md5']):
      return False

    # Check if the following columns contain a base 10 integer value if set.
    for column_name in (
        'uid', 'gid', 'size', 'atime', 'mtime', 'ctime', 'crtime'):
      column_value = row.get(column_name, None)
      if not column_value:
        continue

      try:
        int(column_value, 10)
      except (TypeError, ValueError):
        return False

    return True


manager.ParsersManager.RegisterParser(MactimeParser)
