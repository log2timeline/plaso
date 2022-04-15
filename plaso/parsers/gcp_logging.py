# -*- coding: utf-8 -*-
"""Parser for Google Cloud (GCP) log files."""

import json
import os

from json import decoder as json_decoder

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements
from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import interface


class GCPLogEventData(events.EventData):
  """Google Cloud (GCP) logging event data.

  Attributes:
    action (str): GCP action.
    log_name (str): name of the log entry.
    resource (str): resource the action is being performed on.
    severity (str): log entry severity.
    text_payload (str): text payload for logs not using a JSON or proto
        payload.
    user (str): user principal performing the logged action.
  """

  DATA_TYPE = 'gcp:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(GCPLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.log_name = None
    self.resource = None
    self.severity = None
    self.text_payload = None
    self.user = None

  # TODO: remove this, event data should be predefined.
  def AddEventAttributes(self, event_attributes):
    """Add extra event attributes parsed from GCP logs.

    Extra attributes vary across log types and so must be dynamically added
    depending on presence in the log entry.

    Args: event_attributes (dict): a dict of extra attributes to add to the
      event.
    """
    for key,value in event_attributes.items():
      setattr(self, key, value)


class GCPLogsParser(interface.FileObjectParser):
  """Parser for GCP logging in json format.

  Parsing logic taken from DFTimewolf's GCPLoggingTimesketch module for
  consistency https://github.com/log2timeline/dftimewolf
  """

  NAME = 'gcplogging'
  DATA_FORMAT = 'Google Cloud Logging'

  _ENCODING = 'utf-8'

  _JSON_PAYLOAD_ATTRIBUTES = [
      'container',
      'event_subtype',
      'event_type',
      'filename',
      'message']

  _PROTO_PAYLOAD_ATTRIBUTES = [
      'account_id'
      'description',
      'direction',
      'email',
      'member',
      'name',
      'targetTags']

  # Ordered from least to most preferred value.
  _ACTION_ATTRIBUTES = ['methodName', 'event_subtype']
  _RESROUCE_ATTRIBUTES = ['resource_label_instance_id', 'resourceName']
  _USER_ATTRIBUTES = ['principalEmail', 'user']

  def _GetJSONValue(self, json_dict, name):
    """Retrieves a value from a JSON dict.

    Args:
      json_dict (dict): JSON dictionary.
      name (str): name of the value to retrieve.

    Returns:
      object: value of the JSON log entry or None if not set.
    """
    json_value = json_dict.get(name)
    if json_value == '':
      json_value = None
    return json_value

  def _ParseGCPLog(self, parser_mediator, json_dict):
    """Extracts events from a GCP log entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON log entry dictionary.
    """
    time_string = json_dict.get('timestamp')
    if not time_string:
      parser_mediator.ProduceExtractionWarning(
          'Timestamp value missing from GCP log event')
      return

    event_data = GCPLogEventData()
    event_attributes = {}

    resource_json = json_dict.get('resource')
    if resource_json:
      labels_json = resource_json.get('labels')
      if labels_json:
        for attribute, value in labels_json.items():
          plaso_attribute = 'resource_label_{0:s}'.format(attribute)
          event_attributes[plaso_attribute] = value

    event_data.severity = self._GetJSONValue(json_dict, 'severity')
    event_data.log_name = self._GetJSONValue(json_dict, 'logName')

    json_payload = json_dict.get('jsonPayload')
    if json_payload:
      self._ParseJSONPayload(json_payload, event_attributes)

    proto_payload = json_dict.get('protoPayload')
    if proto_payload:
      self._ParseProtoPayload(proto_payload, event_attributes)

    # TODO: jsonPayload can also contain arbitrary fields so should be
    # handled like textPayload if user, action or resource cannot be parsed.
    text_payload = json_dict.get('textPayload')
    if text_payload:
      # Textpayload records can be anything, so we don't want to try to
      # format them.
      event_data.text_payload = text_payload
    else:
      for attribute in self._USER_ATTRIBUTES:
        if attribute in event_attributes:
          event_data.user = event_attributes[attribute]

      for attribute in self._ACTION_ATTRIBUTES:
        if attribute in event_attributes:
          event_data.action = event_attributes[attribute]

      for attribute in self._RESROUCE_ATTRIBUTES:
        if attribute in event_attributes:
          event_data.resource = event_attributes[attribute]

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(time_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning((
          'Unable to parse written time string: {0:s} with error: '
          '{1!s}').format(time_string, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    event_data.AddEventAttributes(event_attributes)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseProtoPayload(self, proto_payload, event_attributes):
    """Extracts information from a protoPayload field in a GCP log.

    protoPayload is set for all cloud audit events.

    Args:
      proto_payload (dict): the contents of a GCP protoPayload field.
      event_attributes (dict[str, object]): event attributes to be added to
          the event data.
    """
    authentication_info = proto_payload.get('authenticationInfo', None)
    if authentication_info:
      principal_email = authentication_info.get('principalEmail', None)
      if principal_email:
        event_attributes['principalEmail'] = principal_email

    request_metadata = proto_payload.get('requestMetadata', None)
    if request_metadata:
      for attribute, value in request_metadata.items():
        plaso_attribute = 'requestMetadata_{0:s}'.format(attribute)
        event_attributes[plaso_attribute] = str(value)

    proto_attributes = ['serviceName', 'methodName', 'resourceName']
    for attribute in proto_attributes:
      value = proto_payload.get(attribute, None)
      if value:
        event_attributes[attribute] = value

    request = proto_payload.get('request', None)
    if request:
      self._ParseProtoPayloadRequest(request, event_attributes)

    service_data = proto_payload.get('serviceData', None)
    if service_data:
      policy_delta = service_data.get('policyDelta', None)
      if policy_delta:
        binding_deltas = policy_delta.get('bindingDeltas', [])
        if binding_deltas:
          policy_deltas = []
          for bd in binding_deltas:
            policy_deltas.append(
                '{0:s} {1:s} with role {2:s}'.format(
                    bd.get('action', ''), bd.get('member', ''),
                    bd.get('role', '')))
          event_attributes['policyDelta']  = ', '.join(policy_deltas)

  def _ParseProtoPayloadRequest(self, request, event_attributes):
    """Extracts information from the request field of a protoPayload field.

    Args:
      request (dict): the contents of a GCP request field from a
          protoPayload field.
      event_attributes (dict[str, object]): event attributes to be added to
          the event data.
    """
    for attribute_name in self._PROTO_PAYLOAD_ATTRIBUTES:
      attribute_value = request.get(attribute_name)
      if attribute_value:
        plaso_attribute = 'request_{0:s}'.format(attribute_name)
        event_attributes[plaso_attribute] = attribute_value

    # Firewall specific attributes.
    if 'sourceRanges' in request:
      source_ranges = ', '.join(request['sourceRanges'])
      event_attributes['source_ranges'] = source_ranges

    if 'alloweds' in request:
      for allowed in request['alloweds']:
        attribute_name = 'allowed_{0:s}_ports'.format(allowed['IPProtocol'])
        if 'ports' in allowed:
          event_attributes[attribute_name] = allowed['ports']
        else:
          event_attributes[attribute_name] = 'all'

    if 'denieds' in request:
      for denied in request['denieds']:
        attribute_name = 'denied_{0:s}_ports'.format(denied['IPProtocol'])
        if 'ports' in denied:
          event_attributes[attribute_name] = denied['ports']
        else:
          event_attributes[attribute_name] = 'all'

    # Service account specific attributes
    if 'service_account' in request:
      service_account_name = request['service_account'].get('display_name')
      event_attributes['service_account_display_name'] = service_account_name

  def _ParseJSONPayload(self, json_payload, event_attributes):
    """Extracts information from a json_payload.

    Args:
      json_payload (dict): the contents of a GCP jsonPayload field.
      event_attributes (dict): a dict representing event attributes to be added
        to the event object.
    """
    for attribute in self._JSON_PAYLOAD_ATTRIBUTES:
      if attribute in json_payload:
        event_attributes[attribute] = json_payload[attribute]

    actor_json = json_payload.get('actor')
    if actor_json:
      if 'user' in actor_json:
        event_attributes['user'] = actor_json['user']

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a GCP log file-object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Trivial JSON format check: first character must be an open brace.
    if file_object.read(1) != b'{':
      raise errors.WrongParser(
          'is not a valid JSON file, missing opening brace.')

    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    try:
      first_line = text_file_object.readline()
      first_line_json = json.loads(first_line)
    except json_decoder.JSONDecodeError:
      raise errors.WrongParser('could not decode JSON.')

    if 'logName' not in first_line_json:
      raise errors.WrongParser('no logName field, not a GCP log entry.')

    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    for line in text_file_object:
      json_log_entry = json.loads(line)
      self._ParseGCPLog(parser_mediator, json_log_entry)


manager.ParsersManager.RegisterParser(GCPLogsParser)
