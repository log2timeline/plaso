# -*- coding: utf-8 -*-
"""Parser for Windows Scheduled Task job files."""

import construct

from dfdatetime import systemtime as dfdatetime_systemtime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Brian Baskin (brian@thebaskins.com)'


class WinJobEventData(events.EventData):
  """Windows Scheduled Task event data.

  Attributes:
    application (str): path to job executable.
    description (str): description of the scheduled task.
    parameters (str): application command line parameters.
    trigger_type (int): trigger type.
    username (str): username that scheduled the task.
    working_directory (str): working directory of the scheduled task.
  """

  DATA_TYPE = u'windows:tasks:job'

  def __init__(self):
    """Initializes event data."""
    super(WinJobEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application = None
    self.comment = None
    self.parameters = None
    self.trigger_type = None
    self.username = None
    self.working_directory = None


class WinJobParser(interface.FileObjectParser):
  """Parse Windows Scheduled Task files for job events."""

  NAME = u'winjob'
  DESCRIPTION = u'Parser for Windows Scheduled Task job (or At-job) files.'

  _EMPTY_SYSTEM_TIME_TUPLE = (0, 0, 0, 0, 0, 0, 0, 0)

  _PRODUCT_VERSIONS = {
      0x0400: u'Windows NT 4.0',
      0x0500: u'Windows 2000',
      0x0501: u'Windows XP',
      0x0600: u'Windows Vista',
      0x0601: u'Windows 7',
      0x0602: u'Windows 8',
      0x0603: u'Windows 8.1',
      0x0a00: u'Windows 10',
  }

  _JOB_FIXED_LENGTH_SECTION_STRUCT = construct.Struct(
      u'job_fixed_length_section',
      construct.ULInt16(u'product_version'),
      construct.ULInt16(u'format_version'),
      construct.Bytes(u'job_uuid', 16),
      construct.ULInt16(u'application_length_offset'),
      construct.ULInt16(u'trigger_offset'),
      construct.ULInt16(u'error_retry_count'),
      construct.ULInt16(u'error_retry_interval'),
      construct.ULInt16(u'idle_deadline'),
      construct.ULInt16(u'idle_wait'),
      construct.ULInt32(u'priority'),
      construct.ULInt32(u'max_run_time'),
      construct.ULInt32(u'exit_code'),
      construct.ULInt32(u'status'),
      construct.ULInt32(u'flags'),
      construct.Struct(
          u'last_run_time',
          construct.ULInt16(u'year'),
          construct.ULInt16(u'month'),
          construct.ULInt16(u'weekday'),
          construct.ULInt16(u'day'),
          construct.ULInt16(u'hours'),
          construct.ULInt16(u'minutes'),
          construct.ULInt16(u'seconds'),
          construct.ULInt16(u'milliseconds')))

  # Using Construct's utf-16 encoding here will create strings with their
  # null terminators exposed. Instead, we'll read these variables raw and
  # convert them using Plaso's ReadUTF16() for proper formatting.
  _JOB_VARIABLE_STRUCT = construct.Struct(
      u'job_variable_length_section',
      construct.ULInt16(u'running_instance_count'),
      construct.ULInt16(u'application_length'),
      construct.String(
          u'application',
          lambda ctx: ctx.application_length * 2),
      construct.ULInt16(u'parameter_length'),
      construct.String(
          u'parameter',
          lambda ctx: ctx.parameter_length * 2),
      construct.ULInt16(u'working_directory_length'),
      construct.String(
          u'working_directory',
          lambda ctx: ctx.working_directory_length * 2),
      construct.ULInt16(u'username_length'),
      construct.String(
          u'username',
          lambda ctx: ctx.username_length * 2),
      construct.ULInt16(u'comment_length'),
      construct.String(
          u'comment',
          lambda ctx: ctx.comment_length * 2),
      construct.ULInt16(u'userdata_length'),
      construct.String(
          u'userdata',
          lambda ctx: ctx.userdata_length),
      construct.ULInt16(u'reserved_length'),
      construct.String(
          u'reserved',
          lambda ctx: ctx.reserved_length),
      construct.ULInt16(u'number_of_triggers'))

  _TRIGGER_STRUCT = construct.Struct(
      u'trigger',
      construct.ULInt16(u'size'),
      construct.ULInt16(u'reserved1'),
      construct.ULInt16(u'start_year'),
      construct.ULInt16(u'start_month'),
      construct.ULInt16(u'start_day'),
      construct.ULInt16(u'end_year'),
      construct.ULInt16(u'end_month'),
      construct.ULInt16(u'end_day'),
      construct.ULInt16(u'start_hour'),
      construct.ULInt16(u'start_minute'),
      construct.ULInt32(u'duration'),
      construct.ULInt32(u'interval'),
      construct.ULInt32(u'trigger_flags'),
      construct.ULInt32(u'trigger_type'),
      construct.ULInt16(u'trigger_arg0'),
      construct.ULInt16(u'trigger_arg1'),
      construct.ULInt16(u'trigger_arg2'),
      construct.ULInt16(u'trigger_padding'),
      construct.ULInt16(u'trigger_reserved2'),
      construct.ULInt16(u'trigger_reserved3'))

  def _CopySystemTimeToTimestamp(self, system_time_struct, timezone):
    """Copies a system time to a timestamp.

    Args:
      system_time_struct (construct.Struct): structure representing the system
          time.
      timezone (datetime.tzinfo): timezone.
    """
    return timelib.Timestamp.FromTimeParts(
        system_time_struct.year, system_time_struct.month,
        system_time_struct.day, system_time_struct.hours,
        system_time_struct.minutes, system_time_struct.seconds,
        microseconds=system_time_struct.milliseconds * 1000,
        timezone=timezone)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows job file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      header_struct = self._JOB_FIXED_LENGTH_SECTION_STRUCT.parse_stream(
          file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse fixed-length section with error: {0:s}'.format(
              exception))

    if not header_struct.product_version in self._PRODUCT_VERSIONS:
      raise errors.UnableToParseFile(
          u'Unsupported product version in: 0x{0:04x}'.format(
              header_struct.product_version))

    if not header_struct.format_version == 1:
      raise errors.UnableToParseFile(
          u'Unsupported format version in: {0:d}'.format(
              header_struct.format_version))

    try:
      job_variable_struct = self._JOB_VARIABLE_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse variable-length section with error: {0:s}'.format(
              exception))

    event_data = WinJobEventData()
    event_data.application = binary.ReadUTF16(job_variable_struct.application)
    event_data.comment = binary.ReadUTF16(job_variable_struct.comment)
    event_data.parameters = binary.ReadUTF16(job_variable_struct.parameter)
    event_data.username = binary.ReadUTF16(job_variable_struct.username)
    event_data.working_directory = binary.ReadUTF16(
        job_variable_struct.working_directory)

    systemtime_struct = header_struct.last_run_time
    system_time_tuple = (
        systemtime_struct.year, systemtime_struct.month,
        systemtime_struct.weekday, systemtime_struct.day,
        systemtime_struct.hours, systemtime_struct.minutes,
        systemtime_struct.seconds, systemtime_struct.milliseconds)

    date_time = None
    if system_time_tuple != self._EMPTY_SYSTEM_TIME_TUPLE:
      try:
        date_time = dfdatetime_systemtime.Systemtime(
            system_time_tuple=system_time_tuple)
      except ValueError as e:
        print("CP1", e)
        parser_mediator.ProduceExtractionError(
            u'invalid last run time: {0!s}'.format(system_time_tuple))

    if date_time:
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.LAST_RUNTIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for index in range(job_variable_struct.number_of_triggers):
      try:
        trigger_struct = self._TRIGGER_STRUCT.parse_stream(file_object)
      except (IOError, construct.FieldError) as exception:
        raise errors.UnableToParseFile(
            u'Unable to parse trigger: {0:d} with error: {1:s}'.format(
                index, exception))

      try:
        trigger_start_time = timelib.Timestamp.FromTimeParts(
            trigger_struct.start_year, trigger_struct.start_month,
            trigger_struct.start_day, trigger_struct.start_hour,
            trigger_struct.start_minute, 0, timezone=parser_mediator.timezone)
      except errors.TimestampError as exception:
        trigger_start_time = None
        parser_mediator.ProduceExtractionError(
            u'unable to determine scheduled date with error: {0:s}'.format(
                exception))

      event_data.trigger_type = trigger_struct.trigger_type

      if trigger_start_time is not None:
        event = time_events.TimestampEvent(
            trigger_start_time, u'Scheduled to start')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if trigger_struct.end_year:
        try:
          trigger_end_time = timelib.Timestamp.FromTimeParts(
              trigger_struct.end_year, trigger_struct.end_month,
              trigger_struct.end_day, 0, 0, 0,
              timezone=parser_mediator.timezone)
        except errors.TimestampError as exception:
          trigger_end_time = None
          parser_mediator.ProduceExtractionError((
              u'unable to determine scheduled end date with error: '
              u'{0:s}').format(exception))

        if trigger_end_time is not None:
          event = time_events.TimestampEvent(
              trigger_end_time, u'Scheduled to end')
          parser_mediator.ProduceEventWithEventData(event, event_data)

    # TODO: create a timeless event object if last_run_time and
    # trigger_start_time are None? What should be the description of
    # this event?


manager.ParsersManager.RegisterParser(WinJobParser)
