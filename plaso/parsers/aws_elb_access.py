# -*- coding: utf-8 -*-
"""Parser for AWS ELB access logs.

This parser is based on the log format documented at
https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html
"""
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


class AWSELBEventData(events.EventData):
  """AWS Elastic Load Balancer access log event data

  Attributes:
    type (str): The type of request or connection.
    resource_identifier (str): The resource ID of the load balancer.
    client_ip_address (str): The IP address of the requesting client.
    client_port (int): The port of the requesting client.
    target_ip_address (str): The IP address of the target that processed
        this request.
    target_port (int): The port of the target that processed this request.
    request_processing_time (str): The total duration from
        the time the load balancer received the request until the
        time it sent the request to a target.
    target_processing_time (str): The total duration from
        the time the load balancer sent the request to a target until
        the target started to send the response headers.
    response_processing_time (str): The total processing duration.
    target_status_code (int): The status code of the response from the target.
    received_bytes (int): The size of the request, in bytes, received from
        the client.
    sent_bytes (int): The size of the response, in bytes, sent to the client.
    user_agent (str): A User-Agent string.
    ssl_cipher (str): The SSL cipher of the HTTPS listener.
    ssl_protocol (str): The SSL protocol of the HTTPS listener.
    target_group_arn (str): The Amazon Resource Name (ARN) of the target group.
    trace_identifier (str): The contents of the X-Amzn-Trace-Id header.
    domain_name (str): The SNI domain provided by the
        client during the TLS handshake.
    chosen_cert_arn (str): The ARN of the certificate
        presented to the client.
    matched_rule_priority (int): The priority value of the rule that
        matched the request.
    request_creation_time (str): The time when the load balancer received the
        request from the client, in ISO 8601 format.
    actions_executed (str): The actions taken when processing the request.
    redirect_url (str): The URL of the redirect target.
    error_reason (str): The error reason code, enclosed in double quotes.
    target_port_list (str): A space-delimited list of IP addresses and ports
        for the targets that processed this request.
    target_status_code_list (str): A space-delimited list of status codes.
    classification (str): The classification for desync mitigation.
    classification_reason (str): The classification reason code.
  """

  DATA_TYPE = 'aws:elb:access'

  def __init__(self):
    """Initializes event data."""
    super(AWSELBEventData, self).__init__(data_type=self.DATA_TYPE)
    self.type = None
    self.resource_identifier = None
    self.client_ip_address = None
    self.client_port = None
    self.target_ip_address = None
    self.target_port = None
    self.request_processing_time = None
    self.target_processing_time = None
    self.response_processing_time = None
    self.elb_status_code = None
    self.target_status_code = None
    self.received_bytes = None
    self.sent_bytes = None
    self.request = None
    self.user_agent = None
    self.ssl_cipher = None
    self.ssl_protocol = None
    self.target_group_arn = None
    self.trace_identifier = None
    self.domain_name = None
    self.chosen_cert_arn = None
    self.matched_rule_priority = None
    self.request_creation_time = None
    self.actions_executed = None
    self.redirect_url = None
    self.error_reason = None
    self.target_port_list = None
    self.target_status_code_list = None
    self.classification = None
    self.classification_reason = None


class AWSELBParser(text_parser.PyparsingSingleLineTextParser):
  """Parses an AWS ELB access log file."""

  NAME = 'aws_elb_access'
  DATA_FORMAT = 'AWS ELB Access log file'
  MAX_LINE_LENGTH = 3000
  _ENCODING = 'utf-8'

  BLANK = pyparsing.Literal('"-"')

  _WORD = pyparsing.Word(pyparsing.printables) | BLANK

  _QUOTE_INTEGER = pyparsing.OneOrMore('"') \
      + text_parser.PyparsingConstants.INTEGER | BLANK

  _INTEGER = text_parser.PyparsingConstants.INTEGER | BLANK

  _FLOAT = pyparsing.Word(pyparsing.nums + '.')

  _PORT = pyparsing.Word(pyparsing.nums, max=6).setParseAction(
      text_parser.ConvertTokenToInteger) | BLANK

  _CLIENT_IP_ADDRESS_PORT = pyparsing.Group(
      text_parser.PyparsingConstants.IP_ADDRESS('client_ip_address') +
          pyparsing.Suppress(":") + _PORT('client_port') | BLANK)

  _TARGET_IP_ADDRESS_PORT = pyparsing.Group(
      text_parser.PyparsingConstants.IP_ADDRESS('target_ip_address') +
          pyparsing.Suppress(":") + _PORT('target_port') | BLANK)

  _DATE_TIME_ISOFORMAT_STRING = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=4) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('T') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums, exact=6) + pyparsing.Literal('Z'))

  # A log line is defined as in the AWS ELB documentation
  _LOG_LINE = (
      _WORD.setResultsName('type') +
      _DATE_TIME_ISOFORMAT_STRING.setResultsName('time') +
      _WORD.setResultsName('resource_identifier') +
      _CLIENT_IP_ADDRESS_PORT.setResultsName('client_ip_port') +
      _TARGET_IP_ADDRESS_PORT.setResultsName('target_ip_port') +
      _FLOAT.setResultsName('request_processing_time') +
      _FLOAT.setResultsName('target_processing_time') +
      _FLOAT.setResultsName('response_processing_time') +
      _INTEGER.setResultsName('elb_status_code') +
      _INTEGER.setResultsName('target_status_code') +
      _INTEGER.setResultsName('received_bytes') +
      _INTEGER.setResultsName('sent_bytes') +
      pyparsing.quotedString.setResultsName('request')
          .setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName('user_agent')
          .setParseAction(pyparsing.removeQuotes) +
      _WORD.setResultsName('ssl_cipher') +
      _WORD.setResultsName('ssl_protocol') +
      _WORD.setResultsName('target_group_arn') +
      _WORD.setResultsName('trace_identifier') +
      pyparsing.quotedString.setResultsName(
          'domain_name').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'chosen_cert_arn').setParseAction(pyparsing.removeQuotes) +
      _INTEGER.setResultsName('matched_rule_priority') +
      _DATE_TIME_ISOFORMAT_STRING.setResultsName('request_creation_time') +
      pyparsing.quotedString.setResultsName(
          'actions_executed').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'redirect_url').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'error_reason').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'target_port_list').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'target_status_code_list').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'classification').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'classification_reason').setParseAction(pyparsing.removeQuotes)
  )

  LINE_STRUCTURES = [('elb_accesslog', _LOG_LINE)]

  def _GetValueFromGroup(self, structure, name, key_name):
    """Retrieves a value from a Pyparsing.Group structure

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.
      key_name (str): key name to retrieve the value of.

    Returns:
      object: value for the specified key.
    """
    structure_value = self._GetValueFromStructure(structure, name)
    return structure_value.get(key_name)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure parsed from the log file.

    Raises:
      ParseError: when the structure type is unsupported.
    """
    if key != 'elb_accesslog':
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    time_elements_structure = structure.get('time')

    try:
      date_time = dfdatetime_time_elements.TimeElements()
      date_time.CopyFromStringISO8601(time_elements_structure)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_structure))
      return

    event_data = AWSELBEventData()
    event_data.type = self._GetValueFromStructure(structure, 'type')
    event_data.resource_identifier = self._GetValueFromStructure(
        structure, 'resource_identifier')
    event_data.client_ip_address = self._GetValueFromGroup(structure,
        'client_ip_port', 'client_ip_address')
    event_data.client_port = self._GetValueFromGroup(structure,
        'client_ip_port', 'client_port')
    event_data.target_ip_address = self._GetValueFromGroup(structure,
        'target_ip_port', 'target_ip_address')
    event_data.target_port = self._GetValueFromGroup(structure,
        'target_ip_port', 'target_port')
    event_data.request_processing_time = self._GetValueFromStructure(structure,
        'request_processing_time')
    event_data.target_processing_time = self._GetValueFromStructure(structure,
        'target_processing_time')
    event_data.response_processing_time = self._GetValueFromStructure(structure,
        'response_processing_time')
    event_data.elb_status_code = self._GetValueFromStructure(structure,
        'elb_status_code')
    event_data.target_status_code = self._GetValueFromStructure(structure,
        'target_status_code')
    event_data.received_bytes = self._GetValueFromStructure(structure,
        'received_bytes')
    event_data.sent_bytes = self._GetValueFromStructure(structure,
        'sent_bytes')
    event_data.request = self._GetValueFromStructure(structure,
        'request')
    event_data.user_agent = self._GetValueFromStructure(structure,
        'user_agent')
    event_data.ssl_cipher = self._GetValueFromStructure(structure,
        'ssl_cipher')
    event_data.ssl_protocol = self._GetValueFromStructure(structure,
        'ssl_protocol')
    event_data.target_group_arn = self._GetValueFromStructure(structure,
        'target_group_arn')
    event_data.trace_identifier = self._GetValueFromStructure(structure,
        'trace_identifier')
    event_data.domain_name = self._GetValueFromStructure(structure,
        'domain_name')
    event_data.chosen_cert_arn = self._GetValueFromStructure(structure,
        'chosen_cert_arn')
    event_data.matched_rule_priority = self._GetValueFromStructure(structure,
        'matched_rule_priority')
    event_data.request_creation_time = self._GetValueFromStructure(structure,
        'request_creation_time')
    event_data.actions_executed = self._GetValueFromStructure(structure,
        'actions_executed')
    event_data.redirect_url = self._GetValueFromStructure(structure,
        'redirect_url')
    event_data.error_reason = self._GetValueFromStructure(structure,
        'error_reason')
    event_data.target_port_list = self._GetValueFromStructure(structure,
        'target_port_list')
    event_data.target_status_code_list = self._GetValueFromStructure(structure,
        'target_status_code_list')
    event_data.classification = self._GetValueFromStructure(structure,
        'classification')
    event_data.classification_reason = self._GetValueFromStructure(structure,
        'classification_reason')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a valid AWS ELB access log

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line was successfully parsed.
    """
    try:
      structure = self._LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      structure = None

    return bool(structure)

manager.ParsersManager.RegisterParser(AWSELBParser)
