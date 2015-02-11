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

  DATA_TYPE = 'windows:tasks:job'

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


class WinJobParser(interface.BaseParser):
  """Parse Windows Scheduled Task files for job events."""

  NAME = 'winjob'
  DESCRIPTION = u'Parser for Windows Scheduled Task job (or At-job) files.'

  PRODUCT_VERSIONS = {
      0x0400:'Windows NT 4.0',
      0x0500:'Windows 2000',
      0x0501:'Windows XP',
      0x0600:'Windows Vista',
      0x0601:'Windows 7',
      0x0602:'Windows 8',
      0x0603:'Windows 8.1'
  }

  TRIGGER_TYPES = {
      0x0000:'ONCE',
      0x0001:'DAILY',
      0x0002:'WEEKLY',
      0x0003:'MONTHLYDATE',
      0x0004:'MONTHLYDOW',
      0x0005:'EVENT_ON_IDLE',
      0x0006:'EVENT_AT_SYSTEMSTART',
      0x0007:'EVENT_AT_LOGON'
  }

  JOB_FIXED_STRUCT = construct.Struct(
      'job_fixed',
      construct.ULInt16('product_version'),
      construct.ULInt16('file_version'),
      construct.Bytes('job_uuid', 16),
      construct.ULInt16('app_name_len_offset'),
      construct.ULInt16('trigger_offset'),
      construct.ULInt16('error_retry_count'),
      construct.ULInt16('error_retry_interval'),
      construct.ULInt16('idle_deadline'),
      construct.ULInt16('idle_wait'),
      construct.ULInt32('priority'),
      construct.ULInt32('max_run_time'),
      construct.ULInt32('exit_code'),
      construct.ULInt32('status'),
      construct.ULInt32('flags'),
      construct.ULInt16('ran_year'),
      construct.ULInt16('ran_month'),
      construct.ULInt16('ran_weekday'),
      construct.ULInt16('ran_day'),
      construct.ULInt16('ran_hour'),
      construct.ULInt16('ran_minute'),
      construct.ULInt16('ran_second'),
      construct.ULInt16('ran_millisecond'),
      )

  # Using Construct's utf-16 encoding here will create strings with their
  # null terminators exposed. Instead, we'll read these variables raw and
  # convert them using Plaso's ReadUtf16() for proper formatting.
  JOB_VARIABLE_STRUCT = construct.Struct(
      'job_variable',
      construct.ULInt16('running_instance_count'),
      construct.ULInt16('app_name_len'),
      construct.String(
          'app_name',
          lambda ctx: ctx.app_name_len * 2),
      construct.ULInt16('parameter_len'),
      construct.String(
          'parameter',
          lambda ctx: ctx.parameter_len * 2),
      construct.ULInt16('working_dir_len'),
      construct.String(
          'working_dir',
          lambda ctx: ctx.working_dir_len * 2),
      construct.ULInt16('username_len'),
      construct.String(
          'username',
          lambda ctx: ctx.username_len * 2),
      construct.ULInt16('comment_len'),
      construct.String(
          'comment',
          lambda ctx: ctx.comment_len * 2),
      construct.ULInt16('userdata_len'),
      construct.String(
          'userdata',
          lambda ctx: ctx.userdata_len),
      construct.ULInt16('reserved_len'),
      construct.String(
          'reserved',
          lambda ctx: ctx.reserved_len),
      construct.ULInt16('test'),
      construct.ULInt16('trigger_size'),
      construct.ULInt16('trigger_reserved1'),
      construct.ULInt16('sched_start_year'),
      construct.ULInt16('sched_start_month'),
      construct.ULInt16('sched_start_day'),
      construct.ULInt16('sched_end_year'),
      construct.ULInt16('sched_end_month'),
      construct.ULInt16('sched_end_day'),
      construct.ULInt16('sched_start_hour'),
      construct.ULInt16('sched_start_minute'),
      construct.ULInt32('sched_duration'),
      construct.ULInt32('sched_interval'),
      construct.ULInt32('trigger_flags'),
      construct.ULInt32('trigger_type'),
      construct.ULInt16('trigger_arg0'),
      construct.ULInt16('trigger_arg1'),
      construct.ULInt16('trigger_arg2'),
      construct.ULInt16('trigger_padding'),
      construct.ULInt16('trigger_reserved2'),
      construct.ULInt16('trigger_reserved3'))

  def Parse(self, parser_mediator, **kwargs):
    """Extract data from a Windows job file.

    This is the main parsing engine for the parser. It determines if
    the selected file is a proper Scheduled task job file and extracts
    the scheduled task data.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object = parser_mediator.GetFileObject()
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
          scheduled_end_date, 'Scheduled To End', data.app_name, data.parameter,
          data.working_dir, data.username, trigger_type, data.comment)
      parser_mediator.ProduceEvent(event_object)

    file_object.close()


manager.ParsersManager.RegisterParser(WinJobParser)
