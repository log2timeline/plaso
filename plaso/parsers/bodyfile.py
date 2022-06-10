# -*- coding: utf-8 -*-
"""Parser for the Sleuthkit (TSK) bodyfile format.

Sleuthkit version 3 format:
MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime
0|/lost+found|11|d/drwx------|0|0|12288|1337961350|1337961350|1337961350|0

More information about the format specifications can be read here:
  https://forensicswiki.xyz/wiki/index.php?title=Bodyfile
"""

import re

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class BodyfileEventData(events.EventData):
  """Bodyfile event data.

  Attributes:
    filename (str): name of the file.
    group_identifier (int): group identifier (GID), equivalent to st_gid.
    inode (int): "inode" of the file. Note that inode is an overloaded term
        in the context of a bodyfile and used for MFT entry index values as
        well.
    md5 (str): MD5 hash of the file content, formatted as a hexadecimal string.
    mode_as_string (str): protection mode.
    offset (int): number of the corresponding line, from which the event data
        was extracted.
    owner_identifier (str): user identifier (UID or SID) of the owner.
    size (int): size of the file content.
    symbolic_link_target (str): path of the symbolic link target.
  """

  DATA_TYPE = 'fs:bodyfile:entry'

  def __init__(self):
    """Initializes event data."""
    super(BodyfileEventData, self).__init__(data_type=self.DATA_TYPE)
    self.filename = None
    self.group_identifier = None
    self.inode = None
    self.md5 = None
    self.mode_as_string = None
    self.offset = None
    self.owner_identifier = None
    self.size = None
    self.symbolic_link_target = None


class BodyfileParser(interface.FileObjectParser):
  """SleuthKit bodyfile parser."""

  NAME = 'bodyfile'
  DATA_FORMAT = 'SleuthKit version 3 bodyfile'

  _INITIAL_FILE_OFFSET = 0

  _UINT32_MAX = (1 << 32) - 1
  _UINT48_MAX = (1 << 48) - 1

  _MD5_RE = re.compile(r'^[0-9a-fA-F]{32}$')

  _NON_PRINTABLE_CHARACTERS = list(range(0, 0x20)) + list(range(0x7f, 0xa0))
  _ESCAPE_CHARACTERS = str.maketrans({
      value: '\\x{0:02x}'.format(value)
      for value in _NON_PRINTABLE_CHARACTERS})

  def _GetDateTimeFromTimestamp(self, float_value):
    """Retrieves a date time object from the floating-point timestamp.

    Args:
      float_value (float): floating-point timestamp in number of seconds since
          January 1, 1970 00:00:00 UTC.

    Returns:
      dfdatetime.TimeElements: date and time based on the floating-point
          timestamp.
    """
    integer_value = int(float_value)
    if integer_value != float_value:
      integer_value = int(float_value * definitions.NANOSECONDS_PER_SECOND)
      date_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
          timestamp=integer_value)
    else:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=integer_value)

    return date_time

  def _GetLastValueAsBase10Integer(
      self, parser_mediator, values, description, line_number):
    """Retrieves the last value as a base 10 integer.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      values (list[str]): values extracted from the line.
      description (str): human readable description of the value.
      line_number (int): number of the line the values were extracted from.

    Returns:
      int: integer value or None if not available or invalid.

    Raises:
      WrongParser: when an invalid integer value is found on
          the first line.
    """
    integer_value = values.pop(-1) or None
    if integer_value is not None:
      try:
        integer_value = int(integer_value, 10)
      except ValueError:
        error_string = 'invalid {0:s} value in line: {1:d}'.format(
            description, line_number)
        if line_number == 0:
          raise errors.WrongParser(error_string)

        parser_mediator.ProduceRecoveryWarning(error_string)
        integer_value = None

    return integer_value

  def _GetLastValueAsFloatingPoint(
      self, parser_mediator, values, description, line_number):
    """Retrieves the last value as floating-point.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      values (list[str]): values extracted from the line.
      description (str): human readable description of the value.
      line_number (int): number of the line the values were extracted from.

    Returns:
      float: floating-point value or None if not available or invalid.

    Raises:
      WrongParser: when an invalid floating-point value is found on
          the first line.
    """
    float_value = values.pop(-1) or None
    if float_value is not None:
      try:
        float_value = float(float_value)
      except ValueError:
        error_string = 'invalid {0:s} value in line: {1:d}'.format(
            description, line_number)
        if line_number == 0:
          raise errors.WrongParser(error_string)

        parser_mediator.ProduceRecoveryWarning(error_string)
        float_value = None

    return float_value

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a bodyfile file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Note that we cannot use the DSVParser here since the bodyfile format is
    # not strict and clean file format.
    line_reader = text_file.TextFile(
        file_object, encoding='UTF-8', end_of_line='\n')

    line_number = 0

    try:
      line = line_reader.readline()
    except UnicodeDecodeError as exception:
      raise errors.WrongParser(
          'unable to read line: {0:d} with error: {1!s}'.format(
              line_number, exception))

    while line:
      values = line.split('|')
      number_of_values = len(values)
      if number_of_values < 11:
        error_string = 'invalid number of values: {0:d} in line: {1:d}'.format(
            number_of_values, line_number)
        if line_number == 0:
          raise errors.WrongParser(error_string)

        parser_mediator.ProduceExtractionWarning(error_string)

      else:
        md5_value = values.pop(0)
        if md5_value == '0':
          md5_value = None
        elif md5_value and not self._MD5_RE.match(md5_value):
          error_string = 'invalid MD5 value: {0:s} in line: {1:d}'.format(
              md5_value, line_number)
          if line_number == 0:
            raise errors.WrongParser(error_string)

          parser_mediator.ProduceRecoveryWarning(error_string)

        crtime_value = self._GetLastValueAsFloatingPoint(
            parser_mediator, values, 'creation time', line_number)
        ctime_value = self._GetLastValueAsFloatingPoint(
            parser_mediator, values, 'inode change time', line_number)
        mtime_value = self._GetLastValueAsFloatingPoint(
            parser_mediator, values, 'modification time', line_number)
        atime_value = self._GetLastValueAsFloatingPoint(
            parser_mediator, values, 'access time', line_number)

        size_value = self._GetLastValueAsBase10Integer(
            parser_mediator, values, 'size', line_number)
        gid_value = self._GetLastValueAsBase10Integer(
            parser_mediator, values, 'group identifier (GID)', line_number)
        uid_value = self._GetLastValueAsBase10Integer(
            parser_mediator, values, 'user identifier (UID)', line_number)

        if uid_value is not None:
          # Note that the owner_identifier attribute of BodyfileEventData
          # is expected to be a string or None.
          uid_value = '{0:d}'.format(uid_value)

        mode_as_string_value = values.pop(-1) or None

        inode_value = values.pop(-1) or None
        if '-' in inode_value:
          inode_value, _, _ = inode_value.partition('-')

        try:
          inode_value = int(inode_value, 10)
        except (TypeError, ValueError):
          inode_value = None
          parser_mediator.ProduceRecoveryWarning(
              'invalid inode value: {0!s} in line: {1:d}'.format(
                  inode_value, line_number))

        # Determine if the inode value is actually a 64-bit NTFS file reference.
        if inode_value > self._UINT48_MAX:
          mft_entry = inode_value & 0xffffffffffff
          if mft_entry <= self._UINT32_MAX:
            inode_value = mft_entry

        filename = '|'.join(values)
        escaped_filename = filename.translate(self._ESCAPE_CHARACTERS)
        if filename != escaped_filename:
          parser_mediator.ProduceRecoveryWarning((
              'filename in line: {0:d} contains unescaped control '
              'characters').format(line_number))

        else:
          for character in self._NON_PRINTABLE_CHARACTERS:
            escaped_character = '\\x{0:02x}'.format(character)
            filename = filename.replace(escaped_character, chr(character))

          filename = filename.replace('\\|', '|')
          filename = filename.replace('\\\\', '\\')

        symbolic_link_target = ''
        if (mode_as_string_value and mode_as_string_value[0] == 'l' and
            ' -> ' in filename):
          filename, _, symbolic_link_target = filename.rpartition(' -> ')

        event_data = BodyfileEventData()
        event_data.filename = filename
        event_data.group_identifier = gid_value
        event_data.inode = inode_value
        event_data.md5 = md5_value
        event_data.mode_as_string = mode_as_string_value
        event_data.offset = file_object.tell()
        event_data.owner_identifier = uid_value
        event_data.size = size_value
        event_data.symbolic_link_target = symbolic_link_target

        if atime_value:
          date_time = self._GetDateTimeFromTimestamp(atime_value)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        if ctime_value:
          date_time = self._GetDateTimeFromTimestamp(ctime_value)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_CHANGE)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        if crtime_value:
          date_time = self._GetDateTimeFromTimestamp(crtime_value)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_CREATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        if mtime_value:
          date_time = self._GetDateTimeFromTimestamp(mtime_value)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        elif not atime_value and not ctime_value and not crtime_value:
          date_time = dfdatetime_semantic_time.NotSet()
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      line_number += 1

      try:
        line = line_reader.readline()
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to read line: {0:d} with error: {1!s}'.format(
                line_number, exception))
        break


manager.ParsersManager.RegisterParser(BodyfileParser)
