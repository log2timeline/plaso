# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Google Cloud (GCP) log files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class GCPLogEventData(events.EventData):
  """Google Cloud (GCP) log event data.

  Attributes:
    container (str): TODO
    event_subtype (str): JSON event sub type or protocol buffer method.
    event_type (str): TODO
    filename (str): TODO
    firewall_rules (list[str]): firewall rules.
    firewall_source_ranges (list[str]): firewall source ranges.
    log_name (str): name of the log entry.
    message (str): TODO
    policy_deltas (list[str]): TODO
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    request_account_identifier (str): GCP account identifier of the request.
    request_description (str): description of the request.
    request_direction (str): direction of the request.
    request_email (str): email address of the request.
    request_member (str): member of the request.
    request_metadata (list[str]): request metadata values.
    request_name (str): name of the request.
    request_target_tags (str): TODO
    resource_labels (list[str]): resource labels.
    resource_name (str): name of the resource.
    service_account_display_name (str): display name of the service account.
    service_name (str): name of the servie.
    severity (str): log entry severity.
    text_payload (str): text payload for logs not using a JSON or proto payload.
    user (str): user principal performing the logged action.
  """

  DATA_TYPE = 'gcp:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(GCPLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.container = None
    self.event_subtype = None
    self.event_type = None
    self.filename = None
    self.firewall_rules = None
    self.firewall_source_ranges = None
    self.log_name = None
    self.message = None
    self.policy_deltas = None
    self.recorded_time = None
    self.request_account_identifier = None
    self.request_description = None
    self.request_direction = None
    self.request_email = None
    self.request_member = None
    self.request_metadata = None
    self.request_name = None
    self.request_target_tags = None
    self.resource_labels = None
    self.resource_name = None
    self.service_account_display_name = None
    self.service_name = None
    self.severity = None
    self.text_payload = None
    self.user = None


class GCPLogJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Google Cloud (GCP) log files."""

  NAME = 'gcp_log'
  DATA_FORMAT = 'Google Cloud (GCP) log'

  def _ParseJSONPayload(self, json_dict, event_data):
    """Extracts information from a jsonPayload value.

    Args:
      json_dict (dict): JSON dictionary of the log record.
      event_data (GCPLogEventData): event data.
    """
    json_payload = self._GetJSONValue(json_dict, 'jsonPayload')
    if not json_payload:
      return

    event_data.container = self._GetJSONValue(json_payload, 'container')
    event_data.event_subtype = self._GetJSONValue(json_payload, 'event_subtype')
    event_data.event_type = self._GetJSONValue(json_payload, 'event_type')
    event_data.filename = self._GetJSONValue(json_payload, 'filename')
    event_data.message = self._GetJSONValue(json_payload, 'message')

    actor_json = self._GetJSONValue(json_payload, 'actor')
    if actor_json:
      event_data.user = self._GetJSONValue(actor_json, 'user')

  def _ParseProtoPayload(self, json_dict, event_data):
    """Extracts information from a protoPayload value.

    Args:
      json_dict (dict): JSON dictionary of the log record.
      event_data (GCPLogEventData): event data.
    """
    proto_payload = self._GetJSONValue(json_dict, 'protoPayload')
    if not proto_payload:
      return

    authentication_info = self._GetJSONValue(
        proto_payload, 'authenticationInfo')
    if authentication_info and not event_data.user:
      event_data.user = self._GetJSONValue(
          authentication_info, 'principalEmail')

    request_metadata = self._GetJSONValue(
        proto_payload, 'requestMetadata', default_value={})
    event_data.request_metadata = [
        '{0:s}: {1!s}'.format(name, value)
        for name, value in request_metadata.items()]

    event_data.service_name = self._GetJSONValue(proto_payload, 'serviceName')
    event_data.resource_name = self._GetJSONValue(proto_payload, 'resourceName')

    method_name = self._GetJSONValue(proto_payload, 'methodName')
    if method_name and not event_data.event_subtype:
      event_data.event_subtype = method_name

    self._ParseProtoPayloadRequest(proto_payload, event_data)
    self._ParseProtoPayloadServiceData(proto_payload, event_data)

  def _ParseProtoPayloadRequest(self, json_dict, event_data):
    """Extracts information from the request field of a protoPayload field.

    Args:
      json_dict (dict): JSON dictionary of the protoPayload value.
      event_data (GCPLogEventData): event data.
    """
    request = self._GetJSONValue(json_dict, 'request')
    if not request:
      return

    event_data.request_account_identifier = self._GetJSONValue(
        request, 'account_id')
    event_data.request_description = self._GetJSONValue(request, 'description')
    event_data.request_direction = self._GetJSONValue(request, 'direction')
    event_data.request_email = self._GetJSONValue(request, 'email')
    event_data.request_member = self._GetJSONValue(request, 'member')
    event_data.request_name = self._GetJSONValue(request, 'name')
    event_data.request_target_tags = self._GetJSONValue(request, 'targetTags')

    # Firewall specific attributes.
    event_data.firewall_source_ranges = self._GetJSONValue(
        request, 'sourceRanges')

    firewall_rules = []

    alloweds = self._GetJSONValue(request, 'alloweds', default_value=[])
    for allowed in alloweds:
      ip_protocol = self._GetJSONValue(allowed, 'IPProtocol')
      ports = self._GetJSONValue(allowed, 'ports', default_value='all')

      firewall_rule = 'ALLOW: {0:s} {1!s}'.format(ip_protocol, ports)
      firewall_rules.append(firewall_rule)

    denieds = self._GetJSONValue(request, 'denieds', default_value=[])
    for denied in denieds:
      ip_protocol = self._GetJSONValue(denied, 'IPProtocol')
      ports = self._GetJSONValue(denied, 'ports', default_value='all')

      firewall_rule = 'DENY: {0:s} {1!s}'.format(ip_protocol, ports)
      firewall_rules.append(firewall_rule)

    event_data.firewall_rules = firewall_rules or None

    # Service account specific attributes
    service_account = self._GetJSONValue(request, 'service_account')
    if service_account:
      event_data.service_account_display_name = self._GetJSONValue(
          service_account, 'display_name')

  def _ParseProtoPayloadServiceData(self, json_dict, event_data):
    """Extracts information from the serviceData in the protoPayload value.

    Args:
      json_dict (dict): JSON dictionary of the protoPayload value.
      event_data (GCPLogEventData): event data.
    """
    service_data = self._GetJSONValue(json_dict, 'serviceData')
    if not service_data:
      return

    policy_delta = self._GetJSONValue(service_data, 'policyDelta')
    if not policy_delta:
      return

    policy_deltas = []

    binding_deltas = self._GetJSONValue(
        policy_delta, 'bindingDeltas', default_value=[])
    for binding_delta_value in binding_deltas:
      action = self._GetJSONValue(
          binding_delta_value, 'action', default_value='')
      member = self._GetJSONValue(
          binding_delta_value, 'member', default_value='')
      role = self._GetJSONValue(binding_delta_value, 'role', default_value='')

      policy_delta = '{0:s} {1:s} with role {2:s}'.format(action, member, role)
      policy_deltas.append(policy_delta)

    event_data.policy_deltas = policy_deltas or None

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses a Google Cloud (GCP) log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    resource = self._GetJSONValue(json_dict, 'resource', default_value={})
    labels = self._GetJSONValue(resource, 'labels', default_value={})

    resource_labels = [
        '{0:s}: {1!s}'.format(name, value) for name, value in labels.items()]

    event_data = GCPLogEventData()
    event_data.log_name = self._GetJSONValue(json_dict, 'logName')
    event_data.recorded_time = self._ParseISO8601DateTimeString(
        parser_mediator, json_dict, 'timestamp')
    event_data.resource_labels = resource_labels or None
    event_data.severity = self._GetJSONValue(json_dict, 'severity')
    event_data.text_payload = self._GetJSONValue(json_dict, 'textPayload')

    self._ParseJSONPayload(json_dict, event_data)
    self._ParseProtoPayload(json_dict, event_data)

    parser_mediator.ProduceEventData(event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    log_name = json_dict.get('logName') or None
    timestamp = json_dict.get('timestamp') or None

    if None in (log_name, timestamp):
      return False

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

    try:
      date_time.CopyFromStringISO8601(timestamp)
    except ValueError:
      return False

    return True


jsonl_parser.JSONLParser.RegisterPlugin(GCPLogJSONLPlugin)
