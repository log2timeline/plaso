# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Defender DeviceLogonEvents table."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.lib import errors
from plaso.parsers import csv_parser
from plaso.parsers.csv_plugins import interface
from plaso.parsers.csv_plugins import dah_events

class DefenderAHDeviceLogonEventsPlugin(interface.CSVPlugin):
  """Parse DeviceLogonEvents from CSV files."""  

  NAME = 'dah_devicelogonevents'
  DATA_FORMAT = 'M365 Defender DeviceLogonEvents table'

  # This constant is used for checking columns at CSV.
  REQUESTED_COLUMNS = {
    'Timestamp',
    'ActionType',
    'LogonType',
    'AccountDomain',
    'AccountName',
    'Protocol',
    'FailureReason',
    'RemoteDeviceName',
    'RemoteIP',
    'RemotePort',
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
    'AdditionalFields'}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {
    'LogonAttempted',
    'LogonFailed',
    'LogonSuccess'}

  _TIMESTAMP = pyparsing.pyparsing_common.iso8601_datetime

  def _ParseTimeStamp(self, date_time_string):
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

  def _ParseLogonAttempted(self, parser_mediator, row):
    """Extracts LogonAttempted action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHLogonAttemptedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.logontype = row['logontype']
    event_data.accountdomain = row['accountdomain']
    event_data.accountname = row['accountname']
    event_data.protocol = row['protocol']
    event_data.remotedevicename = row['remotedevicename']
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
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
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseLogonFailed(self, parser_mediator, row):
    """Extracts LogonFailed action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHLogonFailedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.logontype = row['logontype']
    event_data.accountdomain = row['accountdomain']
    event_data.accountname = row['accountname']
    event_data.protocol = row['protocol']
    event_data.failurereason = row['failurereason']
    event_data.remotedevicename = row['remotedevicename']
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
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
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseLogonSuccess(self, parser_mediator, row):
    """Extracts LogonSuccess action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHLogonSuccessEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.logontype = row['logontype']
    event_data.accountdomain = row['accountdomain']
    event_data.accountname = row['accountname']
    event_data.protocol = row['protocol']
    event_data.remotedevicename = row['remotedevicename']
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
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
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseCsvRow(self, parser_mediator, row):
    """Extracts events from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """

    try:
      tmp_row = dict((k.lower().strip(), v) for k,v in row.items())
      tmp_action = tmp_row['actiontype'].lower().strip()

      if tmp_action == 'logonattempted':
        self._ParseLogonAttempted(parser_mediator, tmp_row)

      elif tmp_action == 'logonfailed':
        self._ParseLogonFailed(parser_mediator, tmp_row)

      elif tmp_action == 'logonsuccess':
        self._ParseLogonSuccess(parser_mediator, tmp_row)

    except pyparsing.ParseException as exception:
      raise errors.WrongParser(
        'unable to parse line with error: {0!s}'.format(
          exception))

csv_parser.CSVFileParser.RegisterPlugin(DefenderAHDeviceLogonEventsPlugin)
