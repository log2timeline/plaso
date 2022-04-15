# -*- coding: utf-8 -*-
"""Parser for Azure application gateway access log."""

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


class AzureApplicationGatewayAccessEventData(events.EventData):
  """Azure application gateway access log event data.

  Attributes:
    client_ip (str): Client IP address of the request.
    client_port (int): Client TCP/UDP port for the request.
    client_response_time (int): Duration, in seconds, from the first byte of
        a client request to be processed up to the first byte sent as response
        to the client.
    host (str): Address listed in the host header of the request. If rewritten
        using header rewrite, contains the updated host name.
    http_method (str): HTTP method used by the request.
    http_status (int): HTTP status code returned to the client from application
        gateway.
    http_version (str): HTTP version of the request.
    instance_identifier (str): Application gateway instance that served
        the request.
    original_host (str): Original request host name.
    original_request_uri (str): Original request URL, including arguments.
    received_bytes (int): Size of packet received, in bytes.
    request_query (str): Server-Routed: Back-end pool instance that was sent
        the request. X-AzureApplicationGateway-LOG-ID: Correlation ID used for
        the request. It can be used to troubleshoot traffic issues on
        the back-end servers. SERVER-STATUS: HTTP response code that application
        gateway received from the back-end.
    request_uri (str): URI of the received request.
    sent_bytes (int): Size of packet sent, in bytes.
    server_response_latency (str): Latency of the response (in seconds) from
        the back-end server.
    server_routed (str): The back-end server that application gateway routes
        the request to.
    server_status (str): HTTP status code of the back-end server.
    ssl_cipher (str): Cipher suite being used for TLS communication.
    ssl_client_certificate_fingerprint (str): Fingerprint of the SSL client
        certificate.
    ssl_client_certificate_issuer_name (str): Name of the issuer of the SSL
        client certificate.
    ssl_client_verify (str): TODO.
    ssl_enabled (str): Whether communication to the back-end pools used TLS.
        Valid values are on and off.
    ssl_protocol (str): The SSL/TLS protocol used.
    time_taken (double): Duration, in seconds, that it takes for the first byte
        of a client request to be processed and its last-byte sent in
        the response to the client. It's important to note that the Time-Taken
        field usually includes the time that the request and response packets
        are traveling over the network.
    transaction_id (str): Unique identifier to correlate the request received
        from the client
    user_agent (str): User agent from the HTTP request header.
    waf_evaluation_time (str): Duration, in seconds, that it takes for
        the request to be processed by the WAF.
    waf_mode (str): Value can be either Detection or Prevention.
  """

  DATA_TYPE = 'azure:applicationgatewayaccess:entry'

  def __init__(self):
    """Initializes event data."""
    super(AzureApplicationGatewayAccessEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.client_ip = None
    self.client_port = None
    self.client_response_time = None
    self.host = None
    self.http_method = None
    self.http_status = None
    self.http_version = None
    self.instance_identifier = None
    self.original_host = None
    self.original_request_uri = None
    self.received_bytes = None
    self.request_query = None
    self.request_uri = None
    self.sent_bytes = None
    self.server_response_latency = None
    self.server_routed = None
    self.server_status = None
    self.ssl_cipher = None
    self.ssl_client_certificate_fingerprint = None
    self.ssl_client_certificate_issuer_name = None
    self.ssl_client_verify = None
    self.ssl_enabled = None
    self.ssl_protocol = None
    self.time_taken = None
    self.transaction_identifier = None
    self.user_agent = None
    self.waf_evaluation_time = None
    self.waf_mode = None


class AzureApplicationGatewayAccessParser(interface.FileObjectParser):
  """Parser for JSON-L Azure application gateway access log."""

  NAME = 'azure_application_gateway_access'
  DATA_FORMAT = 'Azure application gateway access log'

  _ENCODING = 'utf-8'

  _PROPERTIES = {
      'clientIP': 'client_ip',
      'clientPort': 'client_port',
      'clientResponseTime': 'client_response_time',
      'host': 'host',
      'httpMethod': 'http_method',
      'httpStatus': 'http_status',
      'httpVersion': 'http_version',
      'instanceId': 'instance_identifier',
      'originalHost': 'original_host',
      'originalRequestUriWithArgs': 'original_request_uri',
      'receivedBytes': 'received_bytes',
      'requestQuery': 'request_query',
      'requestUri': 'request_uri',
      'sentBytes': 'sent_bytes',
      'serverResponseLatency': 'server_response_latency',
      'serverRouted': 'server_routed',
      'serverStatus': 'server_status',
      'sslCipher': 'ssl_cipher',
      'sslClientCertificateFingerprint': 'ssl_client_certificate_fingerprint',
      'sslClientCertificateIssuerName': 'ssl_client_certificate_issuer_name',
      'sslClientVerify': 'ssl_client_verify',
      'sslEnabled': 'ssl_enabled',
      'sslProtocol': 'ssl_protocol',
      'timeTaken': 'time_taken',
      'transactionId': 'transaction_identifier',
      'userAgent': 'user_agent',
      'WAFEvaluationTime': 'waf_evaluation_time',
      'WAFMode': 'waf_mode'}

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

  def _ParseAzureApplicationGatewayAccess(self, parser_mediator, json_dict):
    """Extracts events from an Azure application gateway access log entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfVFS.
      json_dict (dict): JSON log entry dictionary.
    """
    timestamp = json_dict.get('timeStamp')
    if not timestamp:
      parser_mediator.ProduceExtractionWarning(
          'Timestamp value missing from application gateway access log event')
      return

    properties_json_dict = json_dict.get('properties')
    if not properties_json_dict:
      parser_mediator.ProduceExtractionWarning(
          'Properties value missing from application gateway access log event')
      return

    event_data = AzureApplicationGatewayAccessEventData()
    for json_name, attribute_name in self._PROPERTIES.items():
      attribute_value = self._GetJSONValue(properties_json_dict, json_name)
      setattr(event_data, attribute_name, attribute_value)

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(timestamp)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse timestamp value: {0:s} with error: {1!s}'.format(
              timestamp, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Azure application gateway access log file-object.

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
      raise errors.WrongParser('unable to decode JSON.')

    if not first_line_json:
      raise errors.WrongParser('missing JSON.')

    if not first_line_json.get('properties'):
      raise errors.WrongParser('no properties found in first line.')

    if first_line_json.get('operationName') != 'ApplicationGatewayAccess':
      raise errors.WrongParser(
          'operationName is not ApplicationGatewayAccess.')

    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    for line in text_file_object:
      json_log_entry = json.loads(line)
      self._ParseAzureApplicationGatewayAccess(parser_mediator, json_log_entry)


manager.ParsersManager.RegisterParser(AzureApplicationGatewayAccessParser)
