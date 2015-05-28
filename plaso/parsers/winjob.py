# -*- coding: utf-8 -*-
"""Parser for Windows Scheduled Task job files."""

import construct

from plaso.events import time_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Brian Baskin (brian@thebaskins.com)'


class WinJobEvent(time_events.TimestampEvent):
  """Convenience class for a Windows Scheduled Task event."""

  DATA_TYPE = u'windows:tasks:job'

  def __init__(
      self, timestamp, timestamp_description, application, parameter,
      working_dir, username, trigger, comment):
    """Initializes the event object.

    Args:
      timestamp: The timestamp value.
      timestamp_description: The usage string for the timestamp value.
      application: Path to job executable.
      parameter: Application command line parameters.
      working_dir: Working path for task.
      username: User job was scheduled from.
      trigger: Trigger event that runs the task, e.g. DAILY.
      comment: Optional description about the job.
    """
    super(WinJobEvent, self).__init__(timestamp, timestamp_description)
    self.application = binary.ReadUtf16(application)
    self.parameter = binary.ReadUtf16(parameter)
    self.working_dir = binary.ReadUtf16(working_dir)
    self.username = binary.ReadUtf16(username)
    self.trigger = trigger
    self.comment = binary.ReadUtf16(comment)


class WinJobParser(interface.SingleFileBaseParser):
  """Parse Windows Scheduled Task files for job events."""

  NAME = u'winjob'
  DESCRIPTION = u'Parser for Windows Scheduled Task job (or At-job) files.'

  PRODUCT_VERSIONS = {
      0x0400: u'Windows NT 4.0',
      0x0500: u'Windows 2000',
      0x0501: u'Windows XP',
      0x0600: u'Windows Vista',
      0x0601: u'Windows 7',
      0x0602: u'Windows 8',
      0x0603: u'Windows 8.1'
  }

  TRIGGER_TYPES = {
      0x0000: u'ONCE',
      0x0001: u'DAILY',
      0x0002: u'WEEKLY',
      0x0003: u'MONTHLYDATE',
      0x0004: u'MONTHLYDOW',
      0x0005: u'EVENT_ON_IDLE',
      0x0006: u'EVENT_AT_SYSTEMSTART',
      0x0007: u'EVENT_AT_LOGON'
  }

  JOB_FIXED_STRUCT = construct.Struct(
      u'job_fixed',
      construct.ULInt16(u'product_version'),
      construct.ULInt16(u'file_version'),
      construct.Bytes(u'job_uuid', 16),
      construct.ULInt16(u'app_name_len_offset'),
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
      construct.ULInt16(u'ran_year'),
      construct.ULInt16(u'ran_month'),
      construct.ULInt16(u'ran_weekday'),
      construct.ULInt16(u'ran_day'),
      construct.ULInt16(u'ran_hour'),
      construct.ULInt16(u'ran_minute'),
      construct.ULInt16(u'ran_second'),
      construct.ULInt16(u'ran_millisecond'),
      )

  # Using Construct's utf-16 encoding here will create strings with their
  # null terminators exposed. Instead, we'll read these variables raw and
  # convert them using Plaso's ReadUtf16() for proper formatting.
  JOB_VARIABLE_STRUCT = construct.Struct(
      u'job_variable',
      construct.ULInt16(u'running_instance_count'),
      construct.ULInt16(u'app_name_len'),
      construct.String(
          u'app_name',
          lambda ctx: ctx.app_name_len * 2),
      construct.ULInt16(u'parameter_len'),
      construct.String(
          u'parameter',
          lambda ctx: ctx.parameter_len * 2),
      construct.ULInt16(u'working_dir_len'),
      construct.String(
          u'working_dir',
          lambda ctx: ctx.working_dir_len * 2),
      construct.ULInt16(u'username_len'),
      construct.String(
          u'username',
          lambda ctx: ctx.username_len * 2),
      construct.ULInt16(u'comment_len'),
      construct.String(
          u'comment',
          lambda ctx: ctx.comment_len * 2),
      construct.ULInt16(u'userdata_len'),
      construct.String(
          u'userdata',
          lambda ctx: ctx.userdata_len),
      construct.ULInt16(u'reserved_len'),
      construct.String(
          u'reserved',
          lambda ctx: ctx.reserved_len),
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

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Windows job file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      header = self.JOB_FIXED_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse Windows Task Job file with error: {0:s}'.format(
              exception))

    if not header.product_version in self.PRODUCT_VERSIONS:
      raise errors.UnableToParseFile(u'Not a valid Scheduled Task file')

    if not header.file_version == 1:
      raise errors.UnableToParseFile(u'Not a valid Scheduled Task file')

    # Obtain the relevant values from the file.
    try:
      data = self.JOB_VARIABLE_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse Windows Task Job file with error: {0:s}'.format(
              exception))

    trigger_type = self.TRIGGER_TYPES.get(data.trigger_type, u'Unknown')

    last_run_date = timelib.Timestamp.FromTimeParts(
        header.ran_year,
        header.ran_month,
        header.ran_day,
        header.ran_hour,
        header.ran_minute,
        header.ran_second,
        microseconds=(header.ran_millisecond * 1000),
        timezone=parser_mediator.timezone)

    scheduled_date = timelib.Timestamp.FromTimeParts(
        data.sched_start_year,
        data.sched_start_month,
        data.sched_start_day,
        data.sched_start_hour,
        data.sched_start_minute,
        0,  # Seconds are not stored.
        timezone=parser_mediator.timezone)

    # Create two timeline events, one for created date and the other for last
    # run.
    parser_mediator.ProduceEvents(
        [WinJobEvent(
            last_run_date, eventdata.EventTimestamp.LAST_RUNTIME, data.app_name,
            data.parameter, data.working_dir, data.username, trigger_type,
            data.comment),
         WinJobEvent(
             scheduled_date, u'Scheduled To Start', data.app_name,
             data.parameter, data.working_dir, data.username, trigger_type,
             data.comment)])

    # A scheduled end date is optional.
    if data.sched_end_year:
      scheduled_end_date = timelib.Timestamp.FromTimeParts(
          data.sched_end_year,
          data.sched_end_month,
          data.sched_end_day,
          0,  # Hours are not stored.
          0,  # Minutes are not stored.
          0,  # Seconds are not stored.
          timezone=parser_mediator.timezone)

      event_object = WinJobEvent(
          scheduled_end_date, u'Scheduled To End', data.app_name,
          data.parameter, data.working_dir, data.username, trigger_type,
          data.comment)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(WinJobParser)
