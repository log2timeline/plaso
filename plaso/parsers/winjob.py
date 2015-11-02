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
  """Convenience class for a Windows Scheduled Task event.

  Attributes:
    application: string that contains the path to job executable.
    comment: string that contains the job description.
    parameter: string that contains the application command line parameters.
    trigger: an integer that contains the event trigger, e.g. DAILY.
    username: string that contains the username that scheduled the job.
    working_dir: string that contains the working path for task.
  """

  DATA_TYPE = u'windows:tasks:job'

  def __init__(
      self, timestamp, timestamp_description, application, parameter,
      working_dir, username, trigger, description):
    """Initializes the event object.

    Args:
      timestamp: the timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: the usage string for the timestamp value.
      application: string that contains the path to job executable.
      parameter: string that contains the application command line parameters.
      working_dir: string that contains the working path for task.
      username: string that contains the username that scheduled the job.
      trigger: an integer that contains the event trigger, e.g. DAILY.
      description: string that contains the job description.
    """
    super(WinJobEvent, self).__init__(timestamp, timestamp_description)
    self.application = application
    self.comment = description
    self.parameter = parameter
    self.trigger = trigger
    self.username = username
    self.working_dir = working_dir


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
      0x0603: u'Windows 8.1'
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

    last_run_date = timelib.Timestamp.FromTimeParts(
        header_struct.ran_year,
        header_struct.ran_month,
        header_struct.ran_day,
        header_struct.ran_hour,
        header_struct.ran_minute,
        header_struct.ran_second,
        microseconds=header_struct.ran_millisecond * 1000,
        timezone=parser_mediator.timezone)

    scheduled_date = timelib.Timestamp.FromTimeParts(
        job_variable_struct.sched_start_year,
        job_variable_struct.sched_start_month,
        job_variable_struct.sched_start_day,
        job_variable_struct.sched_start_hour,
        job_variable_struct.sched_start_minute,
        0,  # Seconds are not stored.
        timezone=parser_mediator.timezone)

    application = binary.ReadUtf16(job_variable_struct.application)
    description = binary.ReadUtf16(job_variable_struct.comment)
    parameter = binary.ReadUtf16(job_variable_struct.parameter)
    username = binary.ReadUtf16(job_variable_struct.username)
    working_dir = binary.ReadUtf16(job_variable_struct.working_dir)

    parser_mediator.ProduceEvents(
        [WinJobEvent(
            last_run_date, eventdata.EventTimestamp.LAST_RUNTIME, application,
            parameter, working_dir, username, job_variable_struct.trigger_type,
            description),
         WinJobEvent(
             scheduled_date, u'Scheduled To Start', application, parameter,
             working_dir, username, job_variable_struct.trigger_type,
             description)])

    if job_variable_struct.sched_end_year:
      scheduled_end_date = timelib.Timestamp.FromTimeParts(
          job_variable_struct.sched_end_year,
          job_variable_struct.sched_end_month,
          job_variable_struct.sched_end_day,
          0,  # Hours are not stored.
          0,  # Minutes are not stored.
          0,  # Seconds are not stored.
          timezone=parser_mediator.timezone)

      event_object = WinJobEvent(
          scheduled_end_date, u'Scheduled To End', application, parameter,
          working_dir, username, job_variable_struct.trigger_type, description)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(WinJobParser)
