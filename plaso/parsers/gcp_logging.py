# -*- coding: utf-8 -*-
"""Parser for GCP cloud logging saved to a file."""

import json
from json.decoder import JSONDecodeError
import os

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import interface


class GCPLogEventData(events.EventData):
  """Google cloud logging event data.

  Attributes:
    severity (str): the log entry severity.
    user (str): the user principal performing the logged action.
    action (str): the logged GCP action.
    resource (str): the resource the action is being performed on.
    text_payload (str): the textPayload for logs not using a json or proto
      payload.
    log_name (str): the logName for the log entry.
  """

  DATA_TYPE = 'gcp:log:json'

  def __init__(self):
    """Initializes event data."""
    super(GCPLogEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.severity = None
    self.user = None
    self.action = None
    self.resource = None
    self.text_payload = None
    self.log_name = None

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

  def _ParseLogJSON(self, parser_mediator, file_json):
    """Extract events from Google Cloud Logging saved to a file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """

    for json_log_entry in file_json:

      time_string = json_log_entry.get('timestamp', None)
      if time_string is None:
        continue

      event_data = GCPLogEventData()
      event_attributes = {}

      resource = json_log_entry.get('resource')
      if resource:
        labels = resource.get('labels')
        if labels:
          for attribute, value in labels.items():
            plaso_attribute = 'resource_label_{0:s}'.format(attribute)
            event_attributes[plaso_attribute] = value

      severity = json_log_entry.get('severity')
      if severity:
        event_data.severity = severity

      log_name = json_log_entry.get('logName')
      if log_name:
        event_data.log_name = log_name

      json_payload = json_log_entry.get('jsonPayload', None)
      if json_payload:
        self._ParseJSONPayload(json_payload, event_attributes)

      proto_payload = json_log_entry.get('protoPayload', None)
      if proto_payload:
        self._ParseProtoPayload(proto_payload, event_attributes)

      text_payload = json_log_entry.get('textPayload', None)

      # TODO: jsonPayload can also contain arbitrary fields so should be
      # handled like textPayload if user, action or resource cannot be parsed.
      if text_payload:
        # Textpayload records can be anything, so we don't want to try to
        # format them.
        event_data.text_payload = text_payload
      else:
        # Ordered from least to most preferred value
        user_attributes = ['principalEmail', 'user']
        for attribute in user_attributes:
          if attribute in event_attributes:
            event_data.user = event_attributes[attribute]

        # Ordered from least to most preferred value
        action_attributes = ['methodName', 'event_subtype']
        for attribute in action_attributes:
          if attribute in event_attributes:
            event_data.action = event_attributes[attribute]

        # Ordered from least to most preferred value
        resource_attributes = ['resource_label_instance_id', 'resourceName']
        for attribute in resource_attributes:
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
      event_attributes (dict): a dict representing event attributes to be added
        to the event object.
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
      event_attributes (dict): a dict representing event attributes to be added
        to the event object.
    """
    request_attributes = [
        'name', 'description', 'direction', 'member', 'targetTags', 'email',
        'account_id'
    ]
    for attribute in request_attributes:
      if attribute in request:
        plaso_attribute = 'request_{0:s}'.format(attribute)
        event_attributes[plaso_attribute] = request[attribute]

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
    json_attributes = [
        'event_type', 'event_subtype', 'container', 'filename', 'message'
    ]
    for attribute in json_attributes:
      if attribute in json_payload:
        event_attributes[attribute] = json_payload[attribute]

    actor = json_payload.get('actor', {})
    if actor:
      if 'user' in actor:
        event_attributes['user'] = actor['user']

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses GCP logging saved to a file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
      ValueError: if the JSON file cannot be decoded.
    """
    if file_object.read(1) != b'[':
      raise errors.UnableToParseFile(
          'is not a valid JSON file, missing opening brace.')
    file_object.seek(0, os.SEEK_SET)
    try:
      file_json = json.loads(file_object.read().decode('utf-8'))
    except JSONDecodeError:
      raise errors.UnableToParseFile('could not decode json.')

    try:
      if 'logName' in file_json[0]:
        self._ParseLogJSON(parser_mediator, file_json)
    except ValueError as exception:
      if exception == 'No JSON object could be decoded':
        raise errors.UnableToParseFile(exception)
      raise


manager.ParsersManager.RegisterParser(GCPLogsParser)
