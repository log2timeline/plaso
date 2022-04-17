# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Azure activity log files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class AzureActivityLogEventData(events.EventData):
  """Azure activity log event data.

  Attributes:
    caller (str): Azure identity.
    client_ip (str): client IP address.
    correlation_identifier (str): Correlation identifier.
    event_data_identifier (str): Event data identifier.
    event_name (str): name of the event.
    level (str): log level.
    operation_identifier (str): Operation identifier.
    operation_name (str): operation name.
    resource_group (str): resource group.
    resource_identifier (str): resource.
    resource_provider (str): API service.
    resource_type (str): resource type.
    subscription_identifier (str): subscription identifier.
    tenant_identifier (str): tenant identifier.
  """

  DATA_TYPE = 'azure:activitylog:entry'

  def __init__(self):
    """Initializes event data."""
    super(AzureActivityLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caller = None
    self.client_ip = None
    self.correlation_identifier = None
    self.event_data_identifier = None
    self.event_name = None
    self.level = None
    self.operation_identifier = None
    self.operation_name = None
    self.resource_group = None
    self.resource_identifier = None
    self.resource_provider = None
    self.resource_type = None
    self.subscription_identifier = None
    self.tenant_identifier = None


class AzureActivityLogJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Azure activity log files."""

  NAME = 'azure_activity_log'
  DATA_FORMAT = 'Azure Activity Log'

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses an Azure activity log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    event_timestamp = self._GetJSONValue(json_dict, 'event_timestamp')
    if not event_timestamp:
      parser_mediator.ProduceExtractionWarning(
          'Event timestamp value missing from activity log entry')

    event_data = AzureActivityLogEventData()
    event_data.caller = self._GetJSONValue(json_dict, 'caller')
    event_data.event_data_identifier = self._GetJSONValue(
        json_dict, 'event_data_id')
    event_data.correlation_identifier = self._GetJSONValue(
        json_dict, 'correlation_id')

    event_name_json = self._GetJSONValue(json_dict, 'event_name')
    if event_name_json:
      event_data.event_name = self._GetJSONValue(event_name_json, 'value')

    http_request_json = self._GetJSONValue(json_dict, 'http_request')
    if http_request_json:
      event_data.client_ip = self._GetJSONValue(
        http_request_json, 'client_ip_address')

    event_data.level = self._GetJSONValue(json_dict, 'level')
    event_data.resource_group = self._GetJSONValue(
        json_dict, 'resource_group_name')

    resource_provider_name_json = self._GetJSONValue(
        json_dict, 'resource_provider_name')
    if resource_provider_name_json:
      event_data.resource_provider = self._GetJSONValue(
          resource_provider_name_json, 'value')

    event_data.resource_identifier = self._GetJSONValue(
        json_dict, 'resource_id')

    resource_type_json = self._GetJSONValue(json_dict, 'resource_type')
    if resource_type_json:
      event_data.resource_type = self._GetJSONValue(
          resource_type_json, 'value')

    event_data.operation_identifier = self._GetJSONValue(
        json_dict, 'operation_id')

    operation_name_json = self._GetJSONValue(json_dict, 'operation_name')
    if operation_name_json:
      event_data.operation_name = self._GetJSONValue(
          operation_name_json, 'value')

    event_data.subscription_identifier = self._GetJSONValue(
        json_dict, 'subscription_id')
    event_data.tenant_identifier = self._GetJSONValue(json_dict, 'tenant_id')

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(event_timestamp)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse time string: {0:s} with error: {1!s}'.format(
              event_timestamp, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    event_timestamp = json_dict.get('event_timestamp') or None
    subscription_identifier = json_dict.get('subscription_id') or None

    if None in (event_timestamp, subscription_identifier):
      return False

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(event_timestamp)
    except ValueError:
      return False

    return True


jsonl_parser.JSONLParser.RegisterPlugin(AzureActivityLogJSONLPlugin)
