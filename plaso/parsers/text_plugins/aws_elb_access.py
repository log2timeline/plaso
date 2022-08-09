# -*- coding: utf-8 -*-
"""Text parser plugin for AWS ELB access logs.

The AWS documentation is not clear about the meaning of the "target_port_list"
field. The assumption is that it refers to a list of possible backend instances'
IP addresses that could receive the client's request. This parser stores the
"target_port_list" data in the "destination_list" attribute of an EventData
object.

Also see:
  https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html
  https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/access-log-collection.html
  https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-access-logs.html
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class AWSELBEventData(events.EventData):
  """AWS Elastic Load Balancer access log event data.

  Attributes:
    actions_executed (str): The actions taken when processing the request.
    chosen_cert_arn (str): The ARN of the certificate
        presented to the source.
    classification (str): The classification for desync mitigation.
    classification_reason (str): The classification reason code.
    destination_group_arn (str): The Amazon Resource Name (ARN) of the
        destination group.
    destination_ip_address (str): The IP address of the destination
        that processed this request.
    destination_list (str): A space-delimited list of IP addresses
        and ports for the destinations that processed this request.
    destination_port (int): The port of the destination that processed
        this request.
    destination_processing_time (str): The total duration from
        the time the load balancer sent the request to a destination until
        the destination started to send the response headers.
    destination_status_code (int): The status code of the response
        from the destination.
    destination_status_code_list (str): A space-delimited list of status codes.
    domain_name (str): The SNI domain provided by the
        source during the TLS handshake.
    error_reason (str): The error reason code, enclosed in
        double quotes.
    matched_rule_priority (int): The priority value of the rule that
        matched the request.
    received_bytes (int): The size of the request, in bytes, received from
        the source.
    redirect_url (str): The URL of the redirect destination.
    request_processing_time (str): The total duration from
        the time the load balancer received the request until the
        time it sent the request to a destination.
    request_type (str): The type of request or connection.
    resource_identifier (str): The resource ID of the load balancer.
    response_processing_time (str): The total processing duration.
    sent_bytes (int): The size of the response, in bytes, sent to the source.
    ssl_cipher (str): The SSL cipher of the HTTPS listener.
    ssl_protocol (str): The SSL protocol of the HTTPS listener.
    source_ip_address (str): The IP address of the requesting source.
    source_port (int): The port of the requesting source.
    trace_identifier (str): The contents of the X-Amzn-Trace-Id header.
    user_agent (str): A User-Agent string.
    version (str): The version of the log entry.
        (only for network load balancer logs)
    listener (str): The resource ID of the TLS listener for the connection.
        (only for network load balancer logs)
    connection_time (str): The total time for the connection to complete, from
        start to closure, in milliseconds.
        (only for network load balancer logs)
    handshake_time (str): The total time for the handshake to complete
        after the TCP connection is established, including client-side delays,
        in milliseconds. This time is included in the connection_time field.
        (only for network load balancer logs)
    incoming_tls_alert (str): The integer value of TLS alerts received by the
        load balancer from the client, if present.
        (only for network load balancer logs)
    chosen_cert_serial (str): Reserved for future use.
        This value is always set to -.
        (only for network load balancer logs)
    tls_named_group (str): Reserved for future use.
        This value is always set to -.
        (only for network load balancer logs)
    tls_cipher (str): The cipher suite negotiated with the client, in OpenSSL
        format. If TLS negotiation does not complete, this value is set to -.
        (only for network load balancer logs)
    tls_protocol_version (str): The TLS protocol negotiated with the client,
        in string format. If TLS negotiation does not complete,
        this value is set to -.
        (only for network load balancer logs)
    alpn_fe_protocol (str): The application protocol negotiated with the
        client, in string format. If no ALPN policy is configured in the TLS
        listener, no matching protocol is found, or no valid protocol list is
        sent, this value is set to -.
        (only for network load balancer logs)
    alpn_be_protocol (str): The application protocol negotiated with the
        target, in string format. If no ALPN policy is configured in the TLS
        listener, no matching protocol is found, or no valid protocol list is
        sent, this value is set to -.
        (only for network load balancer logs)
    alpn_client_preference_list (str): The value of the
        application_layer_protocol_negotiation extension in the client hello
        message. This value is URL-encoded. Each protocol is enclosed in double
        quotes and protocols are separated by a comma. If no ALPN policy is
        configured in the TLS listener, no valid client hello message is sent,
        or the extension is not present, this value is set to -. The string is
        truncated if it is longer than 256 bytes.
        (only for network load balancer logs)
  """

  DATA_TYPE = 'aws:elb:access'

  def __init__(self):
    """Initializes event data."""
    super(AWSELBEventData, self).__init__(data_type=self.DATA_TYPE)
    self.actions_executed = None
    self.chosen_cert_arn = None
    self.classification = None
    self.classification_reason = None
    self.destination_group_arn = None
    self.destination_ip_address = None
    self.destination_list = None
    self.destination_port = None
    self.destination_processing_time = None
    self.destination_status_code_list = None
    self.destination_status_code = None
    self.domain_name = None
    self.elb_status_code = None
    self.error_reason = None
    self.matched_rule_priority = None
    self.received_bytes = None
    self.redirect_url = None
    self.request = None
    self.request_processing_time = None
    self.request_type = None
    self.resource_identifier = None
    self.response_processing_time = None
    self.sent_bytes = None
    self.source_ip_address = None
    self.source_port = None
    self.ssl_cipher = None
    self.ssl_protocol = None
    self.trace_identifier = None
    self.user_agent = None
    self.version = None
    self.listener = None
    self.connection_time = None
    self.handshake_time = None
    self.incoming_tls_alert = None
    self.chosen_cert_serial = None
    self.tls_named_group = None
    self.tls_cipher = None
    self.tls_protocol_version = None
    self.alpn_fe_protocol = None
    self.alpn_be_protocol = None
    self.alpn_client_preference_list = None


class AWSELBTextPlugin(interface.TextPlugin):
  """Text parser plugin for AWS ELB access log files."""

  NAME = 'aws_elb_access'
  DATA_FORMAT = 'AWS ELB Access log file'

  ENCODING = 'utf-8'

  _MAXIMUM_LINE_LENGTH = 3000

  _BLANK = pyparsing.Literal('"-"') | pyparsing.Literal('-')

  _WORD = pyparsing.Word(pyparsing.printables) | _BLANK

  _INTEGER = text_parser.PyparsingConstants.INTEGER | _BLANK

  _INTEGER_NEGATIVE = pyparsing.Word('-', pyparsing.nums) | _INTEGER

  _FLOAT = pyparsing.Word(pyparsing.nums + '.')

  _PORT = pyparsing.Word(pyparsing.nums, max=6).setParseAction(
      text_parser.ConvertTokenToInteger) | _BLANK

  _CLIENT_IP_ADDRESS_PORT = pyparsing.Group(
      text_parser.PyparsingConstants.IP_ADDRESS('source_ip_address') +
          pyparsing.Suppress(':') + _PORT('source_port') | _BLANK)

  _DESTINATION_IP_ADDRESS_PORT = pyparsing.Group(
      text_parser.PyparsingConstants.IP_ADDRESS('destination_ip_address') +
          pyparsing.Suppress(':') + _PORT('destination_port') | _BLANK)

  _DATE_TIME_ISOFORMAT_STRING = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=4) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('T') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums, exact=6) + pyparsing.Literal('Z'))

  _DATE_TIME_ISOFORMAT_STRING_WITHOUT_TIMEZONE = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=4) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('T') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2))

  # A log line is defined as in the AWS ELB documentation
  _LOG_LINE_APPLICATION = (
      _WORD.setResultsName('request_type') +
      _DATE_TIME_ISOFORMAT_STRING.setResultsName('time') +
      _WORD.setResultsName('resource_identifier') +
      _CLIENT_IP_ADDRESS_PORT.setResultsName('source_ip_port') +
      _DESTINATION_IP_ADDRESS_PORT.setResultsName('destination_ip_port') +
      _FLOAT.setResultsName('request_processing_time') +
      _FLOAT.setResultsName('destination_processing_time') +
      _FLOAT.setResultsName('response_processing_time') +
      _INTEGER.setResultsName('elb_status_code') +
      _INTEGER.setResultsName('destination_status_code') +
      _INTEGER_NEGATIVE.setResultsName('received_bytes') +
      _INTEGER_NEGATIVE.setResultsName('sent_bytes') +
      pyparsing.quotedString.setResultsName('request')
          .setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName('user_agent')
          .setParseAction(pyparsing.removeQuotes) +
      _WORD.setResultsName('ssl_cipher') +
      _WORD.setResultsName('ssl_protocol') +
      _WORD.setResultsName('destination_group_arn') +
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
          'destination_list').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'destination_status_code_list').setParseAction(
              pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'classification').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'classification_reason').setParseAction(pyparsing.removeQuotes))

  _LOG_LINE_NETWORK = (
      _WORD.setResultsName('request_type') +
      _WORD.setResultsName('version') +
      _DATE_TIME_ISOFORMAT_STRING_WITHOUT_TIMEZONE.setResultsName('time') +
      _WORD.setResultsName('resource_identifier') +
      _WORD.setResultsName('listener') +
      _CLIENT_IP_ADDRESS_PORT.setResultsName('source_ip_port') +
      _DESTINATION_IP_ADDRESS_PORT.setResultsName('destination_ip_port') +
      _INTEGER.setResultsName('connection_time') +
      _INTEGER.setResultsName('handshake_time') +
      _INTEGER_NEGATIVE.setResultsName('received_bytes') +
      _INTEGER_NEGATIVE.setResultsName('sent_bytes') +
      _WORD.setResultsName('incoming_tls_alert') +
      _WORD.setResultsName('chosen_cert_arn') +
      _WORD.setResultsName('chosen_cert_serial') +
      _WORD.setResultsName('tls_cipher') +
      _WORD.setResultsName('tls_protocol_version') +
      _WORD.setResultsName('tls_named_group') +
      _WORD.setResultsName('domain_name') +
      _WORD.setResultsName('alpn_fe_protocol') +
      _WORD.setResultsName('alpn_be_protocol') +
      (pyparsing.quotedString.setResultsName('alpn_client_preference_list')
          .setParseAction(pyparsing.removeQuotes) | pyparsing.Literal('-')) | pyparsing.Literal('-')
  )

  _LOG_LINE_CLASSIC = (
      _DATE_TIME_ISOFORMAT_STRING.setResultsName('time') +
      _WORD.setResultsName('resource_identifier') +
      _CLIENT_IP_ADDRESS_PORT.setResultsName('source_ip_port') +
      _DESTINATION_IP_ADDRESS_PORT.setResultsName('destination_ip_port') +
      _FLOAT.setResultsName('request_processing_time') +
      _FLOAT.setResultsName('destination_processing_time') +
      _FLOAT.setResultsName('response_processing_time') +
      _INTEGER.setResultsName('elb_status_code') +
      _INTEGER.setResultsName('destination_status_code') +
      _INTEGER_NEGATIVE.setResultsName('received_bytes') +
      _INTEGER_NEGATIVE.setResultsName('sent_bytes') +
      pyparsing.quotedString.setResultsName('request').setParseAction(
          pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName('user_agent').setParseAction(
          pyparsing.removeQuotes) +
      _WORD.setResultsName('ssl_cipher') +
      _WORD.setResultsName('ssl_protocol'))

  _LINE_STRUCTURES = [
      ('elb_application_accesslog', _LOG_LINE_APPLICATION),
      ('elb_network_accesslog', _LOG_LINE_NETWORK),
      ('elb_classic_accesslog', _LOG_LINE_CLASSIC)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _GetValueFromGroup(self, structure, name, key_name):
    """Retrieves a value from a Pyparsing.Group structure.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.
      key_name (str): key name to retrieve the value of.

    Returns:
      object: value for the specified key or None if not available.
    """
    structure_value = self._GetValueFromStructure(structure, name)
    if structure_value is None:
      return None

    return structure_value.get(key_name)

  def _GetDateTime(self, parser_mediator, time_structure):
    """Returns a dfdatetime object from a timestamp.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      time_structure (str): a timestamp string of the event.

    Returns:
      TimeElements: Time elements contain separate values for year, month,
          day of month, hours, minutes and seconds.
    """
    try:
      date_time = dfdatetime_time_elements.TimeElements()
      date_time.CopyFromStringISO8601(time_structure)

      return date_time

    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_structure))

    return None

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    time_response_sent = structure.get('time')
    time_request_received = structure.get('request_creation_time')

    date_time_response_sent = self._GetDateTime(
        parser_mediator, time_response_sent)

    if time_request_received is not None:
        date_time_request_received = self._GetDateTime(
            parser_mediator, time_request_received)

    if date_time_response_sent is None:
      return

    event_data = AWSELBEventData()
    event_data.request_type = self._GetValueFromStructure(
        structure, 'request_type')
    event_data.resource_identifier = self._GetValueFromStructure(
        structure, 'resource_identifier')
    event_data.source_ip_address = self._GetValueFromGroup(
        structure, 'source_ip_port', 'source_ip_address')
    event_data.source_port = self._GetValueFromGroup(
        structure, 'source_ip_port', 'source_port')
    event_data.destination_ip_address = self._GetValueFromGroup(
        structure, 'destination_ip_port', 'destination_ip_address')
    event_data.destination_port = self._GetValueFromGroup(
        structure, 'destination_ip_port', 'destination_port')
    event_data.request_processing_time = self._GetValueFromStructure(
        structure, 'request_processing_time')
    event_data.destination_processing_time = self._GetValueFromStructure(
        structure, 'destination_processing_time')
    event_data.response_processing_time = self._GetValueFromStructure(
        structure, 'response_processing_time')
    event_data.elb_status_code = self._GetValueFromStructure(
        structure, 'elb_status_code')
    event_data.destination_status_code = self._GetValueFromStructure(
        structure, 'destination_status_code')
    event_data.received_bytes = self._GetValueFromStructure(
        structure, 'received_bytes')
    event_data.sent_bytes = self._GetValueFromStructure(
        structure, 'sent_bytes')
    event_data.request = self._GetValueFromStructure(
        structure, 'request')
    event_data.user_agent = self._GetValueFromStructure(
        structure, 'user_agent')
    event_data.ssl_cipher = self._GetValueFromStructure(
        structure, 'ssl_cipher')
    event_data.ssl_protocol = self._GetValueFromStructure(
        structure, 'ssl_protocol')
    event_data.destination_group_arn = self._GetValueFromStructure(
        structure, 'destination_group_arn')
    event_data.trace_identifier = self._GetValueFromStructure(
        structure, 'trace_identifier')
    event_data.domain_name = self._GetValueFromStructure(
        structure, 'domain_name')
    event_data.chosen_cert_arn = self._GetValueFromStructure(
        structure, 'chosen_cert_arn')
    event_data.matched_rule_priority = self._GetValueFromStructure(
        structure, 'matched_rule_priority')
    event_data.actions_executed = self._GetValueFromStructure(
        structure, 'actions_executed')
    event_data.redirect_url = self._GetValueFromStructure(
        structure, 'redirect_url')
    event_data.error_reason = self._GetValueFromStructure(
        structure, 'error_reason')
    event_data.destination_status_code_list = self._GetValueFromStructure(
        structure, 'destination_status_code_list')
    event_data.classification = self._GetValueFromStructure(
        structure, 'classification')
    event_data.classification_reason = self._GetValueFromStructure(
        structure, 'classification_reason')
    destination_list = self._GetValueFromStructure(
        structure, 'destination_list')
    if destination_list is not None:
        event_data.destination_list = destination_list.split()
    event_data.version = self._GetValueFromStructure(
        structure, 'version')
    event_data.listener = self._GetValueFromStructure(
        structure, 'listener')
    event_data.connection_time = self._GetValueFromStructure(
        structure, 'connection_time')
    event_data.handshake_time = self._GetValueFromStructure(
        structure, 'handshake_time')
    event_data.incoming_tls_alert = self._GetValueFromStructure(
        structure, 'incoming_tls_alert')
    event_data.chosen_cert_serial = self._GetValueFromStructure(
        structure, 'chosen_cert_serial')
    event_data.tls_named_group = self._GetValueFromStructure(
        structure, 'tls_named_group')
    event_data.tls_cipher = self._GetValueFromStructure(
        structure, 'tls_cipher')
    event_data.tls_protocol_version = self._GetValueFromStructure(
        structure, 'tls_protocol_version')
    event_data.alpn_fe_protocol = self._GetValueFromStructure(
        structure, 'alpn_fe_protocol')
    event_data.alpn_be_protocol = self._GetValueFromStructure(
        structure, 'alpn_be_protocol')
    event_data.alpn_client_preference_list = self._GetValueFromStructure(
        structure, 'alpn_client_preference_list')

    elb_response_sent_event = time_events.DateTimeValuesEvent(
        date_time_response_sent,
        definitions.TIME_DESCRIPTION_AWS_ELB_RESPONSE_SENT)
    parser_mediator.ProduceEventWithEventData(
        elb_response_sent_event, event_data)

    if key == 'elb_application_accesslog' and date_time_request_received is not None:
        elb_request_received_event = time_events.DateTimeValuesEvent(
            date_time_request_received,
            definitions.TIME_DESCRIPTION_AWS_ELB_REQUEST_RECEIVED)
        parser_mediator.ProduceEventWithEventData(
        elb_request_received_event, event_data)

  def CheckRequiredFormat(self, parser_mediator, text_file_object):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      line = self._ReadLineOfText(text_file_object)
    except UnicodeDecodeError:
      return False

    _, _, parsed_structure = self._GetMatchingLineStructure(line)
    return bool(parsed_structure)


text_parser.PyparsingSingleLineTextParser.RegisterPlugin(AWSELBTextPlugin)
