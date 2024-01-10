# -*- coding: utf-8 -*-
"""CSV parser plugin for M365 Defender DeviceEvents table."""

import json
import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.lib import errors
from plaso.parsers import csv_parser
from plaso.parsers.csv_plugins import interface
from plaso.parsers.csv_plugins import dah_events

class DefenderAHDeviceEventsPlugin(interface.CSVPlugin):
  """Parse DeviceEvents from CSV files."""  

  NAME = 'dah_deviceevents'
  DATA_FORMAT = 'M365 Defender DeviceEvents table'

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
    'FileName',
    'FolderPath',
    'SHA1',
    'SHA256',
    'AccountDomain',
    'AccountName',
    'RemoteUrl',
    'RemoteDeviceName',
    'ProcessId',
    'ProcessCommandLine',
    'ProcessCreationTime',
    'RegistryKey',
    'RegistryValueName',
    'RegistryValueData',
    'RemoteIP',
    'RemotePort',
    'LocalIP',
    'LocalPort',
    'FileOriginUrl',
    'FileOriginIP',
    'AdditionalFields'}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {
    'AntivirusDetection',
    'AntivirusEmergencyUpdatesInstalled',
    'AntivirusError',
    'AntivirusMalwareActionFailed',
    'AntivirusMalwareBlocked',
    'AntivirusReport',
    'AntivirusScanCancelled',
    'AntivirusScanCompleted',
    'AsrAdobeReaderChildProcessBlocked',
    'AsrExecutableEmailContentBlocked',
    'AsrExecutableOfficeContentBlocked',
    'AsrLsassCredentialTheftBlocked',
    'AsrObfuscatedScriptBlocked',
    'AsrOfficeChildProcessBlocked',
    'AsrOfficeCommAppChildProcessBlocked',
    'AsrOfficeMacroWin32ApiCallsBlocked',
    'AsrOfficeProcessInjectionBlocked',
    'AsrPersistenceThroughWmiBlocked',
    'AsrPsexecWmiChildProcessBlocked',
    'AsrRansomwareBlocked',
    'AsrScriptExecutableDownloadBlocked',
    'AsrUntrustedExecutableBlocked',
    'AsrUntrustedUsbProcessBlocked',
    'AsrVulnerableSignedDriverBlocked',
    'BrowserLaunchedToOpenUrl',
    'DnsQueryResponse',
    'FirewallInboundConnectionBlocked',
    'FirewallInboundConnectionToAppBlocked',
    'FirewallOutboundConnectionBlocked',
    'FirewallServiceStopped',
    'GetClipboardData',
    'NetworkProtectionUserBypassEvent',
    'NetworkShareObjectAdded',
    'PowerShellCommand',
    'ProcessCreatedUsingWmiQuery',
    'RemoteDesktopConnection',
    'RemoteWmiOperation',
    'ScheduledTaskCreated',
    'ScreenshotTaken',
    'ScriptContent',
    'SecurityGroupCreated',
    'SecurityLogCleared',
    'ServiceInstalled',
    'SmartScreenAppWarning',
    'SmartScreenExploitWarning',
    'SmartScreenUrlWarning',
    'TamperingAttempt',
    'UntrustedWifiConnection',
    'UserAccountAddedToLocalGroup',
    'UserAccountCreated'}

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

  def _ParseDataFromAdditionalFields(self, additionalfields, dataname):
    """Parses data from additionalfields.

    Args:
      additionalfields (str): Additional information about 
        the event in JSON array format

    Returns:
      str: data.
    """
    result = ""

    try:
      if len(additionalfields) > 0 and dataname in additionalfields:
        addjson = json.loads(additionalfields)
        result = addjson[dataname]

    finally:
      pass

    return result

  def _ParseAntivirusDefinitionsUpdated(self, parser_mediator, row):
    """Extracts AntivirusDefinitionsUpdated action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHAntivirusDefinitionsUpdatedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusDefinitionsUpdateFailed(self, parser_mediator, row):
    """Extracts AntivirusDefinitionsUpdateFailed action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHAntivirusDefinitionsUpdateFailedEventData() # pylint: disable=line-too-long
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusDetection(self, parser_mediator, row):
    """Extracts AntivirusDetection action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAntivirusDetectionEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
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
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusEmergencyUpdatesInstalled(self, parser_mediator, row):
    """Extracts AntivirusEmergencyUpdatesInstalled action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHAntivirusEmergencyUpdatesInstalledEventData() # pylint: disable=line-too-long
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusError(self, parser_mediator, row):
    """Extracts AntivirusError action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHAntivirusErrorEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusMalwareActionFailed(self, parser_mediator, row):
    """Extracts AntivirusMalwareActionFailed action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAntivirusMalwareActionFailedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
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
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusMalwareBlocked(self, parser_mediator, row):
    """Extracts AntivirusMalwareBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAntivirusMalwareBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
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
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusReport(self, parser_mediator, row):
    """Extracts AntivirusReport action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAntivirusReportEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
    event_data.fileoriginurl = row['fileoriginurl']
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
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseAntivirusScanCancelled(self, parser_mediator, row):
    """Extracts AntivirusScanCancelled action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAntivirusScanCancelledEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParseAntivirusScanCompleted(self, parser_mediator, row):
    """Extracts AntivirusScanCompleted action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAntivirusScanCompletedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParseAsrAdobeReaderChildProcessBlocked(self, parser_mediator, row):
    """Extracts AsrAdobeReaderChildProcessBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrAdobeReaderChildProcessBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrExecutableEmailContentBlocked(self, parser_mediator, row):
    """Extracts AsrExecutableEmailContentBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrExecutableEmailContentBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrExecutableOfficeContentBlocked(self, parser_mediator, row):
    """Extracts AsrExecutableOfficeContentBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrExecutableOfficeContentBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrLsassCredentialTheftBlocked(self, parser_mediator, row):
    """Extracts AsrLsassCredentialTheftBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrLsassCredentialTheftBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrObfuscatedScriptBlocked(self, parser_mediator, row):
    """Extracts AsrObfuscatedScriptBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrObfuscatedScriptBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrOfficeChildProcessBlocked(self, parser_mediator, row):
    """Extracts AsrOfficeChildProcessBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrOfficeChildProcessBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrOfficeCommAppChildProcessBlocked(self, parser_mediator, row):
    """Extracts AsrOfficeCommAppChildProcessBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrOfficeCommAppChildProcessBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrOfficeMacroWin32ApiCallsBlocked(self, parser_mediator, row):
    """Extracts AsrOfficeMacroWin32ApiCallsBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrOfficeMacroWin32ApiCallsBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrOfficeProcessInjectionBlocked(self, parser_mediator, row):
    """Extracts AsrOfficeProcessInjectionBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrOfficeProcessInjectionBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrPersistenceThroughWmiBlocked(self, parser_mediator, row):
    """Extracts AsrPersistenceThroughWmiBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrPersistenceThroughWmiBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrPsexecWmiChildProcessBlocked(self, parser_mediator, row):
    """Extracts AsrPsexecWmiChildProcessBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrPsexecWmiChildProcessBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrRansomwareBlocked(self, parser_mediator, row):
    """Extracts AsrRansomwareBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrRansomwareBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrScriptExecutableDownloadBlocked(self, parser_mediator, row):
    """Extracts AsrScriptExecutableDownloadBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrScriptExecutableDownloadBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrUntrustedExecutableBlocked(self, parser_mediator, row):
    """Extracts AsrUntrustedExecutableBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrUntrustedExecutableBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrUntrustedUsbProcessBlocked(self, parser_mediator, row):
    """Extracts AsrUntrustedUsbProcessBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrUntrustedUsbProcessBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseAsrVulnerableSignedDriverBlocked(self, parser_mediator, row):
    """Extracts AsrVulnerableSignedDriverBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHAsrVulnerableSignedDriverBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.sha1 = row['sha1']
    event_data.sha256 = row['sha256']
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

  def _ParseBrowserLaunchedToOpenUrl(self, parser_mediator, row):
    """Extracts BrowserLaunchedToOpenUrl action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHBrowserLaunchedToOpenUrlEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteurl = row['remoteurl']
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

  def _ParseDnsQueryResponse(self, parser_mediator, row):
    """Extracts DnsQueryResponse action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHDnsQueryResponseEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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
    event_data.dnsquery = self._ParseDataFromAdditionalFields(row['additionalfields'], "DnsQueryString")
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseFirewallInboundConnectionBlocked(self, parser_mediator, row):
    """Extracts FirewallInboundConnectionBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFirewallInboundConnectionBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
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

  def _ParseFirewallInboundConnectionToAppBlocked(self, parser_mediator, row):
    """Extracts FirewallInboundConnectionToAppBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFirewallInboundConnectionToAppBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParseFirewallOutboundConnectionBlocked(self, parser_mediator, row):
    """Extracts FirewallOutboundConnectionBlocked action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFirewallOutboundConnectionBlockedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteip = row['remoteip']
    event_data.remoteport = row['remoteport']
    event_data.localip = row['localip']
    event_data.localport = row['localport']
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

  def _ParseFirewallServiceStopped(self, parser_mediator, row):
    """Extracts FirewallServiceStopped action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHFirewallServiceStoppedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParseGetClipboardData(self, parser_mediator, row):
    """Extracts GetClipboardData action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHGetClipboardDataEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParseNetworkProtectionUserBypassEvent(self, parser_mediator, row):
    """Extracts NetworkProtectionUserBypassEvent action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHNetworkProtectionUserBypassEventEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParseNetworkShareObjectAdded(self, parser_mediator, row):
    """Extracts NetworkShareObjectAdded action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHNetworkShareObjectAddedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParsePowerShellCommand(self, parser_mediator, row):
    """Extracts PowerShellCommand action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHPowerShellCommandEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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
    event_data.pscommand = self._ParseDataFromAdditionalFields(row['additionalfields'], "Command")

    parser_mediator.ProduceEventData(event_data)

  def _ParseProcessCreatedUsingWmiQuery(self, parser_mediator, row):
    """Extracts ProcessCreatedUsingWmiQuery action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHProcessCreatedUsingWmiQueryEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseRemoteDesktopConnection(self, parser_mediator, row):
    """Extracts RemoteDesktopConnection action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHRemoteDesktopConnectionEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.localip = row['localip']
    event_data.localport = row['localport']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseRemoteWmiOperation(self, parser_mediator, row):
    """Extracts RemoteWmiOperation action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHRemoteWmiOperationEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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
    event_data.remotedevicename = row['remotedevicename']
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseScheduledTaskCreated(self, parser_mediator, row):
    """Extracts ScheduledTaskCreated action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHScheduledTaskCreatedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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
    event_data.taskname = self._ParseDataFromAdditionalFields(row['additionalfields'], "TaskName")
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseScreenshotTaken(self, parser_mediator, row):
    """Extracts ScreenshotTaken action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHScreenshotTakenEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
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

  def _ParseScriptContent(self, parser_mediator, row):
    """Extracts ScriptContent action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHScriptContentEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.sha256 = row['sha256']
    event_data.initiatingprocessid = row['initiatingprocessid']
    event_data.scriptcontent = self._ParseDataFromAdditionalFields(row['additionalfields'], "ScriptContent")

    parser_mediator.ProduceEventData(event_data)

  def _ParseSecurityGroupCreated(self, parser_mediator, row):
    """Extracts SecurityGroupCreated action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHSecurityGroupCreatedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.initiatingprocessid = row['initiatingprocessid']
    event_data.initiatingprocessparentid = row['initiatingprocessparentid']
    event_data.groupname = self._ParseDataFromAdditionalFields(row['additionalfields'], "GroupName")

    parser_mediator.ProduceEventData(event_data)

  def _ParseSecurityLogCleared(self, parser_mediator, row):
    """Extracts SecurityLogCleared action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHSecurityLogClearedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']

    parser_mediator.ProduceEventData(event_data)

  def _ParseServiceInstalled(self, parser_mediator, row):
    """Extracts ServiceInstalled action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHServiceInstalledEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
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
    event_data.servicename = self._ParseDataFromAdditionalFields(row['additionalfields'], "ServiceName")
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseSmartScreenAppWarning(self, parser_mediator, row):
    """Extracts SmartScreenAppWarning action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHSmartScreenAppWarningEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
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

  def _ParseSmartScreenExploitWarning(self, parser_mediator, row):
    """Extracts SmartScreenExploitWarning action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHSmartScreenExploitWarningEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteurl = row['remoteurl']
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

  def _ParseSmartScreenUrlWarning(self, parser_mediator, row):
    """Extracts SmartScreenUrlWarning action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHSmartScreenUrlWarningEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.remoteurl = row['remoteurl']
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

  def _ParseTamperingAttempt(self, parser_mediator, row):
    """Extracts TamperingAttempt action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHTamperingAttemptEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.filename = row['filename']
    event_data.folderpath = row['folderpath']
    event_data.registrykey = row['registrykey']
    event_data.registryvaluename = row['registryvaluename']
    event_data.registryvaluedata = row['registryvaluedata']
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

  def _ParseUntrustedWifiConnection(self, parser_mediator, row):
    """Extracts UntrustedWifiConnection action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    event_data = dah_events.DefenderAHUntrustedWifiConnectionEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseUserAccountAddedToLocalGroup(self, parser_mediator, row):
    """Extracts UserAccountAddedToLocalGroup action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHUserAccountAddedToLocalGroupEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.groupdomainname = self._ParseDataFromAdditionalFields(row['additionalfields'], "GroupDomainName")
    event_data.groupname = self._ParseDataFromAdditionalFields(row['additionalfields'], "GroupName")
    event_data.additionalfields = row['additionalfields']

    parser_mediator.ProduceEventData(event_data)

  def _ParseUserAccountCreated(self, parser_mediator, row):
    """Extracts UserAccountCreated action from a CSV file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """
    # pylint: disable=line-too-long
    event_data = dah_events.DefenderAHUserAccountCreatedEventData()
    event_data.timestamp = self._ParseTimeStamp(row['timestamp'])
    event_data.initiatingprocessaccountdomain = row['initiatingprocessaccountdomain']
    event_data.initiatingprocessaccountname = row['initiatingprocessaccountname']
    event_data.accountdomain = row['accountdomain']
    event_data.accountname = row['accountname']

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

      if tmp_action == 'antivirusdefinitionsupdated':
        self._ParseAntivirusDefinitionsUpdated(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusdefinitionsupdatefailed':
        self._ParseAntivirusDefinitionsUpdateFailed(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusdetection':
        self._ParseAntivirusDetection(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusemergencyupdatesinstalled':
        self._ParseAntivirusEmergencyUpdatesInstalled(parser_mediator, tmp_row)

      elif tmp_action == 'antiviruserror':
        self._ParseAntivirusError(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusmalwareactionfailed':
        self._ParseAntivirusMalwareActionFailed(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusmalwareblocked':
        self._ParseAntivirusMalwareBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusreport':
        self._ParseAntivirusReport(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusscancancelled':
        self._ParseAntivirusScanCancelled(parser_mediator, tmp_row)

      elif tmp_action == 'antivirusscancompleted':
        self._ParseAntivirusScanCompleted(parser_mediator, tmp_row)

      elif tmp_action == 'asradobereaderchildprocessblocked':
        self._ParseAsrAdobeReaderChildProcessBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrexecutableemailcontentblocked':
        self._ParseAsrExecutableEmailContentBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrexecutableofficecontentblocked':
        self._ParseAsrExecutableOfficeContentBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrlsasscredentialtheftblocked':
        self._ParseAsrLsassCredentialTheftBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrobfuscatedscriptblocked':
        self._ParseAsrObfuscatedScriptBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrofficechildprocessblocked':
        self._ParseAsrOfficeChildProcessBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrofficecommappchildprocessblocked':
        self._ParseAsrOfficeCommAppChildProcessBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrofficemacrowin32apicallsblocked':
        self._ParseAsrOfficeMacroWin32ApiCallsBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrofficeprocessinjectionblocked':
        self._ParseAsrOfficeProcessInjectionBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrpersistencethroughwmiblocked':
        self._ParseAsrPersistenceThroughWmiBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrpsexecwmichildprocessblocked':
        self._ParseAsrPsexecWmiChildProcessBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrransomwareblocked':
        self._ParseAsrRansomwareBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrscriptexecutabledownloadblocked':
        self._ParseAsrScriptExecutableDownloadBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asruntrustedexecutableblocked':
        self._ParseAsrUntrustedExecutableBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asruntrustedusbprocessblocked':
        self._ParseAsrUntrustedUsbProcessBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'asrvulnerablesigneddriverblocked':
        self._ParseAsrVulnerableSignedDriverBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'browserlaunchedtoopenurl':
        self._ParseBrowserLaunchedToOpenUrl (parser_mediator, tmp_row)

      elif tmp_action == 'dnsqueryresponse':
        self._ParseDnsQueryResponse(parser_mediator, tmp_row)

      elif tmp_action == 'firewallinboundconnectionblocked':
        self._ParseFirewallInboundConnectionBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'firewallinboundconnectiontoappblocked':
        self._ParseFirewallInboundConnectionToAppBlocked(
          parser_mediator, tmp_row)

      elif tmp_action == 'firewalloutboundconnectionblocked':
        self._ParseFirewallOutboundConnectionBlocked(parser_mediator, tmp_row)

      elif tmp_action == 'firewallservicestopped':
        self._ParseFirewallServiceStopped(parser_mediator, tmp_row)

      elif tmp_action == 'getclipboarddata':
        self._ParseGetClipboardData(parser_mediator, tmp_row)

      elif tmp_action == 'networkprotectionuserbypassevent':
        self._ParseNetworkProtectionUserBypassEvent(parser_mediator, tmp_row)

      elif tmp_action == 'networkshareobjectadded':
        self._ParseNetworkShareObjectAdded(parser_mediator, tmp_row)

      elif tmp_action == 'powershellcommand':
        self._ParsePowerShellCommand(parser_mediator, tmp_row)

      elif tmp_action == 'processcreatedusingwmiquery':
        self._ParseProcessCreatedUsingWmiQuery(parser_mediator, tmp_row)

      elif tmp_action == 'remotedesktopconnection':
        self._ParseRemoteDesktopConnection(parser_mediator, tmp_row)

      elif tmp_action == 'remotewmioperation':
        self._ParseRemoteWmiOperation(parser_mediator, tmp_row)

      elif tmp_action == 'scheduledtaskcreated':
        self._ParseScheduledTaskCreated(parser_mediator, tmp_row)

      elif tmp_action == 'screenshottaken':
        self._ParseScreenshotTaken(parser_mediator, tmp_row)

      elif tmp_action == 'scriptcontent':
        self._ParseScriptContent(parser_mediator, tmp_row)

      elif tmp_action == 'securitygroupcreated':
        self._ParseSecurityGroupCreated(parser_mediator, tmp_row)

      elif tmp_action == 'securitylogcleared':
        self._ParseSecurityLogCleared(parser_mediator, tmp_row)

      elif tmp_action == 'serviceinstalled':
        self._ParseServiceInstalled(parser_mediator, tmp_row)

      elif tmp_action == 'smartscreenappwarning':
        self._ParseSmartScreenAppWarning(parser_mediator, tmp_row)

      elif tmp_action == 'smartscreenexploitwarning':
        self._ParseSmartScreenExploitWarning(parser_mediator, tmp_row)

      elif tmp_action == 'smartscreenurlwarning':
        self._ParseSmartScreenUrlWarning(parser_mediator, tmp_row)

      elif tmp_action == 'tamperingattempt':
        self._ParseTamperingAttempt(parser_mediator, tmp_row)

      elif tmp_action == 'untrustedwificonnection':
        self._ParseUntrustedWifiConnection(parser_mediator, tmp_row)

      elif tmp_action == 'useraccountaddedtolocalgroup':
        self._ParseUserAccountAddedToLocalGroup(parser_mediator, tmp_row)

      elif tmp_action == 'useraccountcreated':
        self._ParseUserAccountCreated(parser_mediator, tmp_row)

    except pyparsing.ParseException as exception:
      raise errors.WrongParser(
        'unable to parse line with error: {0!s}'.format(
          exception))

csv_parser.CSVFileParser.RegisterPlugin(DefenderAHDeviceEventsPlugin)
