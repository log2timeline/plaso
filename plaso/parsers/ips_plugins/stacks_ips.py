# -*- coding: utf-8 -*-
"""IPS log file parser plugin for Apple stacks report."""

from plaso.containers import events
from plaso.parsers import ips_parser
from plaso.parsers.ips_plugins import interface


class AppleStacksIPSEvent(events.EventData):
  """Apple stacks crash report.

  Attributes:
    bug_type (str): type of bug.
    crash_reporter_key (str): Key of the crash reporter.
    device_model (str): model of the device.
    event_time (dfdatetime.DateTimeValues): date and time of the crash report.
    incident_identifier (str): uuid for crash.
    kernel_version (str): kernel version.
    operating_system_version (str): version of the operating system.
    process_list (str): list of process names running at the time of the crash.
    reason (str): reason for the crash.
  """

  DATA_TYPE = 'apple:ips_stacks'

  def __init__(self):
    """Initializes event data."""
    super(AppleStacksIPSEvent, self).__init__(data_type=self.DATA_TYPE)
    self.bug_type = None
    self.crash_reporter_key = None
    self.device_model = None
    self.event_time = None
    self.incident_identifier = None
    self.kernel_version = None
    self.operating_system_version = None
    self.process_list = None
    self.reason = None


class AppleStacksIPSPlugin(interface.IPSPlugin):
  """Parses Apple stacks crash IPS file."""

  NAME = 'apple_stacks_ips'
  DATA_FORMAT = 'IPS stacks crash log'

  REQUIRED_HEADER_KEYS = frozenset([
      'bug_type', 'incident_id', 'os_version', 'timestamp'])
  REQUIRED_CONTENT_KEYS = frozenset([
      'build', 'crashReporterKey', 'kernel', 'product', 'reason'])

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, ips_file=None, **unused_kwargs):
    """Extracts information from an Apple stacks crash IPS log file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      ips_file (Optional[IpsFile]): database.

    Raises:
      ValueError: If the file value is missing.
    """
    if ips_file is None:
      raise ValueError('Missing ips_file value')

    event_data = AppleStacksIPSEvent()
    event_data.bug_type = ips_file.header.get('bug_type')
    event_data.crash_reporter_key = ips_file.content.get('crashReporterKey')
    event_data.device_model = ips_file.content.get('product')
    event_data.kernel_version = ips_file.content.get('kernel')
    event_data.incident_identifier = ips_file.header.get('incident_id')
    event_data.operating_system_version = ips_file.header.get('os_version')
    event_data.reason = ips_file.content.get('reason')

    process_list = [
        i.get('procname') for i in ips_file.content.get(
            'processByPid').values()]
    process_list = list(set(process_list))
    process_list.sort()

    event_data.process_list = ', '.join(process_list)

    event_timestamp = ips_file.header.get('timestamp')
    event_data.event_time = self._ParseTimestampValue(
        parser_mediator, event_timestamp)

    parser_mediator.ProduceEventData(event_data)


ips_parser.IPSParser.RegisterPlugin(AppleStacksIPSPlugin)
