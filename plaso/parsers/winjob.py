# -*- coding: utf-8 -*-
"""Parser for Windows Scheduled Task job files."""

import os

from dfdatetime import definitions as dfdatetime_definitions
from dfdatetime import systemtime as dfdatetime_systemtime
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class WinJobEventData(events.EventData):
  """Windows Scheduled Task event data.

  Attributes:
    application (str): path to job executable.
    comment (str): description of the scheduled task.
    last_run_time (dfdatetime.DateTimeValues): executable (binary) last run
        date and time.
    parameters (str): application command line parameters.
    username (str): username that scheduled the task.
    working_directory (str): working directory of the scheduled task.
  """

  DATA_TYPE = 'windows:tasks:job'

  def __init__(self):
    """Initializes event data."""
    super(WinJobEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application = None
    self.comment = None
    self.last_run_time = None
    self.parameters = None
    self.username = None
    self.working_directory = None


class WinJobTriggerEventData(events.EventData):
  """Windows Scheduled Task trigger event data.

  Attributes:
    application (str): path to job executable.
    comment (str): description of the scheduled task.
    end_time (dfdatetime.DateTimeValues): date and time the end of the trigger.
    parameters (str): application command line parameters.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the trigger.
    trigger_type (int): trigger type.
    username (str): username that scheduled the task.
    working_directory (str): working directory of the scheduled task.
  """

  DATA_TYPE = 'windows:tasks:trigger'

  def __init__(self):
    """Initializes event data."""
    super(WinJobTriggerEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application = None
    self.comment = None
    self.end_time = None
    self.parameters = None
    self.start_time = None
    self.trigger_type = None
    self.username = None
    self.working_directory = None


class WinJobParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Parse Windows Scheduled Task files for job events."""

  NAME = 'winjob'
  DATA_FORMAT = 'Windows Scheduled Task job (or at-job) file'

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'winjob.yaml')

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

  def _ParseEventData(self, variable_length_section):
    """Parses the event data form a variable-length data section.

    Args:
      variable_length_section (job_variable_length_data_section): a
          Windows Scheduled Task job variable-length data section.

    Returns:
      WinJobEventData: event data of the job file.
    """
    event_data = WinJobEventData()
    event_data.application = variable_length_section.application_name or None
    event_data.comment = variable_length_section.comment or None
    event_data.parameters = variable_length_section.parameters or None
    event_data.username = variable_length_section.author or None
    event_data.working_directory = (
        variable_length_section.working_directory or None)

    return event_data

  def _ParseLastRunTime(self, parser_mediator, fixed_length_section):
    """Parses the last run time from a fixed-length data section.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      fixed_length_section (job_fixed_length_data_section): a Windows
          Scheduled Task job fixed-length data section.

    Returns:
      dfdatetime.DateTimeValues: last run date and time or None if not
          available.
    """
    systemtime_struct = fixed_length_section.last_run_time
    system_time_tuple = (
        systemtime_struct.year, systemtime_struct.month,
        systemtime_struct.weekday, systemtime_struct.day_of_month,
        systemtime_struct.hours, systemtime_struct.minutes,
        systemtime_struct.seconds, systemtime_struct.milliseconds)

    date_time = None
    if system_time_tuple != self._EMPTY_SYSTEM_TIME_TUPLE:
      try:
        date_time = dfdatetime_systemtime.Systemtime(
            system_time_tuple=system_time_tuple)
      except ValueError:
        parser_mediator.ProduceExtractionWarning(
            'invalid last run time: {0!s}'.format(system_time_tuple))

    return date_time

  def _ParseTriggerEventData(self, variable_length_section):
    """Parses the trigger event data form a variable-length data section.

    Args:
      variable_length_section (job_variable_length_data_section): a
          Windows Scheduled Task job variable-length data section.

    Returns:
      WinJobTriggerEventData: event data of the job file.
    """
    event_data = WinJobTriggerEventData()
    event_data.application = variable_length_section.application_name or None
    event_data.comment = variable_length_section.comment or None
    event_data.parameters = variable_length_section.parameters or None
    event_data.username = variable_length_section.author or None
    event_data.working_directory = (
        variable_length_section.working_directory or None)

    return event_data

  def _ParseTriggerEndTime(self, parser_mediator, trigger):
    """Parses the end time from a trigger.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      trigger (job_trigger): a trigger.

    Returns:
      dfdatetime.DateTimeValues: last run date and time or None if not
          available.
    """
    time_elements_tuple = (
        trigger.end_date.year, trigger.end_date.month,
        trigger.end_date.day_of_month, 0, 0, 0)

    date_time = None
    if time_elements_tuple != (0, 0, 0, 0, 0, 0):
      try:
        date_time = dfdatetime_time_elements.TimeElements(
            precision=dfdatetime_definitions.PRECISION_1_DAY,
            time_elements_tuple=time_elements_tuple)

        date_time.is_local_time = True

      except ValueError:
        parser_mediator.ProduceExtractionWarning(
            'invalid trigger end time: {0!s}'.format(time_elements_tuple))

    return date_time

  def _ParseTriggerStartTime(self, parser_mediator, trigger):
    """Parses the start time from a trigger.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      trigger (job_trigger): a trigger.

    Returns:
      dfdatetime.DateTimeValues: last run date and time or None if not
          available.
    """
    time_elements_tuple = (
        trigger.start_date.year, trigger.start_date.month,
        trigger.start_date.day_of_month, trigger.start_time.hours,
        trigger.start_time.minutes, 0)

    date_time = None
    if time_elements_tuple != (0, 0, 0, 0, 0, 0):
      try:
        date_time = dfdatetime_time_elements.TimeElements(
            precision=dfdatetime_definitions.PRECISION_1_MINUTE,
            time_elements_tuple=time_elements_tuple)

        date_time.is_local_time = True

      except ValueError:
        parser_mediator.ProduceExtractionWarning(
            'invalid trigger start time: {0!s}'.format(time_elements_tuple))

    return date_time

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows job file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    fixed_section_data_map = self._GetDataTypeMap(
        'job_fixed_length_data_section')

    try:
      fixed_length_section, file_offset = self._ReadStructureFromFileObject(
          file_object, 0, fixed_section_data_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse fixed-length data section with error: {0!s}'.format(
              exception))

    if not fixed_length_section.product_version in self._PRODUCT_VERSIONS:
      raise errors.WrongParser(
          'Unsupported product version in: 0x{0:04x}'.format(
              fixed_length_section.product_version))

    if not fixed_length_section.format_version == 1:
      raise errors.WrongParser(
          'Unsupported format version in: {0:d}'.format(
              fixed_length_section.format_version))

    variable_section_data_map = self._GetDataTypeMap(
        'job_variable_length_data_section')

    try:
      variable_length_section, data_size = self._ReadStructureFromFileObject(
          file_object, file_offset, variable_section_data_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser((
          'Unable to parse variable-length data section with error: '
          '{0!s}').format(exception))

    file_offset += data_size

    event_data = self._ParseEventData(variable_length_section)
    event_data.last_run_time = self._ParseLastRunTime(
        parser_mediator, fixed_length_section)

    parser_mediator.ProduceEventData(event_data)

    trigger_data_map = self._GetDataTypeMap('job_trigger')

    for trigger_index in range(variable_length_section.number_of_triggers):
      try:
        trigger, data_size = self._ReadStructureFromFileObject(
            file_object, file_offset, trigger_data_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse trigger: {0:d} with error: {1!s}').format(
                trigger_index, exception))
        break

      file_offset += data_size

      event_data = self._ParseTriggerEventData(variable_length_section)
      event_data.end_time = self._ParseTriggerEndTime(parser_mediator, trigger)
      event_data.start_time = self._ParseTriggerStartTime(
          parser_mediator, trigger)
      event_data.trigger_type = trigger.trigger_type

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(WinJobParser)
