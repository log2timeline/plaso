# -*- coding: utf-8 -*-
"""Parser for the Sleuthkit (TSK) bodyfile or mactime format.

The format specifications can be read here:
  http://wiki.sleuthkit.org/index.php?title=Body_file
"""

import re

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import manager
from plaso.parsers import text_parser


class MactimeEvent(time_events.PosixTimeEvent):
  """Convenience class for a mactime-based event."""

  DATA_TYPE = 'fs:mactime:line'

  def __init__(self, posix_time, usage, row_offset, data):
    """Initializes a mactime-based event object.

    Args:
      posix_time: The POSIX time value.
      usage: The description of the usage of the time value.
      row_offset: The offset of the row.
      data: A dict object containing extracted data from the body file.
    """
    super(MactimeEvent, self).__init__(posix_time, usage)
    self.offset = row_offset
    self.user_sid = unicode(data.get('uid', u''))
    self.user_gid = data.get('gid', None)
    self.md5 = data.get('md5', None)
    self.filename = data.get('name', 'N/A')
    # Check if the filename field is not a string, eg in the instances where a
    # filename only conists of numbers. In that case the self.filename field
    # becomes an integer value instead of a string value. That causes issues
    # later in the process, where we expect the filename value to be a string.
    if not isinstance(self.filename, basestring):
      self.filename = unicode(self.filename)

    self.mode_as_string = data.get('mode_as_string', None)
    self.size = data.get('size', None)

    inode_number = data.get('inode', 0)
    if isinstance(inode_number, basestring):
      if '-' in inode_number:
        inode_number, _, _ = inode_number.partition('-')

      try:
        inode_number = int(inode_number, 10)
      except ValueError:
        inode_number = 0

    self.inode = inode_number


class MactimeParser(text_parser.TextCSVParser):
  """Parses SleuthKit's mactime bodyfiles."""

  NAME = 'mactime'
  DESCRIPTION = u'Parser for SleuthKit\'s mactime bodyfiles.'

  COLUMNS = [
      'md5', 'name', 'inode', 'mode_as_string', 'uid', 'gid', 'size',
      'atime', 'mtime', 'ctime', 'crtime']
  VALUE_SEPARATOR = '|'

  MD5_RE = re.compile('^[0-9a-fA-F]+$')

  _TIMESTAMP_DESC_MAP = {
      'atime': eventdata.EventTimestamp.ACCESS_TIME,
      'crtime': eventdata.EventTimestamp.CREATION_TIME,
      'ctime': eventdata.EventTimestamp.CHANGE_TIME,
      'mtime': eventdata.EventTimestamp.MODIFICATION_TIME,
  }

  def VerifyRow(self, unused_parser_mediator, row):
    """Verify we are dealing with a mactime bodyfile.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: A single row from the CSV file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    if not self.MD5_RE.match(row['md5']):
      return False

    try:
      # Verify that the "size" field is an integer, thus cast it to int
      # and then back to string so it can be compared, if the value is
      # not a string representation of an integer, eg: '12a' then this
      # conversion will fail and we return a False value.
      if str(int(row.get('size', '0'), 10)) != row.get('size', None):
        return False
    except ValueError:
      return False

    # TODO: Add additional verification.
    return True

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a row and extract event objects.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row_offset: The offset of the row.
      row: A dictionary containing all the fields as denoted in the
           COLUMNS class list.
    """
    for key, value in row.iteritems():
      if isinstance(row[key], basestring):
        try:
          row[key] = int(value, 10)
        except ValueError:
          pass

    for key, timestamp_description in self._TIMESTAMP_DESC_MAP.iteritems():
      value = row.get(key, None)
      if not value:
        continue
      event_object = MactimeEvent(
          value, timestamp_description, row_offset, row)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(MactimeParser)
