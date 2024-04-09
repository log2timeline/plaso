# -*- coding: utf-8 -*-
"""IPS log file parser plugin for Apple crash recovery report."""

from plaso.containers import events
from plaso.parsers import ips_parser
from plaso.parsers.ips_plugins import interface


class AppleRecoveryLogdEvent(events.EventData):
  """Apple crash recovery event data.

  Attributes:
    application_name (str): name of the application.
    application_version (str): version of the application.
    bug_type (str): type of bug.
    crash_reporter_key (str): Key of the crash reporter.
    device_model (str): model of the device.
    event_time (dfdatetime.DateTimeValues): date and time of the crash report.
    exception_type (str): type of the exception that caused the crash.
    incident_identifier (str): uuid for crash.
    operating_system_version (str): version of the operating system.
    parent_process_identifier (int): process identifier of the parent process.
    parent_process (str): parent process.
    process_identifier (int): process identifier.
    process_launch_time (dfdatetime.DateTimeValues): date and time when the
        process started.
    user_identifier (int): user identifier of the process.
  """
  DATA_TYPE = 'apple:ips_recovery_logd'

  def __init__(self):
    """Initializes event data."""
    super(AppleRecoveryLogdEvent, self).__init__(data_type=self.DATA_TYPE)
    self.application_name = None
    self.application_version = None
    self.bug_type = None
    self.crash_reporter_key = None
    self.device_model = None
    self.event_time = None
    self.exception_type = None
    self.incident_identifier = None
    self.operating_system_version = None
    self.parent_process_identifier = None
    self.parent_process = None
    self.process_identifier = None
    self.process_launch_time = None
    self.user_identifier = None


class AppleRecoveryLogdIPSPlugin(interface.IPSPlugin):
  """Parses Apple Crash logs from IPS file."""

  NAME = 'apple_recovery_ips'
  DATA_FORMAT = 'IPS recovery logd crash log'

  REQUIRED_HEADER_KEYS = frozenset([
      'app_name', 'app_version', 'bug_type', 'incident_id', 'os_version',
      'timestamp'])
  REQUIRED_CONTENT_KEYS = frozenset([
      'captureTime', 'modelCode', 'pid', 'procLaunch'])

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, ips_file=None, **unused_kwargs):
    """Extracts events from an Apple Crash IPS log file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      ips_file (Optional[IpsFile]): database.

    Raises:
      ValueError: If the file value is missing.
    """
    if ips_file is None:
      raise ValueError('Missing ips_file value')

    ips_exception = ips_file.content.get('exception', {})

    event_data = AppleRecoveryLogdEvent()
    event_data.application_name = ips_file.header.get('app_name')
    event_data.application_version = ips_file.header.get('app_version')
    event_data.bug_type = ips_file.header.get('bug_type')
    event_data.crash_reporter_key = ips_file.content.get('crashReporterKey')
    event_data.device_model = ips_file.content.get('modelCode')
    event_data.exception_type = ips_exception.get('type')
    event_data.incident_identifier = ips_file.header.get('incident_id')
    event_data.operating_system_version = ips_file.header.get('os_version')
    event_data.parent_process = ips_file.content.get('parentProc')
    event_data.parent_process_identifier = ips_file.content.get('parentPid')
    event_data.process_identifier = ips_file.content.get('pid')
    event_data.user_identifier = ips_file.content.get('userID')

    event_timestamp = ips_file.content.get('captureTime')
    event_data.event_time = self._ParseTimestampValue(
        parser_mediator, event_timestamp)

    launch_timestamp = ips_file.content.get('procLaunch')
    event_data.process_launch_time = self._ParseTimestampValue(
        parser_mediator, launch_timestamp)

    parser_mediator.ProduceEventData(event_data)


ips_parser.IPSParser.RegisterPlugin(AppleRecoveryLogdIPSPlugin)
