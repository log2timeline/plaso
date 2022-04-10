# -*- coding: utf-8 -*-
"""Parser for Azure application gateway access logging saved to a file."""

import json
import json.decoder as json_decoder
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
    instanceId (str): Application Gateway instance that served the request.
    clientIP (str): Originating IP for the request.
    clientPort (int): Originating port for the request.
    httpMethod (str): HTTP method used by the request.
    originalRequestUriWithArgs (str): This field contains the original request URL
    requestUri (str): URI of the received request.
    requestQuery (str): Server-Routed: Back-end pool instance that was sent the request. X-AzureApplicationGateway-LOG-ID: Correlation ID used for the request. It can be used to troubleshoot traffic issues on the back-end servers. SERVER-STATUS: HTTP response code that Application Gateway received from the back end.
    userAgent (str): User agent from the HTTP request header.
    httpStatus (int): HTTP status code returned to the client from Application Gateway.
    httpVersion (str): HTTP version of the request.
    receivedBytes (int): Size of packet received, in bytes.
    sentBytes (int): Size of packet sent, in bytes.
    clientResponseTime (int): Length of time (in seconds) that it takes for the first byte of a client request to be processed and the first byte sent in the response to the client.
    timeTaken (double): Length of time (in seconds) that it takes for the first byte of a client request to be processed and its last-byte sent in the response to the client. It's important to note that the Time-Taken field usually includes the time that the request and response packets are traveling over the network.
    WAFEvaluationTime (str): Length of time (in seconds) that it takes for the request to be processed by the WAF.
    WAFMode (str): Value can be either Detection or Prevention
    transactionId (str): Unique identifier to correlate the request received from the client
    sslEnabled (str): Whether communication to the back-end pools used TLS. Valid values are on and off.
    sslCipher (str): Cipher suite being used for TLS communication (if TLS is enabled).
    sslProtocol (str): SSL/TLS protocol being used (if TLS is enabled).
    sslClientVerify (str):
    sslClientCertificateFingerprint (str):
    sslClientCertificateIssuerName (str):
    serverRouted (str): The backend server that application gateway routes the request to.
    serverStatus (str): HTTP status code of the backend server.
    serverResponseLatency (str): Latency of the response (in seconds) from the backend server.
    originalHost (str): This field contains the original request host name
    host (str): Address listed in the host header of the request. If rewritten using header rewrite, this field contains the updated host name
  """

  DATA_TYPE = 'azure:applicationgatewayaccess:json'

  def __init__(self):
    """Initializes event data."""
    super(AzureApplicationGatewayAccessEventData, self).__init__(data_type=self.DATA_TYPE)

    self.instanceId = None
    self.clientIP = None
    self.clientPort = None
    self.httpMethod = None
    self.originalRequestUriWithArgs = None
    self.requestUri = None
    self.requestQuery = None
    self.userAgent = None
    self.httpStatus = None
    self.httpVersion = None
    self.receivedBytes = None
    self.sentBytes = None
    self.clientResponseTime = None
    self.timeTaken = None
    self.WAFEvaluationTime = None
    self.WAFMode = None
    self.transactionId = None
    self.sslEnabled = None
    self.sslCipher = None
    self.sslProtocol = None
    self.sslClientVerify = None
    self.sslClientCertificateFingerprint = None
    self.sslClientCertificateIssuerName = None
    self.serverRouted = None
    self.serverStatus = None
    self.serverResponseLatency = None
    self.originalHost = None
    self.host = None


class AzureApplicationGatewayAccessParser(interface.FileObjectParser):
  """Parser for Azure application gateway access logs saved in JSON-L format."""

  NAME = 'azure_applicationgatewayaccess'
  DATA_FORMAT = 'Azure Application Gateway Access Logging'

  _ENCODING = 'utf-8'

  def _ParseAzureApplicationGatewayAccess(self, parser_mediator, file_object):
    """Extract events from Azure application gateway access logging in JSON-L format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
        event_data.instanceId = properties_json_log_entry.get('instanceId')
        event_data.clientIP = properties_json_log_entry.get('clientIP')
        event_data.clientPort = properties_json_log_entry.get('clientPort')
        event_data.httpMethod = properties_json_log_entry.get('httpMethod')
        event_data.originalRequestUriWithArgs = properties_json_log_entry.get('originalRequestUriWithArgs')
        event_data.requestUri = properties_json_log_entry.get('requestUri')
        event_data.requestQuery = properties_json_log_entry.get('requestQuery')
        event_data.userAgent = properties_json_log_entry.get('userAgent')
        event_data.httpStatus = properties_json_log_entry.get('httpStatus')
        event_data.httpVersion = properties_json_log_entry.get('httpVersion')
        event_data.receivedBytes = properties_json_log_entry.get('receivedBytes')
        event_data.sentBytes = properties_json_log_entry.get('sentBytes')
        event_data.clientResponseTime = properties_json_log_entry.get('clientResponseTime')
        event_data.timeTaken = properties_json_log_entry.get('timeTaken')
        event_data.WAFEvaluationTime = properties_json_log_entry.get('WAFEvaluationTime')
        event_data.WAFMode = properties_json_log_entry.get('WAFMode')
        event_data.transactionId = properties_json_log_entry.get('transactionId')
        event_data.sslEnabled = properties_json_log_entry.get('sslEnabled')
        event_data.sslCipher = properties_json_log_entry.get('sslCipher')
        event_data.sslProtocol = properties_json_log_entry.get('sslProtocol')
        event_data.sslClientVerify = properties_json_log_entry.get('sslClientVerify')
        event_data.sslClientCertificateFingerprint = properties_json_log_entry.get('sslClientCertificateFingerprint')
        event_data.sslClientCertificateIssuerName = properties_json_log_entry.get('sslClientCertificateIssuerName')
        event_data.serverRouted = properties_json_log_entry.get('serverRouted')
        event_data.serverStatus = properties_json_log_entry.get('serverStatus')
        event_data.serverResponseLatency = properties_json_log_entry.get('serverResponseLatency')
        event_data.originalHost = properties_json_log_entry.get('originalHost')
        event_data.host = properties_json_log_entry.get('host')
      else:
        parser_mediator.ProduceExtractionWarning('unable to parse application gateway access log event: missing properties field')
        continue

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(time_string)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            f'Unable to parse time string: {time_string} with error: '
            f'{str(exception)}')
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses Azure Application Gateway Access logging saved in JSON-L format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Trivial JSON format check: first character must be an open brace.
    if file_object.read(1) != b'{':
      raise errors.WrongParser('is not a valid JSON file, missing opening brace.')
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    try:
      first_line = text_file_object.readline()
      first_line_json = json.loads(first_line)
    except json_decoder.JSONDecodeError:
      raise errors.WrongParser('could not decode json.')

    if not first_line_json:
      raise errors.WrongParser('no JSON found in file.')

    if not first_line_json.get('properties'):
      raise errors.WrongParser('no properties found in first line.')

    if first_line_json.get('operationName') != "ApplicationGatewayAccess":
      raise errors.WrongParser('operationName is not ApplicationGatewayAccess.')

    file_object.seek(0, os.SEEK_SET)
    self._ParseAzureApplicationGatewayAccess(parser_mediator, file_object)


manager.ParsersManager.RegisterParser(AzureApplicationGatewayAccessParser)
