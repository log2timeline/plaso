# -*- coding: utf-8 -*-
"""Parser for Windows Scheduled Task job files."""

from __future__ import unicode_literals

import construct

from dfdatetime import definitions as dfdatetime_definitions
from dfdatetime import systemtime as dfdatetime_systemtime
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import binary
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


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

  DATA_TYPE = 'windows:tasks:job'

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

  NAME = 'winjob'
  DESCRIPTION = 'Parser for Windows Scheduled Task job (or At-job) files.'

  _EMPTY_SYSTEM_TIME_TUPLE = (0, 0, 0, 0, 0, 0, 0, 0)

  _PRODUCT_VERSIONS = {
      0x0400: 'Windows NT 4.0',
      0x0500: 'Windows 2000',
      0x0501: 'Windows XP',
      0x0600: 'Windows Vista',
      0x0601: 'Windows 7',
      0x0602: 'Windows 8',
      0x0603: 'Windows 8.1',
      0x0a00: 'Windows 10',
  }

  _JOB_FIXED_LENGTH_SECTION_STRUCT = construct.Struct(
      'job_fixed_length_section',
      construct.ULInt16('product_version'),
      construct.ULInt16('format_version'),
      construct.Bytes('job_uuid', 16),
      construct.ULInt16('application_length_offset'),
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
      construct.Struct(
          'last_run_time',
          construct.ULInt16('year'),
          construct.ULInt16('month'),
          construct.ULInt16('weekday'),
          construct.ULInt16('day'),
          construct.ULInt16('hours'),
          construct.ULInt16('minutes'),
          construct.ULInt16('seconds'),
          construct.ULInt16('milliseconds')))

  # Using Construct's utf-16 encoding here will create strings with their
  # null terminators exposed. Instead, we'll read these variables raw and
  # convert them using Plaso's ReadUTF16() for proper formatting.
  _JOB_VARIABLE_STRUCT = construct.Struct(
      'job_variable_length_section',
      construct.ULInt16('running_instance_count'),
      construct.ULInt16('application_length'),
      construct.String(
          'application',
          lambda ctx: ctx.application_length * 2),
      construct.ULInt16('parameter_length'),
      construct.String(
          'parameter',
          lambda ctx: ctx.parameter_length * 2),
      construct.ULInt16('working_directory_length'),
      construct.String(
          'working_directory',
          lambda ctx: ctx.working_directory_length * 2),
      construct.ULInt16('username_length'),
      construct.String(
          'username',
          lambda ctx: ctx.username_length * 2),
      construct.ULInt16('comment_length'),
      construct.String(
          'comment',
          lambda ctx: ctx.comment_length * 2),
      construct.ULInt16('userdata_length'),
      construct.String(
          'userdata',
          lambda ctx: ctx.userdata_length),
      construct.ULInt16('reserved_length'),
      construct.String(
          'reserved',
          lambda ctx: ctx.reserved_length),
      construct.ULInt16('number_of_triggers'))

  _TRIGGER_STRUCT = construct.Struct(
      'trigger',
      construct.ULInt16('size'),
      construct.ULInt16('reserved1'),
      construct.ULInt16('start_year'),
      construct.ULInt16('start_month'),
      construct.ULInt16('start_day'),
      construct.ULInt16('end_year'),
      construct.ULInt16('end_month'),
      construct.ULInt16('end_day'),
      construct.ULInt16('start_hour'),
      construct.ULInt16('start_minute'),
      construct.ULInt32('duration'),
      construct.ULInt32('interval'),
      construct.ULInt32('trigger_flags'),
      construct.ULInt32('trigger_type'),
      construct.ULInt16('trigger_arg0'),
      construct.ULInt16('trigger_arg1'),
      construct.ULInt16('trigger_arg2'),
      construct.ULInt16('trigger_padding'),
      construct.ULInt16('trigger_reserved2'),
      construct.ULInt16('trigger_reserved3'))

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
          'Unable to parse fixed-length section with error: {0!s}'.format(
              exception))

    if not header_struct.product_version in self._PRODUCT_VERSIONS:
      raise errors.UnableToParseFile(
          'Unsupported product version in: 0x{0:04x}'.format(
              header_struct.product_version))

    if not header_struct.format_version == 1:
      raise errors.UnableToParseFile(
          'Unsupported format version in: {0:d}'.format(
              header_struct.format_version))

    try:
      job_variable_struct = self._JOB_VARIABLE_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse variable-length section with error: {0!s}'.format(
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
      except ValueError:
        parser_mediator.ProduceExtractionError(
            'invalid last run time: {0!s}'.format(system_time_tuple))

    if date_time:
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_RUN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for index in range(job_variable_struct.number_of_triggers):
      try:
        trigger_struct = self._TRIGGER_STRUCT.parse_stream(file_object)
      except (IOError, construct.FieldError) as exception:
        parser_mediator.ProduceExtractionError(
            'unable to parse trigger: {0:d} with error: {1!s}'.format(
                index, exception))
        return

      event_data.trigger_type = trigger_struct.trigger_type

      time_elements_tuple = (
          trigger_struct.start_year, trigger_struct.start_month,
          trigger_struct.start_day, trigger_struct.start_hour,
          trigger_struct.start_minute, 0)

      if time_elements_tuple != (0, 0, 0, 0, 0, 0):
        try:
          date_time = dfdatetime_time_elements.TimeElements(
              time_elements_tuple=time_elements_tuple)
          date_time.is_local_time = True
          date_time.precision = dfdatetime_definitions.PRECISION_1_MINUTE
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionError(
              'invalid trigger start time: {0!s}'.format(time_elements_tuple))

        if date_time:
          event = time_events.DateTimeValuesEvent(
              date_time, 'Scheduled to start',
              time_zone=parser_mediator.timezone)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      time_elements_tuple = (
          trigger_struct.end_year, trigger_struct.end_month,
          trigger_struct.end_day, 0, 0, 0)

      if time_elements_tuple != (0, 0, 0, 0, 0, 0):
        try:
          date_time = dfdatetime_time_elements.TimeElements(
              time_elements_tuple=time_elements_tuple)
          date_time.is_local_time = True
          date_time.precision = dfdatetime_definitions.PRECISION_1_DAY
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionError(
              'invalid trigger end time: {0!s}'.format(time_elements_tuple))

        if date_time:
          event = time_events.DateTimeValuesEvent(
              date_time, 'Scheduled to end',
              time_zone=parser_mediator.timezone)
          parser_mediator.ProduceEventWithEventData(event, event_data)

    # TODO: create a timeless event object if last_run_time and
    # trigger_start_time are None? What should be the description of
    # this event?


manager.ParsersManager.RegisterParser(WinJobParser)
