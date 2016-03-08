# -*- coding: utf-8 -*-
"""Parser for the Sleuthkit (TSK) bodyfile or mactime format.

The format specifications can be read here:
  http://wiki.sleuthkit.org/index.php?title=Body_file
"""

import re

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import manager
from plaso.parsers import text_parser


class MactimeEvent(time_events.PosixTimeEvent):
  """Convenience class for a mactime event.

  Attributes:
    filename: string containing the name of the file.
    inode: integer containing the "inode" of the file. Note that
           inode is an overloaded term in the context of mactime and
           used for MFT entry index values as well.
    md5_hash: string containing the MD5 hash of the content data.
    mode_as_string: string containing the protection mode.
    offset: integer containing the line number of the corresponding
            mactime entry.
    size: integer containing the size of the content data.
    user_gid: integer containing the user group identifier (GID).
    user_sid: string containing the user security identifier (SID).
  """

  DATA_TYPE = u'fs:mactime:line'

  def __init__(
      self, posix_time, usage, row_offset, filename, inode_number, data_size,
      mode, user_uid, user_gid, md5_hash):
    """Initializes a mactime-based event object.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      usage: the description of the usage of the time value.
      row_offset: integer containing the line number of the corresponding
                  mactime entry.
      filename: string containing the name of the file.
      inode_number: integer containing the "inode" of the file. Note that
                    inode is an overloaded term in the context of mactime and
                    used for MFT entry index values as well.
      data_size: integer containing the size of the content data.
      mode: string containing the protection mode.
      user_uid: integer containing the user identifier (UID).
      user_gid: integer containing the user group identifier (GID).
      md5_hash: string containing the MD5 hash of the content data.
    """
    super(MactimeEvent, self).__init__(posix_time, usage)
    self.filename = filename
    self.inode = inode_number
    self.md5 = md5_hash
    self.mode_as_string = mode
    self.offset = row_offset
    self.size = data_size
    self.user_gid = user_gid

    if user_uid is None:
      self.user_sid = None
    else:
      # Note that the user_sid value is expected to be a string.
      self.user_sid = u'{0:d}'.format(user_uid)


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
      u'atime': eventdata.EventTimestamp.ACCESS_TIME,
      u'btime': eventdata.EventTimestamp.CREATION_TIME,
      u'ctime': eventdata.EventTimestamp.CHANGE_TIME,
      u'mtime': eventdata.EventTimestamp.MODIFICATION_TIME,
  }

  def _GetIntegerValue(self, row, value_name):
    """Retrieves an integer value from the row.

    Args:
      row: a dictionary containing all the fields as denoted in the
           COLUMNS class list.
      value_name: string containing the name of the value.

    Retruns:
      An integer containing the value or None.
    """
    value = row.get(value_name, None)
    try:
      return int(value, 10)
    except (TypeError, ValueError):
      return

  def VerifyRow(self, unused_parser_mediator, row):
    """Verify we are dealing with a mactime bodyfile.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      row: a dictionary containing all the fields as denoted in the
           COLUMNS class list.

    Returns:
      A boolean indicating the row could be verified.
    """
    # The md5 value is '0' if not set.
    if row[u'md5'] != b'0' and not self._MD5_RE.match(row[u'md5']):
      return False

    try:
      # Verify that the "size" field is an integer, thus cast it to int
      # and then back to string so it can be compared, if the value is
      # not a string representation of an integer, eg: '12a' then this
      # conversion will fail and we return a False value.
      if str(int(row.get(u'size', b'0'), 10)) != row.get(u'size', None):
        return False
    except ValueError:
      return False

    # TODO: Add additional verification.
    return True

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a row and extract event objects.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      row_offset: the offset of the row.
      row: a dictionary containing all the fields as denoted in the
           COLUMNS class list.
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

    for value_name, timestamp_description in iter(
        self._TIMESTAMP_DESC_MAP.items()):
      posix_time = self._GetIntegerValue(row, value_name)
      # mactime will return 0 if the timestamp is not set.
      if not posix_time:
        continue

      event_object = MactimeEvent(
          posix_time, timestamp_description, row_offset, filename,
          inode_number, data_size, mode, user_uid, user_gid, md5_hash)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(MactimeParser)
