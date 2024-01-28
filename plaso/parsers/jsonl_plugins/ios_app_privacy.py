# -*- coding: utf-8 -*-
"""JSON-L parser plugin for iOS application privacy report files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class IOSAppPrivacyAccessEvent(events.EventData):
  """iOS application privacy report event of type access.

  Attributes:
    accessor_identifier (str): identifier of process accessing the resource
    accessor_identifier_type (str): type of identifier
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    resource_category (str): category of the accessed resource
    resource_identifier (str): GUID of the resource being accessed
  """

  DATA_TYPE = 'ios:app_privacy:access'

  def __init__(self):
    """Initializes event data."""
    super(IOSAppPrivacyAccessEvent, self).__init__(data_type=self.DATA_TYPE)
    self.accessor_identifier = None
    self.accessor_identifier_type = None
    self.recorded_time = None
    self.resource_category = None
    self.resource_identifier = None


class IOSAppPrivacyNetworkEvent(events.EventData):
  """iOS application privacy report event of type network activity.

  Attributes:
    bundle_identifier (str): bundle identifier that accesssed the resource
    domain (str): domain name accessed
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
  """
  DATA_TYPE = 'ios:app_privacy:network'

  def __init__(self):
    """Initializes event data."""
    super(IOSAppPrivacyNetworkEvent, self).__init__(data_type=self.DATA_TYPE)
    self.bundle_identifier = None
    self.domain = None
    self.recorded_time = None


class IOSAppPrivacPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for iOS application privacy report files."""

  NAME = 'ios_application_privacy'
  DATA_FORMAT = 'iOS Application Privacy report'

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses an iOS application privacy report record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    event_type = self._GetJSONValue(json_dict, 'type')
    if not event_type:
      parser_mediator.ProduceExtractionWarning('Missing event type.')
      return

    if event_type not in ('access', 'networkActivity'):
      parser_mediator.ProduceExtractionWarning(
          'Unsupported event type: {0:s}.'.format(event_type))
      return

    date_time = None

    event_timestamp = self._GetJSONValue(json_dict, 'timeStamp')
    if event_timestamp:
      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(event_timestamp)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse time string: {0:s} with error: {1!s}'.format(
                event_timestamp, exception))
        date_time = None

    if event_type == 'access':
      event_data = self._ParseRecordAccess(json_dict)
    else:
      event_data = self._ParseRecordNetwork(json_dict)

    event_data.recorded_time = date_time

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecordAccess(self, json_dict):
    """Parses an iOS application privacy report record of type access.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      IOSAppPrivacyAccess: populated event.
    """
    event_data = IOSAppPrivacyAccessEvent()

    event_accessor = self._GetJSONValue(json_dict, 'accessor')
    if event_accessor:
      event_data.accessor_identifier = self._GetJSONValue(
          event_accessor, 'identifier')
      event_data.accessor_identifier_type = self._GetJSONValue(
          event_accessor, 'identifierType')

    event_data.resource_identifier = self._GetJSONValue(
        json_dict, 'identifier')

    event_data.resource_category = self._GetJSONValue(json_dict, 'category')

    return event_data

  def _ParseRecordNetwork(self, json_dict):
    """Parses an iOS application privacy report record of type network activity.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      IOSAppPrivacyNetwork: populated event.
    """
    event_data = IOSAppPrivacyNetworkEvent()

    event_data.domain = self._GetJSONValue(json_dict, 'domain')
    event_data.bundle_identifier = self._GetJSONValue(json_dict, 'bundleID')

    return event_data

  def CheckRequiredFormat(self, json_dict):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    event_timestamp = self._GetJSONValue(json_dict, 'timeStamp')
    event_type = self._GetJSONValue(json_dict, 'type')

    if None in (event_timestamp, event_type):
      return False

    if event_type not in ('access', 'networkActivity'):
      return False

    if event_type == 'access':
      event_category = self._GetJSONValue(json_dict, 'category')
      event_accessor_identifier = json_dict.get(
          'accessor').get('identifier') or None
      if None in (event_category, event_accessor_identifier):
        return False

    elif event_type == 'networkActivity':
      event_domain = self._GetJSONValue(json_dict, 'domain')
      event_bundle_identifier = json_dict.get('bundleID') or None
      if None in (event_domain, event_bundle_identifier):
        return False

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

    try:
      date_time.CopyFromStringISO8601(event_timestamp)
    except ValueError:
      return False

    return True


jsonl_parser.JSONLParser.RegisterPlugin(IOSAppPrivacPlugin)
