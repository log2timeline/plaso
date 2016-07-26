# -*- coding: utf-8 -*-
"""Parser for Windows Scheduled Task job files."""

import construct

from plaso.containers import time_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Brian Baskin (brian@thebaskins.com)'


class WinJobEvent(time_events.TimestampEvent):
  """Convenience class for a Windows Scheduled Task event.

  Attributes:
    application (str): path to job executable.
    description (str): description of the scheduled task.
    parameters (str): application command line parameters.
    trigger (int): event trigger, e.g. DAILY.
    username (str): username that scheduled the task.
    working_directory (str): working directory of the scheduled task.
  """

  DATA_TYPE = u'windows:tasks:job'

  def __init__(
      self, timestamp, timestamp_description, application, parameters,
      working_dir, username, trigger, description):
    """Initializes the event object.

    Args:
      timestamp (int): timestamp, which contains the number of microseconds
          since January 1, 1970, 00:00:00 UTC.
      timestamp_description (str): description of the usage of the timestamp
          value.
      application (str): path to job executable.
      parameters (str): application command line parameters.
      working_directory (str): working directory of the scheduled task.
      username (str): username that scheduled the task.
      trigger (int): event trigger, e.g. DAILY.
      description (str): description of the scheduled task.
    """
    super(WinJobEvent, self).__init__(timestamp, timestamp_description)
    self.application = application
    self.comment = description
    self.parameters = parameters
    self.trigger = trigger
    self.username = username
    self.working_directory = working_directory


class WinJobParser(interface.FileObjectParser):
  """Parse Windows Scheduled Task files for job events."""

  NAME = u'winjob'
  DESCRIPTION = u'Parser for Windows Scheduled Task job (or At-job) files.'

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

  _JOB_FIXED_STRUCT = construct.Struct(
      u'job_fixed',
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
      u'job_variable',
      construct.ULInt16(u'running_instance_count'),
      construct.ULInt16(u'application_length'),
      construct.String(
          u'application',
          lambda ctx: ctx.application_length * 2),
      construct.ULInt16(u'parameter_length'),
      construct.String(
          u'parameter',
          lambda ctx: ctx.parameter_length * 2),
      construct.ULInt16(u'working_dir_length'),
      construct.String(
          u'working_dir',
          lambda ctx: ctx.working_dir_length * 2),
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
      construct.ULInt16(u'test'),
      construct.ULInt16(u'trigger_size'),
      construct.ULInt16(u'trigger_reserved1'),
      construct.ULInt16(u'sched_start_year'),
      construct.ULInt16(u'sched_start_month'),
      construct.ULInt16(u'sched_start_day'),
      construct.ULInt16(u'sched_end_year'),
      construct.ULInt16(u'sched_end_month'),
      construct.ULInt16(u'sched_end_day'),
      construct.ULInt16(u'sched_start_hour'),
      construct.ULInt16(u'sched_start_minute'),
      construct.ULInt32(u'sched_duration'),
      construct.ULInt32(u'sched_interval'),
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

  def _IsEmptySystemTime(self, system_time_struct):
    """Determines if the system time is empty.

    Args:
      system_time_struct (construct.Struct): structure representing the system
          time.

    Return:
      bool: True if the system time is empty.
    """
    return (
        system_time_struct.year == 0 or system_time_struct.month == 0 and
        system_time_struct.weekday == 0 and system_time_struct.day == 0 and
        system_time_struct.hours == 0 and system_time_struct.minutes == 0 and
        system_time_struct.seconds == 0 and
        system_time_struct.milliseconds == 0)

  def _IsValidSystemTime(self, system_time_struct):
    """Determines if the system time is valid.

    Args:
      system_time_struct (construct.Struct): structure representing the system
          time.

    Return:
      bool: True if the system time is valid.
    """
    return (
        system_time_struct.year >= 1601 and
        system_time_struct.year <= 30827 and
        system_time_struct.month >= 1 and system_time_struct.month <= 12 and
        system_time_struct.weekday >= 0 and system_time_struct.weekday <= 6 and
        system_time_struct.day >= 1 and system_time_struct.day <= 31 and
        system_time_struct.hours >= 0 and system_time_struct.hours <= 23 and
        system_time_struct.minutes >= 0 and system_time_struct.minutes <= 59 and
        system_time_struct.seconds >= 0 and system_time_struct.seconds <= 59 and
        system_time_struct.milliseconds >= 0 and
        system_time_struct.milliseconds <= 999)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows job file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      header_struct = self._JOB_FIXED_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse Windows Task Job file with error: {0:s}'.format(
              exception))

    if not header_struct.product_version in self._PRODUCT_VERSIONS:
      raise errors.UnableToParseFile((
          u'Unsupported product version in: 0x{0:04x} Scheduled Task '
          u'file').format(header_struct.product_version))

    if not header_struct.format_version == 1:
      raise errors.UnableToParseFile(
          u'Unsupported format version in: {0:d} Scheduled Task file'.format(
              header_struct.format_version))

    try:
      job_variable_struct = self._JOB_VARIABLE_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse Windows Task Job file with error: {0:s}'.format(
              exception))

    if self._IsEmptySystemTime(header_struct.last_run_time):
      last_run_time = None
    else:
      try:
        last_run_time = self._CopySystemTimeToTimestamp(
            header_struct.last_run_time, parser_mediator.timezone)
      except errors.TimestampError as exception:
        last_run_time = None
        parser_mediator.ProduceExtractionError(
            u'unable to determine last run time with error: {0:s}'.format(
                exception))

    try:
      scheduled_date = timelib.Timestamp.FromTimeParts(
          job_variable_struct.sched_start_year,
          job_variable_struct.sched_start_month,
          job_variable_struct.sched_start_day,
          job_variable_struct.sched_start_hour,
          job_variable_struct.sched_start_minute,
          0,  # Seconds are not stored.
          timezone=parser_mediator.timezone)
    except errors.TimestampError as exception:
      scheduled_date = None
      parser_mediator.ProduceExtractionError(
          u'unable to determine scheduled date with error: {0:s}'.format(
              exception))

    application = binary.ReadUTF16(job_variable_struct.application)
    description = binary.ReadUTF16(job_variable_struct.comment)
    parameter = binary.ReadUTF16(job_variable_struct.parameter)
    username = binary.ReadUTF16(job_variable_struct.username)
    working_dir = binary.ReadUTF16(job_variable_struct.working_dir)

    if last_run_time is not None:
      event_object = WinJobEvent(
          last_run_time, eventdata.EventTimestamp.LAST_RUNTIME, application,
          parameter, working_dir, username, job_variable_struct.trigger_type,
          description)
      parser_mediator.ProduceEvent(event_object)

    if scheduled_date is not None:
      event_object = WinJobEvent(
          scheduled_date, u'Scheduled To Start', application, parameter,
          working_dir, username, job_variable_struct.trigger_type,
          description)
      parser_mediator.ProduceEvent(event_object)

    # TODO: create a timeless event object if last_run_time and scheduled_date
    # are None? What should be the description of this event?

    if job_variable_struct.sched_end_year:
      try:
        scheduled_end_date = timelib.Timestamp.FromTimeParts(
            job_variable_struct.sched_end_year,
            job_variable_struct.sched_end_month,
            job_variable_struct.sched_end_day,
            0,  # Hours are not stored.
            0,  # Minutes are not stored.
            0,  # Seconds are not stored.
            timezone=parser_mediator.timezone)
      except errors.TimestampError as exception:
        scheduled_end_date = None
        parser_mediator.ProduceExtractionError(
            u'unable to determine scheduled end date with error: {0:s}'.format(
                exception))

      if scheduled_end_date is not None:
        event_object = WinJobEvent(
            scheduled_end_date, u'Scheduled To End', application, parameter,
            working_dir, username, job_variable_struct.trigger_type,
            description)
        parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(WinJobParser)
