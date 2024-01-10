# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Defender DeviceFileEvents table."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.lib import errors
from plaso.parsers import csv_parser
from plaso.parsers.csv_plugins import interface
from plaso.parsers.csv_plugins import dah_events

class DefenderAHDeviceFileEventsPlugin(interface.CSVPlugin):
  """Parse DeviceFileEvents from CSV files."""  

  NAME = 'dah_devicefileevents'
  DATA_FORMAT = 'M365 Defender DeviceFileEvents table'

  # This constant is used for checking columns at CSV.
  REQUESTED_COLUMNS = {'Timestamp',
                       'ActionType',
                       'FileName',
                       'FolderPath',
                       'SHA1',
                       'SHA256',
                       'FileOriginUrl',
                       'FileOriginReferrerUrl',
                       'FileOriginIP',
                       'PreviousFolderPath',
                       'PreviousFileName',
                       'InitiatingProcessAccountDomain',
                       'InitiatingProcessAccountName',
                       'InitiatingProcessSHA1',
                       'InitiatingProcessSHA256',
                       'InitiatingProcessFolderPath',
                       'InitiatingProcessFileName',
                       'InitiatingProcessId',
                       'InitiatingProcessCommandLine',
                       'InitiatingProcessCreationTime',
                       'InitiatingProcessParentId',
                       'InitiatingProcessParentFileName',
                       'InitiatingProcessParentCreationTime',
                       'RequestProtocol',
                       'RequestSourceIP',
                       'RequestSourcePort',
                       'RequestAccountName',
                       'RequestAccountDomain',
                       'ShareName',
                       'AdditionalFields'}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {
    'FileCreated',
    'FileDeleted',
    'FileModified',
    'FileRenamed'}

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

  def _ParseFileCreated(self, parser_mediator, row):
    """Extracts FileCreated action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFileCreatedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
    event_data.fileoriginreferrerurl = row['fileoriginreferrerurl']
    event_data.fileoriginip = row['fileoriginip']
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
    event_data.requestprotocol = row['requestprotocol']
    event_data.requestsourceip = row['requestsourceip']
    event_data.requestsourceport = row['requestsourceport']
    event_data.requestaccountname = row['requestaccountname']
    event_data.requestaccountdomain = row['requestaccountdomain']
    event_data.sharename = row['sharename']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseFileDeleted(self, parser_mediator, row):
    """Extracts FileDeleted action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFileDeletedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
    event_data.fileoriginreferrerurl = row['fileoriginreferrerurl']
    event_data.fileoriginip = row['fileoriginip']
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
    event_data.requestprotocol = row['requestprotocol']
    event_data.requestsourceip = row['requestsourceip']
    event_data.requestsourceport = row['requestsourceport']
    event_data.requestaccountname = row['requestaccountname']
    event_data.requestaccountdomain = row['requestaccountdomain']
    event_data.sharename = row['sharename']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseFileModified(self, parser_mediator, row):
    """Extracts FileModified action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFileModifiedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
    event_data.fileoriginreferrerurl = row['fileoriginreferrerurl']
    event_data.fileoriginip = row['fileoriginip']
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
    event_data.requestprotocol = row['requestprotocol']
    event_data.requestsourceip = row['requestsourceip']
    event_data.requestsourceport = row['requestsourceport']
    event_data.requestaccountname = row['requestaccountname']
    event_data.requestaccountdomain = row['requestaccountdomain']
    event_data.sharename = row['sharename']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseFileRenamed(self, parser_mediator, row):
    """Extracts FileRenamed action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFileRenamedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
    event_data.fileoriginreferrerurl = row['fileoriginreferrerurl']
    event_data.fileoriginip = row['fileoriginip']
    event_data.previousfolderpath = row['previousfolderpath']
    event_data.previousfilename = row['previousfilename']
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
    event_data.requestprotocol = row['requestprotocol']
    event_data.requestsourceip = row['requestsourceip']
    event_data.requestsourceport = row['requestsourceport']
    event_data.requestaccountname = row['requestaccountname']
    event_data.requestaccountdomain = row['requestaccountdomain']
    event_data.sharename = row['sharename']
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

      if tmp_action == 'filecreated':
        self._ParseFileCreated(parser_mediator, tmp_row)

      elif tmp_action == 'filedeleted':
        self._ParseFileDeleted(parser_mediator, tmp_row)

      elif tmp_action == 'filemodified':
        self._ParseFileModified(parser_mediator, tmp_row)

      elif tmp_action == 'filerenamed':
        self._ParseFileRenamed(parser_mediator, tmp_row)

    except pyparsing.ParseException as exception:
      raise errors.WrongParser(
        'unable to parse line with error: {0!s}'.format(
          exception))

csv_parser.CSVFileParser.RegisterPlugin(DefenderAHDeviceFileEventsPlugin)
