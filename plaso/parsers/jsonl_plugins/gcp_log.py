# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Google Cloud (GCP) log files."""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class GCPLogEventData(events.EventData):
  """Google Cloud (GCP) log event data.

  Attributes:
    caller_ip (str): IP address of the client that requested the operation.
    container (str): TODO
    dcsa_emails (list[str]): default compute service account attached to a
        Google Compute Engine (GCE) instance.
    dcsa_scopes (list[str]): OAuth scopes granted to the default compute service
        account.
    delegation_chain (str): service account delegation chain.
    event_subtype (str): JSON event sub type or protocol buffer method.
    event_type (str): TODO
    filename (str): TODO
    firewall_rules (list[str]): firewall rules.
    firewall_source_ranges (list[str]): firewall source ranges.
    gcloud_command_identity (str): unique gcloud command identity.
    gcloud_command_partial (str): partial gcloud command.
    log_name (str): name of the log entry.
    message (str): TODO
    method_name (str): operation performed.
    permissions (list[str]): IAM permission used for the operation.
    policy_deltas (list[str]): TODO
    principal_email (str): email address of the requester.
    principal_subject (str): subject name of the requester.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    request_account_identifier (str): GCP account identifier of the request.
    request_address (str): IP address assigned to a Google Cloud Engine (GCE)
        instance.
    request_description (str): description of the request.
    request_direction (str): direction of the request.
    request_email (str): email address of the request.
    request_member (str): member of the request.
    request_metadata (list[str]): request metadata values.
    request_name (str): name of the request.
    request_target_tags (str): TODO
    resource_labels (list[str]): resource labels.
    resource_name (str): name of the resource.
    service_account_delegation (list[str]): service accounts delegation in the
        authentication.
    service_account_display_name (str): display name of the service account.
    service_account_key_name (str): service account key name used in
        authentication.
    service_name (str): name of the service.
    severity (str): log entry severity.
    source_images (list[str]): source images of disks attached to a compute
        engine instance.
    status_code (str): operation success or failure code.
    status_message (str); operation success or failure message.
    status_reasons (list[str]): reasons for operation failure.
    text_payload (str): text payload for logs not using a JSON or proto payload.
    user_agent (str): user agent used in the request.
  """

  DATA_TYPE = 'gcp:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(GCPLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caller_ip = None
    self.container = None
    self.dcsa_emails = None
    self.dcsa_scopes = None
    self.delegation_chain = None
    self.event_subtype = None
    self.event_type = None
    self.filename = None
    self.firewall_rules = None
    self.firewall_source_ranges = None
    self.gcloud_command_identity = None
    self.gcloud_command_partial = None
    self.log_name = None
    self.method_name = None
    self.message = None
    self.permissions = None
    self.policy_deltas = None
    self.principal_email = None
    self.principal_subject = None
    self.recorded_time = None
    self.request_account_identifier = None
    self.request_address = None
    self.request_description = None
    self.request_direction = None
    self.request_email = None
    self.request_member = None
    self.request_metadata = None
    self.request_name = None
    self.request_target_tags = None
    self.resource_labels = None
    self.resource_name = None
    self.service_account_delegation = None
    self.service_account_display_name = None
    self.service_account_key_name = None
    self.service_name = None
    self.severity = None
    self.source_images = None
    self.status_code = None
    self.status_message = None
    self.text_payload = None
    self.user_agent = None


class GCPLogJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Google Cloud (GCP) log files."""

  NAME = 'gcp_log'
  DATA_FORMAT = 'Google Cloud (GCP) log'

  _USER_AGENT_COMMAND_RE = re.compile(r'command/([^\s]+)')

  _USER_AGENT_INVOCATION_ID_RE = re.compile(r'invocation-id/([^\s]+)')

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

  def _ParseAuthenticationInfo(self, proto_payload, event_data):
    """Extracts information from `protoPayload.authenticationInfo`.

    Args:
      proto_payload (dict): JSON dictionary of the `protoPayload` value.
      event_data (GCPLogEventData): event data.
    """
    authentication_info = self._GetJSONValue(
        proto_payload, 'authenticationInfo')
    if not authentication_info:
      return

    principal_email = self._GetJSONValue(authentication_info, 'principalEmail')
    if principal_email:
      event_data.principal_email = principal_email

    principal_subject = self._GetJSONValue(
        authentication_info, 'principalSubject')
    if principal_subject:
      event_data.principal_subject = principal_subject

    service_account_key_name = self._GetJSONValue(
        authentication_info, 'serviceAccountKeyName')
    if service_account_key_name:
      event_data.service_account_key_name = service_account_key_name

    delegations = []

    delegation_info_list = self._GetJSONValue(
        authentication_info, 'serviceAccountDelegationInfo', [])
    for delegation_info in delegation_info_list:
      first_party_principal = self._GetJSONValue(
          delegation_info, 'firstPartyPrincipal', {})

      first_party_principal_email = self._GetJSONValue(first_party_principal,
          'principalEmail')
      if first_party_principal_email:
        delegations.append(first_party_principal_email)
      else:
        first_party_principal_subject = self._GetJSONValue(
            first_party_principal, 'principalSubject')
        if first_party_principal_subject:
          delegations.append(first_party_principal_subject)

    if delegations:
      event_data.service_account_delegation = delegations
      event_data.delegation_chain = '->'.join(delegations)

  def _ParseAuthorizationInfo(self, proto_payload, event_data):
    """Extracts information from `protoPayload.authorizationInfo`.

    Args:
      proto_payload (dict): JSON dictionary of the `protoPayload` value.
      event_data (GCPLogEventData): event data.
    """
    permissions = []

    authorization_info_list = self._GetJSONValue(
        proto_payload, 'authorizationInfo', [])
    for authorization_info in authorization_info_list:
      permission = self._GetJSONValue(authorization_info, 'permission')
      if permission:
        permissions.append(permission)

    if permissions:
      event_data.permissions = permissions

  def _ParseRequestMetadata(self, proto_payload, event_data):
    """Extracts information from `protoPayload.requestMetadata`.

    Args:
      proto_payload (dict): JSON dictionary of the `protoPayload` value.
      event_data (GCPLogEventData): event data.
    """
    request_metadata = self._GetJSONValue(proto_payload, 'requestMetadata')
    if not request_metadata:
      return

    event_data.caller_ip = self._GetJSONValue(request_metadata, 'callerIp')
    event_data.user_agent = self._GetJSONValue(
        request_metadata, 'callerSuppliedUserAgent')

    if event_data.user_agent:
      if 'command/' in event_data.user_agent:
        matches = self._USER_AGENT_COMMAND_RE.search(event_data.user_agent)
        if matches:
          command_string = matches.group(1).replace('.', ' ')
          event_data.gcloud_command_partial = command_string

      if 'invocation-id' in event_data.user_agent:
        matches = self._USER_AGENT_INVOCATION_ID_RE.search(
            event_data.user_agent)
        if matches:
          event_data.gcloud_command_identity = matches.group(1)

  def _ParseProtoPayloadStatus(self, proto_payload, event_data):
    """Extracts information from `protoPayload.status`.

    Args:
      proto_payload (dict): JSON dictionary of the `protoPayload` value.
      event_data (GCPLogEventData): event data.
    """
    status = self._GetJSONValue(proto_payload, 'status')
    if status:
      # Non empty `protoPayload.status` field could have empty
      # `protoPayload.status.code` field.
      #
      # Empty `code` and `message` fields indicate the operation was successful.

      event_data.status_code = str(self._GetJSONValue(status, 'code', ''))
      event_data.status_message = self._GetJSONValue(status, 'message')

      # `protoPayload.status.details[].reason` contains reason for an operation
      # failure.
      status_reasons = []

      for status_detail in self._GetJSONValue(status, 'details', []):
        status_reason = self._GetJSONValue(status_detail, 'reason')
        if status_reason:
          status_reasons.append(status_reason)

      if status_reasons:
        event_data.status_reasons = status_reasons

  def _ParseComputeInsertRequest(self, request, event_data):
    """Extracts compute.instances.insert information.

    Args:
      request (dict): JSON dictionary of the `protoPayload.request` field.
      event_data (GCPLogEventData): event data.
    """
    # source_images hold Google Cloud source disk path used in creating a GCE
    # instance.
    source_images = []

    for disk in self._GetJSONValue(request, 'disks', []):
      initialize_params = self._GetJSONValue(disk, 'initializeParams', {})

      source_image = self._GetJSONValue(initialize_params, 'sourceImage')
      if source_image:
        source_images.append(source_image)

    if source_images:
      event_data.source_images = source_images

    # Default compute service account aka dcsa
    dcsa_emails = []
    dcsa_scopes = []

    service_account_list = self._GetJSONValue(request, 'serviceAccounts', [])
    for service_account in service_account_list:
      email = self._GetJSONValue(service_account, 'email')
      if email:
        dcsa_emails.append(email)

      scopes = self._GetJSONValue(service_account, 'scopes')
      if scopes:
        dcsa_scopes.extend(scopes)

    if dcsa_emails:
      event_data.dcsa_emails = dcsa_emails

    if dcsa_scopes:
      event_data.dcsa_scopes = dcsa_scopes

  def _ParseComputeProtoPayload(self, proto_payload, event_data):
    """Extracts compute.googleapis.com information.

    Args:
      proto_payload (dict): JSON dictionary of the `protoPayload` value.
      event_data (GCPLogEventData): event data.
    """
    request = self._GetJSONValue(proto_payload, 'request')
    if not request:
      return

    request_type = self._GetJSONValue(request, '@type')
    if not request_type:
      return

    if request_type == 'type.googleapis.com/compute.instances.insert':
      self._ParseComputeInsertRequest(request, event_data)

  def _ParseProtoPayload(self, json_dict, event_data):
    """Extracts information from a protoPayload value.

    Args:
      json_dict (dict): JSON dictionary of the log record.
      event_data (GCPLogEventData): event data.
    """
    proto_payload = self._GetJSONValue(json_dict, 'protoPayload')
    if not proto_payload:
      return

    event_data.service_name = self._GetJSONValue(proto_payload, 'serviceName')
    event_data.resource_name = self._GetJSONValue(proto_payload, 'resourceName')

    method_name = self._GetJSONValue(proto_payload, 'methodName')
    if method_name and not event_data.event_subtype:
      event_data.event_subtype = method_name
      event_data.method_name = method_name

    self._ParseAuthenticationInfo(proto_payload, event_data)
    self._ParseAuthorizationInfo(proto_payload, event_data)
    self._ParseRequestMetadata(proto_payload, event_data)
    self._ParseProtoPayloadStatus(proto_payload, event_data)
    self._ParseProtoPayloadRequest(proto_payload, event_data)
    self._ParseProtoPayloadServiceData(proto_payload, event_data)

    if event_data.service_name == 'compute.googleapis.com':
      self._ParseComputeProtoPayload(proto_payload, event_data)

  def _ParseProtoPayloadRequest(self, proto_payload, event_data):
    """Extracts information from the request field of a protoPayload field.

    Args:
      proto_payload (dict): JSON dictionary of the `protoPayload` value.
      event_data (GCPLogEventData): event data.
    """
    request = self._GetJSONValue(proto_payload, 'request')
    if not request:
      return

    event_data.request_account_identifier = self._GetJSONValue(
        request, 'account_id')
    event_data.request_address = self._GetJSONValue(request, 'address')
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

  def _ParseProtoPayloadServiceData(self, proto_payload, event_data):
    """Extracts information from the serviceData in the protoPayload value.

    Args:
      proto_payload (dict): JSON dictionary of the `protoPayload` value.
      event_data (GCPLogEventData): event data.
    """
    service_data = self._GetJSONValue(proto_payload, 'serviceData')
    if not service_data:
      return

    policy_delta = self._GetJSONValue(service_data, 'policyDelta')
    if not policy_delta:
      return

    policy_deltas = []

    binding_deltas = self._GetJSONValue(
        policy_delta, 'bindingDeltas', default_value=[])
    for binding_delta_value in binding_deltas:
      action = self._GetJSONValue(binding_delta_value, 'action') or 'N/A'
      member = self._GetJSONValue(binding_delta_value, 'member') or 'N/A'
      role = self._GetJSONValue(binding_delta_value, 'role') or 'N/A'

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
