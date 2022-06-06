# -*- coding: utf-8 -*-
"""IPS file parser plugin for Apple Crash logs."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import text_parser
from plaso.parsers import ips_parser
from plaso.parsers.ips_plugins import interface


class ApplicationCrashLogEventData(events.EventData):
  """Apple Crash log event data.

  Attributes:
    application_name (str): name of the application.
    application_version (str): version of the application.
    bug_type (str): type of bug.
    bundle_identifier (str): bundleID of the application.
    device_model (str): model of the device.
    incident_identifier (str): uuid for crash.
    os_version (str): version of the operating system.
    parent_process (str): name process that spawned the application
    parent_process_identifier (int): process identifier of the parent
    process_identifier (int): process identifier
    process_launch (str): timestamp for the launch of the application
    process_path (str): path to the executable
    user_identifier (int): user id under which the application was running.
  """
  DATA_TYPE = 'ios:ips:application_crash_log'

  def __init__(self):
    """Initializes event data."""
    super(ApplicationCrashLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application_name = None
    self.application_version = None
    self.bug_type = None
    self.bundle_identifier = None
    self.device_model = None
    self.incident_identifier = None
    self.os_version = None
    self.parent_process = None
    self.parent_process_identifier = None
    self.process_identifier = None
    self.process_launch = None
    self.process_path = None
    self.user_identifier = None


class ApplicationCrashLogsPlugin(interface.IPSPlugin):
  """Parses Apple Crash logs from IPS file."""

  NAME = 'apple_crash_log'
  DATA_FORMAT = 'IPS application crash log'

  REQUIRED_HEADER_KEYS = [
      'app_name', 'app_version', 'bug_type', 'bundleID', 'incident_id',
      'os_version', 'timestamp']
  REQUIRED_CONTENT_KEYS = [
      'modelCode', 'parentPid', 'parentProc', 'pid', 'procLaunch', 'procPath',
      'userID']

  _DATE_ELEMENTS = text_parser.PyparsingConstants.DATE_ELEMENTS

  _TIME_MSEC_ELEMENTS = text_parser.PyparsingConstants.TIME_MSEC_ELEMENTS

  _TIME_DELTA = pyparsing.Word(
      pyparsing.nums + '+' + '-', exact=5).setResultsName('time_delta')

  TIMESTAMP_GRAMMAR = _DATE_ELEMENTS + _TIME_MSEC_ELEMENTS + _TIME_DELTA

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, ips_file=None, **unused_kwargs):
    """Extracts information from an IPS log file.

    This is the main method that an IPS plugin needs to implement.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      ips_file (Optional[IpsFile]): database.

    Raises:
      ValueError: If the file value is missing.
    """
    if ips_file is None:
      raise ValueError('Missing ips_file value')

    # This will raise if unhandled keyword arguments are passed.
    super(ApplicationCrashLogsPlugin, self).Process(parser_mediator)

    event_data = ApplicationCrashLogEventData()
    event_data.application_name = ips_file.header.get('app_name')
    event_data.application_version = ips_file.header.get('app_version')
    event_data.bug_type = ips_file.header.get('bug_type')
    event_data.bundle_identifier = ips_file.header.get('bundleID')
    event_data.device_model = ips_file.content.get('modelCode')
    event_data.incident_identifier = ips_file.header.get('incident_id')
    event_data.os_version = ips_file.header.get('os_version')
    event_data.parent_process = ips_file.content.get('parentProc')
    event_data.parent_process_identifier = ips_file.content.get('parentPid')
    event_data.process_identifier = ips_file.content.get('pid')
    event_data.process_launch = ips_file.content.get('procLaunch')
    event_data.process_path = ips_file.content.get('procPath')
    event_data.user_identifier = ips_file.content.get('userID')

    timestamp = ips_file.header.get('timestamp')

    parsed_timestamp = self.TIMESTAMP_GRAMMAR.parseString(timestamp)

    # dfDateTime takes the time zone offset as number of minutes relative from
    # UTC. So for Easter Standard Time (EST), which is UTC-5:00 the sign needs
    # to be converted, to +300 minutes.
    try:
      time_delta_hours = int(parsed_timestamp['time_delta'][:3], 10)
      time_delta_minutes = int(parsed_timestamp['time_delta'][3:], 10)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('unsupported date time value')
      return

    time_zone_offset = (time_delta_hours * -60) + time_delta_minutes

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=(
              parsed_timestamp['year'], parsed_timestamp['month'],
              parsed_timestamp['day_of_month'], parsed_timestamp['hours'],
              parsed_timestamp['minutes'], parsed_timestamp['seconds']),
          time_zone_offset=time_zone_offset)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('unsupported date time value')
      return

    start_event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_START)

    parser_mediator.ProduceEventWithEventData(start_event, event_data)


ips_parser.IPSParser.RegisterPlugin(ApplicationCrashLogsPlugin)
