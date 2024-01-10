# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Defender DeviceNetworkEvents table."""

import json
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.lib import errors
from plaso.parsers import csv_parser
from plaso.parsers.csv_plugins import interface
from plaso.parsers.csv_plugins import dah_events

class DefenderAHDeviceNetworkEventsPlugin(interface.CSVPlugin):
  """Parse DeviceNetworkEvents from CSV files."""  

  NAME = 'dah_devicenetworkevents'
  DATA_FORMAT = 'M365 Defender DeviceNetworkEvents table'

  # This constant is used for checking columns at CSV.
  REQUESTED_COLUMNS = {
    'Timestamp',
    'ActionType',
    'InitiatingProcessAccountDomain',
    'InitiatingProcessAccountName',
    'InitiatingProcessSHA1',
    'InitiatingProcessSHA256',
    'InitiatingProcessFileName',
    'InitiatingProcessId',
    'InitiatingProcessCommandLine',
    'InitiatingProcessCreationTime',
    'InitiatingProcessFolderPath',
    'InitiatingProcessParentId',
    'InitiatingProcessParentFileName',
    'InitiatingProcessParentCreationTime',
    'RemoteIP',
    'RemotePort',
    'RemoteUrl',
    'LocalIP',
    'LocalPort',
    'Protocol',
    'AdditionalFields'}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {
    'ConnectionFailed',
    'ConnectionFound',
    'ConnectionRequest',
    'ConnectionSuccess',
    'DnsConnectionInspected',
    'FtpConnectionInspected',
    'HttpConnectionInspected',
    'IcmpConnectionInspected',
    'InboundConnectionAccepted',
    'InboundInternetScanInspected',
    'ListeningConnectionCreated',
    'NetworkSignatureInspected',
    'NtlmAuthenticationInspected',
    'SmtpConnectionInspected',
    'SshConnectionInspected',
    'SslConnectionInspected'}

  _TIMESTAMP = pyparsing.pyparsing_common.iso8601_datetime

  def _ParseTimeStamp(self, date_time_string = None):
    """Parses date and time elements of a log line.

    Args:
      date_time_string (str): date and time elements of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.
    """
    self._TIMESTAMP.parseString(date_time_string) # pylint: disable=too-many-function-args

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
    date_time.CopyFromStringISO8601(time_string=date_time_string)
    return date_time

  def _ParseDnsQuery(self, additionalfields):
    """Parses DNS query from additionalfields.

    Args:
      additionalfields (str): Additional information about
        the event in JSON array format.

    Returns:
      str: DNS query.
    """
    result = ""

    try:
      if len(additionalfields) > 0 and "query" in additionalfields:
        addjson = json.loads(additionalfields)
        result = addjson['query']

    finally:
      pass

    return result

  def _ParseDirection(self, additionalfields):
    """Parses direction from additionalfields.

    Args:
      additionalfields (str): Additional information about
        the event in JSON array format.

    Returns:
      str: direction.
    """
    result = "-"

    try:
      if len(additionalfields) > 0 and "direction" in additionalfields:
        addjson = json.loads(additionalfields)
        tempresult = addjson['direction']

        if tempresult == "Out":
          result = "->"

        elif tempresult == "In":
          result = "<-"

    finally:
      pass

    return result

  def _ParseHost(self, additionalfields):
    """Parses direction from additionalfields.

    Args:
      additionalfields (str): Additional information about
        the event in JSON array format.

    Returns:
      str: Server hostname.
    """
    result = ""

    try:
      if len(additionalfields) > 0 and "host" in additionalfields:
        addjson = json.loads(additionalfields)
        result = addjson['host']

    finally:
      pass

    return result

  def _ParseServerName(self, additionalfields):
    """Parses direction from additionalfields.

    Args:
      additionalfields (str): Additional information about
        the event in JSON array format.

    Returns:
      str: Server hostname.
    """
    result = ""

    try:
      if len(additionalfields) > 0 and "server_name" in additionalfields:
        addjson = json.loads(additionalfields)
        result = addjson['server_name']

    finally:
      pass

    return result

  def _ParseConnectionFailed(self, parser_mediator, row):
    """Extracts ConnectionFailed action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHConnectionFailedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteurl = row['remoteurl']
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.initiatingprocesssha1 = row['initiatingprocesssha1']
    event_data.initiatingprocesssha256 = row['initiatingprocesssha256']
    event_data.initiatingprocessfilename = row['initiatingprocessfilename']
    event_data.initiatingprocessid = row['initiatingprocessid']
    event_data.initiatingprocesscommandline = row['initiatingprocesscommandline']
    event_data.initiatingprocesscreationtime = row['initiatingprocesscreationtime']
    event_data.initiatingprocessfolderpath = row['initiatingprocessfolderpath']
    event_data.initiatingprocessparentid = row['initiatingprocessparentid']
    event_data.initiatingprocessparentfilename = row['initiatingprocessparentfilename']
    event_data.initiatingprocessparentcreationtime = row['initiatingprocessparentcreationtime']

    parser_mediator.ProduceEventData(event_data)

  def _ParseConnectionFound(self, parser_mediator, row):
    """Extracts ConnectionFound action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHConnectionFoundEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteurl = row['remoteurl']
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.initiatingprocesssha1 = row['initiatingprocesssha1']
    event_data.initiatingprocesssha256 = row['initiatingprocesssha256']
    event_data.initiatingprocessfilename = row['initiatingprocessfilename']
    event_data.initiatingprocessid = row['initiatingprocessid']
    event_data.initiatingprocesscommandline = row['initiatingprocesscommandline']
    event_data.initiatingprocesscreationtime = row['initiatingprocesscreationtime']
    event_data.initiatingprocessfolderpath = row['initiatingprocessfolderpath']
    event_data.initiatingprocessparentid = row['initiatingprocessparentid']
    event_data.initiatingprocessparentfilename = row['initiatingprocessparentfilename']
    event_data.initiatingprocessparentcreationtime = row['initiatingprocessparentcreationtime']

    parser_mediator.ProduceEventData(event_data)

  def _ParseConnectionRequest(self, parser_mediator, row):
    """Extracts ConnectionRequest action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHConnectionRequestEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteurl = row['remoteurl']
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.initiatingprocesssha1 = row['initiatingprocesssha1']
    event_data.initiatingprocesssha256 = row['initiatingprocesssha256']
    event_data.initiatingprocessfilename = row['initiatingprocessfilename']
    event_data.initiatingprocessid = row['initiatingprocessid']
    event_data.initiatingprocesscommandline = row['initiatingprocesscommandline']
    event_data.initiatingprocesscreationtime = row['initiatingprocesscreationtime']
    event_data.initiatingprocessfolderpath = row['initiatingprocessfolderpath']
    event_data.initiatingprocessparentid = row['initiatingprocessparentid']
    event_data.initiatingprocessparentfilename = row['initiatingprocessparentfilename']
    event_data.initiatingprocessparentcreationtime = row['initiatingprocessparentcreationtime']

    parser_mediator.ProduceEventData(event_data)

  def _ParseConnectionSuccess(self, parser_mediator, row):
    """Extracts ConnectionSuccess action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHConnectionSuccessEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteurl = row['remoteurl']
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.initiatingprocesssha1 = row['initiatingprocesssha1']
    event_data.initiatingprocesssha256 = row['initiatingprocesssha256']
    event_data.initiatingprocessfilename = row['initiatingprocessfilename']
    event_data.initiatingprocessid = row['initiatingprocessid']
    event_data.initiatingprocesscommandline = row['initiatingprocesscommandline']
    event_data.initiatingprocesscreationtime = row['initiatingprocesscreationtime']
    event_data.initiatingprocessfolderpath = row['initiatingprocessfolderpath']
    event_data.initiatingprocessparentid = row['initiatingprocessparentid']
    event_data.initiatingprocessparentfilename = row['initiatingprocessparentfilename']
    event_data.initiatingprocessparentcreationtime = row['initiatingprocessparentcreationtime']

    parser_mediator.ProduceEventData(event_data)

  def _ParseDnsConnectionInspected(self, parser_mediator, row):
    """Extracts DnsConnectionInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHDnsConnectionInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.dnsquery = self._ParseDnsQuery(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseFtpConnectionInspected(self, parser_mediator, row):
    """Extracts FtpConnectionInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHFtpConnectionInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.direction = self._ParseDirection(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseHttpConnectionInspected(self, parser_mediator, row):
    """Extracts HttpConnectionInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHHttpConnectionInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.host = self._ParseHost(row['additionalfields'])
    event_data.direction = self._ParseDirection(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseIcmpConnectionInspected(self, parser_mediator, row):
    """Extracts IcmpConnectionInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHIcmpConnectionInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.localip = row['localip']
    event_data.protocol = row['protocol']
    event_data.direction = self._ParseDirection(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseInboundConnectionAccepted(self, parser_mediator, row):
    """Extracts InboundConnectionAccepted action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHInboundConnectionAcceptedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']

    parser_mediator.ProduceEventData(event_data)

  def _ParseInboundInternetScanInspected(self, parser_mediator, row):
    """Extracts InboundInternetScanInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHInboundInternetScanInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseListeningConnectionCreated(self, parser_mediator, row):
    """Extracts ListeningConnectionCreated action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHListeningConnectionCreatedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.initiatingprocesssha1 = row['initiatingprocesssha1']
    event_data.initiatingprocesssha256 = row['initiatingprocesssha256']
    event_data.initiatingprocessfilename = row['initiatingprocessfilename']
    event_data.initiatingprocessid = row['initiatingprocessid']
    event_data.initiatingprocesscommandline = row['initiatingprocesscommandline']
    event_data.initiatingprocesscreationtime = row['initiatingprocesscreationtime']
    event_data.initiatingprocessfolderpath = row['initiatingprocessfolderpath']
    event_data.initiatingprocessparentid = row['initiatingprocessparentid']
    event_data.initiatingprocessparentfilename = row['initiatingprocessparentfilename']
    event_data.initiatingprocessparentcreationtime = row['initiatingprocessparentcreationtime']

    parser_mediator.ProduceEventData(event_data)

  def _ParseNetworkSignatureInspected(self, parser_mediator, row):
    """Extracts NetworkSignatureInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHNetworkSignatureInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseNtlmAuthenticationInspected(self, parser_mediator, row):
    """Extracts NtlmAuthenticationInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHNtlmAuthenticationInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.direction = self._ParseDirection(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseSmtpConnectionInspected(self, parser_mediator, row):
    """Extracts SmtpConnectionInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHSmtpConnectionInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.direction = self._ParseDirection(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseSshConnectionInspected(self, parser_mediator, row):
    """Extracts SshConnectionInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHSshConnectionInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.direction = self._ParseDirection(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseSslConnectionInspected(self, parser_mediator, row):
    """Extracts SslConnectionInspected action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHSslConnectionInspectedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.protocol = row['protocol']
    event_data.server_name = self._ParseServerName(row['additionalfields'])
    event_data.direction = self._ParseDirection(row['additionalfields'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseCsvRow(self, parser_mediator, row):
    """Extracts events from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """

    try:
      tmp_row = dict((k.lower().strip(), v) for k,v in row.items())
      tmp_action = tmp_row['actiontype'].lower().strip()

      if tmp_action == 'connectionfailed':
        self._ParseConnectionFailed(parser_mediator, tmp_row)

      elif tmp_action == 'connectionfound':
        self._ParseConnectionFound(parser_mediator, tmp_row)

      elif tmp_action == 'connectionrequest':
        self._ParseConnectionRequest(parser_mediator, tmp_row)

      elif tmp_action == 'connectionsuccess':
        self._ParseConnectionSuccess(parser_mediator, tmp_row)

      elif tmp_action == 'dnsconnectioninspected':
        self._ParseDnsConnectionInspected(parser_mediator, tmp_row)

      elif tmp_action == 'ftpconnectioninspected':
        self._ParseFtpConnectionInspected(parser_mediator, tmp_row)

      elif tmp_action == 'httpconnectioninspected':
        self._ParseHttpConnectionInspected(parser_mediator, tmp_row)

      elif tmp_action == 'icmpconnectioninspected':
        self._ParseIcmpConnectionInspected(parser_mediator, tmp_row)

      elif tmp_action == 'inboundconnectionaccepted':
        self._ParseInboundConnectionAccepted(parser_mediator, tmp_row)

      elif tmp_action == 'inboundinternetscaninspected':
        self._ParseInboundInternetScanInspected(parser_mediator, tmp_row)

      elif tmp_action == 'listeningconnectioncreated':
        self._ParseListeningConnectionCreated(parser_mediator, tmp_row)

      elif tmp_action == 'networksignatureinspected':
        self._ParseNetworkSignatureInspected(parser_mediator, tmp_row)

      elif tmp_action == 'ntlmauthenticationinspected':
        self._ParseNtlmAuthenticationInspected(parser_mediator, tmp_row)

      elif tmp_action == 'smtpconnectioninspected':
        self._ParseSmtpConnectionInspected(parser_mediator, tmp_row)

      elif tmp_action == 'sshconnectioninspected':
        self._ParseSshConnectionInspected(parser_mediator, tmp_row)

      elif tmp_action == 'sslconnectioninspected':
        self._ParseSslConnectionInspected(parser_mediator, tmp_row)

    except pyparsing.ParseException as exception:
      raise errors.WrongParser(
        'unable to parse line with error: {0!s}'.format(
          exception))

csv_parser.CSVFileParser.RegisterPlugin(DefenderAHDeviceNetworkEventsPlugin)
