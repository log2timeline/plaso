# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Defender DeviceImageLoadEvents table."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.lib import errors
from plaso.parsers import csv_parser
from plaso.parsers.csv_plugins import interface
from plaso.parsers.csv_plugins import dah_events

class DefenderAHDeviceRegistryEventsPlugin(interface.CSVPlugin):
  """Parse DeviceRegistryEvents from CSV files."""  

  NAME = 'dah_deviceregistryevents'
  DATA_FORMAT = 'M365 Defender DeviceRegistryEvents table'

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
    'RegistryKey',
    'RegistryValueName',
    'RegistryValueData',
    'PreviousRegistryKey',
    'PreviousRegistryValueName',
    'PreviousRegistryValueData'}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {
    'RegistryKeyCreated',
    'RegistryKeyDeleted',
    'RegistryKeyRenamed',
    'RegistryValueDeleted',
    'RegistryValueSet'}

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

  def _ParseRegistryKeyCreated(self, parser_mediator, row):
    """Extracts RegistryKeyCreated action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHRegistryKeyCreatedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.registrykey = row['registrykey']
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

  def _ParseRegistryKeyDeleted(self, parser_mediator, row):
    """Extracts RegistryKeyDeleted action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHRegistryKeyDeletedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.previousregistrykey = row['previousregistrykey']
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

  def _ParseRegistryKeyRenamed(self, parser_mediator, row):
    """Extracts RegistryKeyRenamed action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHRegistryKeyRenamedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.registrykey = row['registrykey']
    event_data.previousregistrykey = row['previousregistrykey']
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

  def _ParseRegistryValueDeleted(self, parser_mediator, row):
    """Extracts RegistryValueDeleted action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHRegistryValueDeletedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.previousregistrykey = row['previousregistrykey']
    event_data.previousregistryvaluename = row['previousregistryvaluename']
    event_data.previousregistryvaluedata = row['previousregistryvaluedata']
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

  def _ParseRegistryValueSet(self, parser_mediator, row):
    """Extracts RegistryValueSet action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row ([row]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHRegistryValueSetEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.registrykey = row['registrykey']
    event_data.registryvaluename = row['registryvaluename']
    event_data.registryvaluedata = row['registryvaluedata']
    event_data.previousregistryvaluename = row['previousregistryvaluename']
    event_data.previousregistryvaluedata = row['previousregistryvaluedata']
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

  def _ParseCsvRow(self, parser_mediator, row):
    """Extracts events from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """

    try:
      tmp_row = dict((k.lower().strip(), v) for k,v in row.items())
      tmp_action = tmp_row['actiontype'].lower().strip()

      if tmp_action == 'registrykeycreated':
        self._ParseRegistryKeyCreated(parser_mediator, tmp_row)

      elif tmp_action == 'registrykeydeleted':
        self._ParseRegistryKeyDeleted(parser_mediator, tmp_row)

      elif tmp_action == 'registrykeyrenamed':
        self._ParseRegistryKeyRenamed(parser_mediator, tmp_row)

      elif tmp_action == 'registryvaluedeleted':
        self._ParseRegistryValueDeleted(parser_mediator, tmp_row)

      elif tmp_action == 'registryvalueset':
        self._ParseRegistryValueSet(parser_mediator, tmp_row)

    except pyparsing.ParseException as exception:
      raise errors.WrongParser(
        'unable to parse line with error: {0!s}'.format(
          exception))

csv_parser.CSVFileParser.RegisterPlugin(DefenderAHDeviceRegistryEventsPlugin)
