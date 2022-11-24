# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Azure application gateway access log files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


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
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
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

  DATA_TYPE = 'azure:application_gateway_access:entry'

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
    self.recorded_time = None
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


class AzureApplicationGatewayAccessLogJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Azure application gateway access log files."""

  NAME = 'azure_application_gateway_access_log'
  DATA_FORMAT = 'Azure Application Gateway access log'

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses an Azure application gateway access log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    properties_json_dict = self._GetJSONValue(
        json_dict, 'properties', default_value={})

    event_data = AzureApplicationGatewayAccessEventData()
    event_data.client_ip = self._GetJSONValue(
        properties_json_dict, 'clientIP')
    event_data.client_port = self._GetJSONValue(
        properties_json_dict, 'clientPort')
    event_data.client_response_time = self._GetJSONValue(
        properties_json_dict, 'clientResponseTime')
    event_data.host = self._GetJSONValue(
        properties_json_dict, 'host')
    event_data.http_method = self._GetJSONValue(
        properties_json_dict, 'httpMethod')
    event_data.http_status = self._GetJSONValue(
        properties_json_dict, 'httpStatus')
    event_data.http_version = self._GetJSONValue(
        properties_json_dict, 'httpVersion')
    event_data.instance_identifier = self._GetJSONValue(
        properties_json_dict, 'instanceId')
    event_data.original_host = self._GetJSONValue(
        properties_json_dict, 'originalHost')
    event_data.original_request_uri = self._GetJSONValue(
        properties_json_dict, 'originalRequestUriWithArgs')
    event_data.received_bytes = self._GetJSONValue(
        properties_json_dict, 'receivedBytes')
    event_data.recorded_time = self._ParseISO8601DateTimeString(
        parser_mediator, json_dict, 'timeStamp')
    event_data.request_query = self._GetJSONValue(
        properties_json_dict, 'requestQuery')
    event_data.request_uri = self._GetJSONValue(
        properties_json_dict, 'requestUri')
    event_data.sent_bytes = self._GetJSONValue(
        properties_json_dict, 'sentBytes')
    event_data.server_response_latency = self._GetJSONValue(
        properties_json_dict, 'serverResponseLatency')
    event_data.server_routed = self._GetJSONValue(
        properties_json_dict, 'serverRouted')
    event_data.server_status = self._GetJSONValue(
        properties_json_dict, 'serverStatus')
    event_data.ssl_cipher = self._GetJSONValue(
        properties_json_dict, 'sslCipher')
    event_data.ssl_client_certificate_fingerprint = self._GetJSONValue(
        properties_json_dict, 'sslClientCertificateFingerprint')
    event_data.ssl_client_certificate_issuer_name = self._GetJSONValue(
        properties_json_dict, 'sslClientCertificateIssuerName')
    event_data.ssl_client_verify = self._GetJSONValue(
        properties_json_dict, 'sslClientVerify')
    event_data.ssl_enabled = self._GetJSONValue(
        properties_json_dict, 'sslEnabled')
    event_data.ssl_protocol = self._GetJSONValue(
        properties_json_dict, 'sslProtocol')
    event_data.time_taken = self._GetJSONValue(
        properties_json_dict, 'timeTaken')
    event_data.transaction_identifier = self._GetJSONValue(
        properties_json_dict, 'transactionId')
    event_data.user_agent = self._GetJSONValue(
        properties_json_dict, 'userAgent')
    event_data.waf_evaluation_time = self._GetJSONValue(
        properties_json_dict, 'WAFEvaluationTime')
    event_data.waf_mode = self._GetJSONValue(
        properties_json_dict, 'WAFMode')

    parser_mediator.ProduceEventData(event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    operation_name = self._GetJSONValue(json_dict, 'operationName')
    properties = self._GetJSONValue(json_dict, 'properties')
    iso8601_string = self._GetJSONValue(json_dict, 'timeStamp')

    if (None in (operation_name, properties, iso8601_string) or
        operation_name != 'ApplicationGatewayAccess'):
      return False

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

    try:
      date_time.CopyFromStringISO8601(iso8601_string)
    except ValueError:
      return False

    return True


jsonl_parser.JSONLParser.RegisterPlugin(
    AzureApplicationGatewayAccessLogJSONLPlugin)
