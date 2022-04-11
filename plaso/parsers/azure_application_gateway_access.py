# -*- coding: utf-8 -*-
"""Parser for Azure application gateway access logging saved to a file."""

import json
from json.decoder import JSONDecodeError
import os

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
    instance_id (str): Application Gateway instance that served the request
    client_ip (str): Originating IP for the request.
    client_port (int): Originating port for the request.
    http_method (str): HTTP method used by the request.
    original_request_uri_with_args (str): This field contains the original
        request URL
    request_uri (str): URI of the received request.
    request_query (str): Server-Routed: Back-end pool instance that was sent
        the request.
        X-AzureApplicationGateway-LOG-ID: Correlation ID used for the request.
        It can be used to troubleshoot traffic issues on the back-end servers.
        SERVER-STATUS: HTTP response code that Application Gateway received from
        the back end.
    user_agent (str): User agent from the HTTP request header.
    http_status (int): HTTP status code returned to the client from
        Application Gateway.
    http_version (str): HTTP version of the request.
    received_bytes (int): Size of packet received, in bytes.
    sent_bytes (int): Size of packet sent, in bytes.
    client_response_time (int): Length of time (in seconds) that it takes for
        the first byte of a client request to be processed and the first byte
        sent in the response to the client.
    time_taken (double): Length of time (in seconds) that it takes for the
        first byte of a client request to be processed and its last-byte
        sent in the response to the client. It's important to note that the
        Time-Taken field usually includes the time that the request and
        response packets are traveling over the network.
    waf_evaluation_time (str): Length of time (in seconds) that it takes for
        the request to be processed by the WAF.
    waf_mode (str): Value can be either Detection or Prevention
    transaction_id (str): Unique identifier to correlate the request received
        from the client
    ssl_enabled (str): Whether communication to the back-end pools used TLS.
        Valid values are on and off.
    ssl_cipher (str): Cipher suite being used for TLS communication
        (if TLS is enabled).
    ssl_protocol (str): SSL/TLS protocol being used (if TLS is enabled).
    ssl_client_verify (str):
    ssl_client_certificate_fingerprint (str):
    ssl_client_certificate_issuer_name (str):
    server_routed (str): The backend server that application gateway routes
        the request to.
    server_status (str): HTTP status code of the backend server.
    server_response_latency (str): Latency of the response (in seconds)
        from the backend server.
    original_host (str): This field contains the original request host name
    host (str): Address listed in the host header of the request. If rewritten
        using header rewrite, this field contains the updated host name
  """

  DATA_TYPE = 'azure:applicationgatewayaccess:json'

  def __init__(self):
    """Initializes event data."""
    super(AzureApplicationGatewayAccessEventData, self).__init__(
        data_type=self.DATA_TYPE
    )

    self.instance_id = None
    self.client_ip = None
    self.client_port = None
    self.http_method = None
    self.original_request_uri_with_args = None
    self.request_uri = None
    self.request_query = None
    self.user_agent = None
    self.http_status = None
    self.http_version = None
    self.received_bytes = None
    self.sent_bytes = None
    self.client_response_time = None
    self.time_taken = None
    self.waf_evaluation_time = None
    self.waf_mode = None
    self.transaction_id = None
    self.ssl_enabled = None
    self.ssl_cipher = None
    self.ssl_protocol = None
    self.ssl_client_verify = None
    self.ssl_client_certificate_fingerprint = None
    self.ssl_client_certificate_issuer_name = None
    self.server_routed = None
    self.server_status = None
    self.server_response_latency = None
    self.original_host = None
    self.host = None


class AzureApplicationGatewayAccessParser(interface.FileObjectParser):
  """Parser for Azure application gateway access logs in JSON-L format."""

  NAME = 'azure_applicationgatewayaccess'
  DATA_FORMAT = 'Azure Application Gateway Access Logging'

  _ENCODING = 'utf-8'

  def _ParseAzureApplicationGatewayAccess(self, parser_mediator, file_object):
    """ Extract events from Azure application gateway access logging.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    text_file_object = text_file.TextFile(file_object)

    for line in text_file_object:
      json_log_entry = json.loads(line)

      time_string = json_log_entry.get('timeStamp')
      if not time_string:
        continue

      if 'properties' in json_log_entry:
        properties_json_log_entry = json_log_entry.get('properties')

        event_data = AzureApplicationGatewayAccessEventData()
        event_data.instance_id = properties_json_log_entry.get('instanceId')
        event_data.client_ip = properties_json_log_entry.get('clientIP')
        event_data.client_port = properties_json_log_entry.get('clientPort')
        event_data.http_method = properties_json_log_entry.get('httpMethod')
        event_data.original_request_uri_with_args = (
            properties_json_log_entry.get('originalRequestUriWithArgs')
        )
        event_data.request_uri = properties_json_log_entry.get('requestUri')
        event_data.request_query = properties_json_log_entry.get('requestQuery')
        event_data.user_agent = properties_json_log_entry.get('userAgent')
        event_data.http_status = properties_json_log_entry.get('httpStatus')
        event_data.http_version = properties_json_log_entry.get('httpVersion')
        event_data.received_bytes = properties_json_log_entry.get(
            'receivedBytes'
        )
        event_data.sent_bytes = properties_json_log_entry.get('sentBytes')
        event_data.client_response_time = properties_json_log_entry.get(
            'clientResponseTime'
        )
        event_data.time_taken = properties_json_log_entry.get('timeTaken')
        event_data.waf_evaluation_time = properties_json_log_entry.get(
            'WAFEvaluationTime'
        )
        event_data.waf_mode = properties_json_log_entry.get('WAFMode')
        event_data.transaction_id = properties_json_log_entry.get(
            'transactionId'
        )
        event_data.ssl_enabled = properties_json_log_entry.get('sslEnabled')
        event_data.ssl_cipher = properties_json_log_entry.get('sslCipher')
        event_data.ssl_protocol = properties_json_log_entry.get('sslProtocol')
        event_data.ssl_client_verify = properties_json_log_entry.get(
            'sslClientVerify'
        )
        event_data.ssl_client_certificate_fingerprint = (
            properties_json_log_entry.get('sslClientCertificateFingerprint')
        )
        event_data.ssl_client_certificate_issuer_name = (
            properties_json_log_entry.get('sslClientCertificateIssuerName')
        )
        event_data.server_routed = properties_json_log_entry.get('serverRouted')
        event_data.server_status = properties_json_log_entry.get('serverStatus')
        event_data.server_response_latency = properties_json_log_entry.get(
            'serverResponseLatency'
        )
        event_data.original_host = properties_json_log_entry.get('originalHost')
        event_data.host = properties_json_log_entry.get('host')
      else:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse application gateway access log event:'
            'missing properties field'
        )
        continue

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(time_string)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            f'Unable to parse time string: {time_string} with error: '
            f'{str(exception)}'
        )
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED
      )
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses Azure Application Gateway Access logging in JSON-L format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Trivial JSON format check: first character must be an open brace.
    if file_object.read(1) != b'{':
      raise errors.WrongParser(
          'is not a valid JSON file, missing opening brace.'
      )
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    try:
      first_line = text_file_object.readline()
      first_line_json = json.loads(first_line)
    except JSONDecodeError:
      raise errors.WrongParser('could not decode json.')

    if not first_line_json:
      raise errors.WrongParser('no JSON found in file.')

    if not first_line_json.get('properties'):
      raise errors.WrongParser('no properties found in first line.')

    if first_line_json.get('operationName') != "ApplicationGatewayAccess":
      raise errors.WrongParser(
          'operationName is not ApplicationGatewayAccess.'
      )

    file_object.seek(0, os.SEEK_SET)
    self._ParseAzureApplicationGatewayAccess(parser_mediator, file_object)


manager.ParsersManager.RegisterParser(AzureApplicationGatewayAccessParser)
