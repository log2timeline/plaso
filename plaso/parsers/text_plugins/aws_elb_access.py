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
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class AWSELBEventData(events.EventData):
  """AWS Elastic Load Balancer access log event data.

  Attributes:
    actions_executed (str): The actions taken when processing the request.
    alpn_back_end_protocol (str): The application protocol negotiated with
        the target, in string format. If no ALPN policy is configured in
        the TLS listener, no matching protocol is found, or no valid protocol
        list is sent, this value is set to -.
        (only for network load balancer logs)
    alpn_client_preference_list (str): The value of the
        application_layer_protocol_negotiation extension in the client hello
        message. This value is URL-encoded. Each protocol is enclosed in double
        quotes and protocols are separated by a comma. If no ALPN policy is
        configured in the TLS listener, no valid client hello message is sent,
        or the extension is not present, this value is set to -. The string is
        truncated if it is longer than 256 bytes.
        (only for network load balancer logs)
    alpn_front_end_protocol (str): The application protocol negotiated with
        the client, in string format. If no ALPN policy is configured in
        the TLS listener, no matching protocol is found, or no valid protocol
        list is sent, this value is set to -.
        (only for network load balancer logs)
    chosen_cert_arn (str): The ARN of the certificate
        presented to the source.
    chosen_cert_serial (str): Reserved for future use.
        This value is always set to -.
        (only for network load balancer logs)
    classification (str): The classification for desync mitigation.
    classification_reason (str): The classification reason code.
    connection_duration (str): duration of the connection to complete, from
        start to closure, in milliseconds.
        (only for network load balancer logs)
    destination_group_arn (str): The Amazon Resource Name (ARN) of the
        destination group.
    destination_ip_address (str): The IP address of the destination
        that processed this request.
    destination_list (str): A space-delimited list of IP addresses
        and ports for the destinations that processed this request.
    destination_port (int): The port of the destination that processed
        this request.
    destination_processing_duration (str): duration from the time the load
        balancer sent the request to a destination until the destination
        started to send the response headers.
    destination_status_code (int): The status code of the response
        from the destination.
    destination_status_code_list (str): A space-delimited list of status codes.
    domain_name (str): The SNI domain provided by the
        source during the TLS handshake.
    error_reason (str): The error reason code, enclosed in
        double quotes.
    handshake_duration (str): duration of the handshake to complete after
        the TCP connection is established, including client-side delays,
        in milliseconds. This time is included in the connection_duration field.
        (only for network load balancer logs)
    incoming_tls_alert (str): The integer value of TLS alerts received by the
        load balancer from the client, if present.
        (only for network load balancer logs)
    listener (str): The resource ID of the TLS listener for the connection.
        (only for network load balancer logs)
    matched_rule_priority (int): The priority value of the rule that
        matched the request.
    received_bytes (int): The size of the request, in bytes, received from
        the source.
    redirect_url (str): The URL of the redirect destination.
    request_processing_duration (str): total duration from the time the load
        balancer received the request until the time it sent the request to
        a destination.
    request_time (dfdatetime.DateTimeValues): date and time a request
        was sent.
    request_type (str): The type of request or connection.
    resource_identifier (str): The resource ID of the load balancer.
    response_processing_duration (str): duration of processing a response.
    response_time (dfdatetime.DateTimeValues): date and time a response
        was sent.
    sent_bytes (int): The size of the response, in bytes, sent to the source.
    ssl_cipher (str): The SSL cipher of the HTTPS listener.
    ssl_protocol (str): The SSL protocol of the HTTPS listener.
    source_ip_address (str): The IP address of the requesting source.
    source_port (int): The port of the requesting source.
    tls_cipher (str): The cipher suite negotiated with the client, in OpenSSL
        format. If TLS negotiation does not complete, this value is set to -.
        (only for network load balancer logs)
    tls_named_group (str): Reserved for future use.
        This value is always set to -.
        (only for network load balancer logs)
    tls_protocol_version (str): The TLS protocol negotiated with the client,
        in string format. If TLS negotiation does not complete,
        this value is set to -.
        (only for network load balancer logs)
    trace_identifier (str): The contents of the X-Amzn-Trace-Id header.
    user_agent (str): A User-Agent string.
    version (str): The version of the log entry.
        (only for network load balancer logs)
  """

  DATA_TYPE = 'aws:elb:access'

  def __init__(self):
    """Initializes event data."""
    super(AWSELBEventData, self).__init__(data_type=self.DATA_TYPE)
    self.actions_executed = None
    self.alpn_back_end_protocol = None
    self.alpn_client_preference_list = None
    self.alpn_front_end_protocol = None
    self.chosen_cert_arn = None
    self.chosen_cert_serial = None
    self.classification = None
    self.classification_reason = None
    self.connection_duration = None
    self.destination_group_arn = None
    self.destination_ip_address = None
    self.destination_list = None
    self.destination_port = None
    self.destination_processing_duration = None
    self.destination_status_code = None
    self.destination_status_code_list = None
    self.domain_name = None
    self.elb_status_code = None
    self.error_reason = None
    self.handshake_duration = None
    self.incoming_tls_alert = None
    self.listener = None
    self.matched_rule_priority = None
    self.received_bytes = None
    self.redirect_url = None
    self.request = None
    self.request_processing_duration = None
    self.request_time = None
    self.request_type = None
    self.resource_identifier = None
    self.response_processing_duration = None
    self.response_time = None
    self.sent_bytes = None
    self.source_ip_address = None
    self.source_port = None
    self.ssl_cipher = None
    self.ssl_protocol = None
    self.tls_cipher = None
    self.tls_named_group = None
    self.tls_protocol_version = None
    self.trace_identifier = None
    self.user_agent = None
    self.version = None


class AWSELBTextPlugin(interface.TextPlugin):
  """Text parser plugin for AWS ELB access log files."""

  NAME = 'aws_elb_access'
  DATA_FORMAT = 'AWS ELB Access log file'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _BLANK = pyparsing.Literal('"-"') | pyparsing.Literal('-')

  _WORD = pyparsing.Word(pyparsing.printables) | _BLANK

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _UNSIGNED_INTEGER = _INTEGER | _BLANK

  _SIGNED_INTEGER = pyparsing.Word('-', pyparsing.nums) | _UNSIGNED_INTEGER

  _FLOATING_POINT = (
      pyparsing.Word(pyparsing.nums + '.') | pyparsing.Literal('-1'))

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address)

  _PORT = pyparsing.Word(pyparsing.nums, max=6).setParseAction(
      lambda tokens: int(tokens[0], 10)) | _BLANK

  _SOURCE_IP_ADDRESS_AND_PORT = pyparsing.Group(
      _IP_ADDRESS.setResultsName('source_ip_address') +
      pyparsing.Suppress(':') + _PORT.setResultsName('source_port') | _BLANK)

  _DESTINATION_IP_ADDRESS_AND_PORT = pyparsing.Group(
      _IP_ADDRESS.setResultsName('destination_ip_address') +
      pyparsing.Suppress(':') + _PORT.setResultsName('destination_port') |
      _BLANK)

  _DATE_TIME_ISOFORMAT_STRING = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('T') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') +
      _SIX_DIGITS + pyparsing.Suppress('Z'))

  _DATE_TIME_ISOFORMAT_STRING_WITHOUT_TIMEZONE = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('T') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS)

  _REQUEST = pyparsing.quotedString.setResultsName(
      'request').setParseAction(pyparsing.removeQuotes)

  _USER_AGENT = pyparsing.quotedString.setResultsName(
      'user_agent').setParseAction(pyparsing.removeQuotes)

  _ALPN_CLIENT_PREFERENCE_LIST = pyparsing.quotedString.setResultsName(
      'alpn_client_preference_list').setParseAction(pyparsing.removeQuotes)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # A log line is defined as in the AWS ELB documentation
  _APPLICATION_LOG_LINE = (
      _WORD.setResultsName('request_type') +
      _DATE_TIME_ISOFORMAT_STRING.setResultsName('response_time') +
      _WORD.setResultsName('resource_identifier') +
      _SOURCE_IP_ADDRESS_AND_PORT.setResultsName('source_ip_port') +
      _DESTINATION_IP_ADDRESS_AND_PORT.setResultsName('destination_ip_port') +
      _FLOATING_POINT.setResultsName('request_processing_duration') +
      _FLOATING_POINT.setResultsName('destination_processing_duration') +
      _FLOATING_POINT.setResultsName('response_processing_duration') +
      _UNSIGNED_INTEGER.setResultsName('elb_status_code') +
      _UNSIGNED_INTEGER.setResultsName('destination_status_code') +
      _UNSIGNED_INTEGER.setResultsName('received_bytes') +
      _UNSIGNED_INTEGER.setResultsName('sent_bytes') +
      _REQUEST +
      _USER_AGENT +
      _WORD.setResultsName('ssl_cipher') +
      _WORD.setResultsName('ssl_protocol') +
      _WORD.setResultsName('destination_group_arn') +
      pyparsing.quotedString.setResultsName(
          'trace_identifier').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'domain_name').setParseAction(pyparsing.removeQuotes) +
      pyparsing.quotedString.setResultsName(
          'chosen_cert_arn').setParseAction(pyparsing.removeQuotes) +
      _SIGNED_INTEGER.setResultsName('matched_rule_priority') +
      _DATE_TIME_ISOFORMAT_STRING.setResultsName('request_time') +
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
          'classification_reason').setParseAction(pyparsing.removeQuotes) +
      _END_OF_LINE)

  _NETWORK_LOG_LINE = (
      _WORD.setResultsName('request_type') +
      _WORD.setResultsName('version') +
      _DATE_TIME_ISOFORMAT_STRING_WITHOUT_TIMEZONE.setResultsName(
          'response_time') +
      _WORD.setResultsName('resource_identifier') +
      _WORD.setResultsName('listener') +
      _SOURCE_IP_ADDRESS_AND_PORT.setResultsName('source_ip_port') +
      _DESTINATION_IP_ADDRESS_AND_PORT.setResultsName('destination_ip_port') +
      _UNSIGNED_INTEGER.setResultsName('connection_duration') +
      _UNSIGNED_INTEGER.setResultsName('handshake_duration') +
      _UNSIGNED_INTEGER.setResultsName('received_bytes') +
      _UNSIGNED_INTEGER.setResultsName('sent_bytes') +
      _WORD.setResultsName('incoming_tls_alert') +
      _WORD.setResultsName('chosen_cert_arn') +
      _WORD.setResultsName('chosen_cert_serial') +
      _WORD.setResultsName('tls_cipher') +
      _WORD.setResultsName('tls_protocol_version') +
      _WORD.setResultsName('tls_named_group') +
      _WORD.setResultsName('domain_name') +
      _WORD.setResultsName('alpn_front_end_protocol') +
      _WORD.setResultsName('alpn_back_end_protocol') +
      (_ALPN_CLIENT_PREFERENCE_LIST | pyparsing.Literal('-')) +
      _END_OF_LINE)

  _CLASSIC_LOG_LINE = (
      _DATE_TIME_ISOFORMAT_STRING.setResultsName('response_time') +
      _WORD.setResultsName('resource_identifier') +
      _SOURCE_IP_ADDRESS_AND_PORT.setResultsName('source_ip_port') +
      _DESTINATION_IP_ADDRESS_AND_PORT.setResultsName('destination_ip_port') +
      _FLOATING_POINT.setResultsName('request_processing_duration') +
      _FLOATING_POINT.setResultsName('destination_processing_duration') +
      _FLOATING_POINT.setResultsName('response_processing_duration') +
      _UNSIGNED_INTEGER.setResultsName('elb_status_code') +
      _UNSIGNED_INTEGER.setResultsName('destination_status_code') +
      _SIGNED_INTEGER.setResultsName('received_bytes') +
      _SIGNED_INTEGER.setResultsName('sent_bytes') +
      _REQUEST +
      _USER_AGENT +
      _WORD.setResultsName('ssl_cipher') +
      _WORD.setResultsName('ssl_protocol') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('elb_application_accesslog', _APPLICATION_LOG_LINE),
      ('elb_classic_accesslog', _CLASSIC_LOG_LINE),
      ('elb_network_accesslog', _NETWORK_LOG_LINE)]

  VERIFICATION_GRAMMAR = (
      _APPLICATION_LOG_LINE ^ _CLASSIC_LOG_LINE ^ _NETWORK_LOG_LINE)

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

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: if the structure cannot be parsed.
    """
    destination_list = self._GetValueFromStructure(
        structure, 'destination_list')
    if destination_list:
      destination_list = destination_list.split()

    chosen_cert_serial = self._GetValueFromStructure(
        structure, 'chosen_cert_serial')
    if chosen_cert_serial == '-':
      chosen_cert_serial = None

    classification = self._GetValueFromStructure(structure, 'classification')
    if classification == '-':
      classification = None

    classification_reason = self._GetValueFromStructure(
        structure, 'classification_reason')
    if classification_reason == '-':
      classification_reason = None

    destination_status_code = self._GetValueFromStructure(
        structure, 'destination_status_code')
    if destination_status_code == '-':
      destination_status_code = None

    elb_status_code = self._GetValueFromStructure(structure, 'elb_status_code')
    if elb_status_code == '-':
      elb_status_code = None

    error_reason = self._GetValueFromStructure(structure, 'error_reason')
    if error_reason == '-':
      error_reason = None

    incoming_tls_alert = self._GetValueFromStructure(
        structure, 'incoming_tls_alert')
    if incoming_tls_alert == '-':
      incoming_tls_alert = None

    redirect_url = self._GetValueFromStructure(structure, 'redirect_url')
    if redirect_url == '-':
      redirect_url = None

    ssl_cipher = self._GetValueFromStructure(structure, 'ssl_cipher')
    if ssl_cipher == '-':
      ssl_cipher = None

    ssl_protocol = self._GetValueFromStructure(structure, 'ssl_protocol')
    if ssl_protocol == '-':
      ssl_protocol = None

    tls_named_group = self._GetValueFromStructure(structure, 'tls_named_group')
    if tls_named_group == '-':
      tls_named_group = None

    user_agent = self._GetValueFromStructure(structure, 'user_agent')
    if user_agent == '-':
      user_agent = None

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
    event_data.request_processing_duration = self._GetValueFromStructure(
        structure, 'request_processing_duration')
    event_data.destination_processing_duration = self._GetValueFromStructure(
        structure, 'destination_processing_duration')
    event_data.response_processing_duration = self._GetValueFromStructure(
        structure, 'response_processing_duration')
    event_data.elb_status_code = elb_status_code
    event_data.destination_status_code = destination_status_code
    event_data.received_bytes = self._GetValueFromStructure(
        structure, 'received_bytes')
    event_data.sent_bytes = self._GetValueFromStructure(structure, 'sent_bytes')
    event_data.request = self._GetValueFromStructure(structure, 'request')
    event_data.user_agent = user_agent
    event_data.ssl_cipher = ssl_cipher
    event_data.ssl_protocol = ssl_protocol
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
    event_data.redirect_url = redirect_url
    event_data.error_reason = error_reason
    event_data.destination_status_code_list = self._GetValueFromStructure(
        structure, 'destination_status_code_list')
    event_data.classification = classification
    event_data.classification_reason = classification_reason
    event_data.destination_list = destination_list
    event_data.version = self._GetValueFromStructure(structure, 'version')
    event_data.listener = self._GetValueFromStructure(structure, 'listener')
    event_data.connection_duration = self._GetValueFromStructure(
        structure, 'connection_duration')
    event_data.handshake_duration = self._GetValueFromStructure(
        structure, 'handshake_duration')
    event_data.incoming_tls_alert = incoming_tls_alert
    event_data.chosen_cert_serial = chosen_cert_serial
    event_data.tls_named_group = tls_named_group
    event_data.tls_cipher = self._GetValueFromStructure(structure, 'tls_cipher')
    event_data.tls_protocol_version = self._GetValueFromStructure(
        structure, 'tls_protocol_version')
    event_data.alpn_front_end_protocol = self._GetValueFromStructure(
        structure, 'alpn_front_end_protocol')
    event_data.alpn_back_end_protocol = self._GetValueFromStructure(
        structure, 'alpn_back_end_protocol')
    event_data.alpn_client_preference_list = self._GetValueFromStructure(
        structure, 'alpn_client_preference_list')

    response_time_structure = self._GetValueFromStructure(
        structure, 'response_time')
    if response_time_structure:
      event_data.response_time = self._ParseTimeElements(
          response_time_structure)

    request_time_structure = structure.get('request_time')
    if request_time_structure:
      event_data.request_time = self._ParseTimeElements(request_time_structure)

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
      # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
      # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
      # overriding __getattr__ with a function that returns an empty string
      # when named token does not exist.

      if len(time_elements_structure) == 7:
        year, month, day_of_month, hours, minutes, seconds, microseconds = (
            time_elements_structure)

        time_elements_tuple = (
            year, month, day_of_month, hours, minutes, seconds, microseconds)
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
            time_elements_tuple=time_elements_tuple)
      else:
        year, month, day_of_month, hours, minutes, seconds = (
            time_elements_structure)

        time_elements_tuple = (
            year, month, day_of_month, hours, minutes, seconds)
        date_time = dfdatetime_time_elements.TimeElements(
            time_elements_tuple=time_elements_tuple)
        date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'response_time')

    if time_elements_structure:
      try:
        self._ParseTimeElements(time_elements_structure)
      except errors.ParseError:
        return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'request_time')

    if time_elements_structure:
      try:
        self._ParseTimeElements(time_elements_structure)
      except errors.ParseError:
        return False

    return True


text_parser.TextLogParser.RegisterPlugin(AWSELBTextPlugin)
