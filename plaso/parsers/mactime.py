# -*- coding: utf-8 -*-
"""Parser for the Sleuthkit (TSK) bodyfile or mactime format.

The format specifications can be read here:
  http://wiki.sleuthkit.org/index.php?title=Body_file
"""

import re

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


# TODO: refactor to pass user_sid as an int.
class MactimeEventData(events.EventData):
  """Mactime event data.

  Attributes:
    filename (str): name of the file.
    inode (int): "inode" of the file. Note that inode is an overloaded term
        in the context of mactime and used for MFT entry index values as well.
    md5_hash (str): MD5 hash of the file content.
    mode_as_string (str): protection mode.
    offset (int): number of the corresponding line.
    size (int): size of the file content.
    user_gid (int): user group identifier (GID).
    user_sid (str): user security identifier (SID).
  """

  DATA_TYPE = u'fs:mactime:line'

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


class MactimeParser(text_parser.TextCSVParser):
  """Parses SleuthKit's mactime bodyfiles."""

  NAME = u'mactime'
  DESCRIPTION = u'Parser for SleuthKit\'s mactime bodyfiles.'

  COLUMNS = [
      u'md5', u'name', u'inode', u'mode_as_string', u'uid', u'gid', u'size',
      u'atime', u'mtime', u'ctime', u'btime']
  VALUE_SEPARATOR = b'|'

  _MD5_RE = re.compile(r'^[0-9a-fA-F]{32}$')

  # Mapping according to:
  # http://wiki.sleuthkit.org/index.php?title=Mactime_output
  _TIMESTAMP_DESC_MAP = {
      u'atime': definitions.TIME_DESCRIPTION_LAST_ACCESS,
      u'btime': definitions.TIME_DESCRIPTION_CREATION,
      u'ctime': definitions.TIME_DESCRIPTION_CHANGE,
      u'mtime': definitions.TIME_DESCRIPTION_MODIFICATION,
  }

  def _GetIntegerValue(self, row, value_name):
    """Converts a specific value of the row to an integer.

    Args:
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.
      value_name (str): name of the value within the row.

    Retruns:
      int: value or None if the value cannot be converted.
    """
    value = row.get(value_name, None)
    try:
      return int(value, 10)
    except (TypeError, ValueError):
      return

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a row and extract events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): number of the corresponding line.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.
    """
    filename = row.get(u'name', None)
    md5_hash = row.get(u'md5', None)
    mode = row.get(u'mode_as_string', None)

    inode_number = row.get(u'inode', None)
    if u'-' in inode_number:
      inode_number, _, _ = inode_number.partition(u'-')

    try:
      inode_number = int(inode_number, 10)
    except (TypeError, ValueError):
      inode_number = None

    data_size = self._GetIntegerValue(row, u'size')
    user_uid = self._GetIntegerValue(row, u'uid')
    user_gid = self._GetIntegerValue(row, u'gid')

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
      event_data.user_sid = u'{0:d}'.format(user_uid)

    for value_name, timestamp_description in iter(
        self._TIMESTAMP_DESC_MAP.items()):
      posix_time = self._GetIntegerValue(row, value_name)
      # mactime will return 0 if the timestamp is not set.
      if not posix_time:
        continue

      date_time = dfdatetime_posix_time.PosixTime(timestamp=posix_time)
      event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyRow(self, unused_parser_mediator, row):
    """Verify we are dealing with a mactime bodyfile.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as denoted in COLUMNS.

    Returns:
      bool: True if the row is valid.
    """
    # The md5 value is '0' if not set.
    if row[u'md5'] != b'0' and not self._MD5_RE.match(row[u'md5']):
      return False

    try:
      # Verify that the "size" field is an integer, thus cast it to int
      # and then back to string so it can be compared, if the value is
      # not a string representation of an integer, e.g. '12a' then this
      # conversion will fail and we return a False value.
      if str(int(row.get(u'size', b'0'), 10)) != row.get(u'size', None):
        return False
    except ValueError:
      return False

    # TODO: Add additional verification.
    return True


manager.ParsersManager.RegisterParser(MactimeParser)
