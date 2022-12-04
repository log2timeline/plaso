# -*- coding: utf-8 -*-
"""SQLite parser plugin for Windows 10 Timeline database files."""

import json

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class WindowsTimelineGenericEventData(events.EventData):
  """Windows Timeline database generic event data.

  Attributes:
    application_display_name (str): a more human-friendly version of the
        package_identifier, such as 'Docker for Windows' or 'Microsoft Store'.
    description (str): this is an optional field, used to describe the action in
        the timeline view, and is usually populated with the path of the file
        currently open in the program described by package_identifier.
        Otherwise None.
    package_identifier (str): the package ID or path to the executable run.
        Depending on the program, this either looks like a path
        (for example, c:\\python34\\python.exe) or like a package name
        (for example Docker.DockerForWindows.Settings).
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the activity.
  """

  DATA_TYPE = 'windows:timeline:generic'

  def __init__(self):
    """Initialize event data"""
    super(WindowsTimelineGenericEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_display_name = None
    self.description = None
    self.package_identifier = None
    self.start_time = None


class WindowsTimelineUserEngagedEventData(events.EventData):
  """Windows Timeline database User Engaged event data.

  Contains information describing how long a user interacted with an application
  for.

  Attributes:
    active_duration_seconds (int): the number of seconds the user spent
        interacting with the program.
    package_identifier (str): the package ID or location of the executable
        the user interacted with.
    reporting_app (str): the name of the application that reported the user's
        interaction. This is the name of a monitoring tool, for example
        "ShellActivityMonitor".
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the activity.
  """

  DATA_TYPE = 'windows:timeline:user_engaged'

  def __init__(self):
    """Initialize event data"""
    super(WindowsTimelineUserEngagedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.active_duration_seconds = None
    self.package_identifier = None
    self.reporting_app = None
    self.start_time = None


class WindowsTimelinePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Windows 10 Timeline database files.

  The Windows 10 Timeline database file is typically stored in:
  %APPDATA%\\Local\\ConnectedDevicesPlatform\\L.<username>\\ActivitiesCache.db
  """

  NAME = 'windows_timeline'
  DATA_FORMAT = 'Windows 10 Timeline SQLite database (ActivitiesCache.db) file'

  REQUIRED_STRUCTURE = {
      'Activity': frozenset([
          'StartTime', 'Payload', 'Id', 'AppId']),
      'Activity_PackageId': frozenset([
          'ActivityId', 'PackageName'])}

  QUERIES = [
      (('SELECT StartTime, Payload, PackageName FROM Activity '
        'INNER JOIN Activity_PackageId ON Activity.Id = '
        'Activity_PackageId.ActivityId WHERE instr(Payload, "UserEngaged") > 0'
        ' AND Platform = "packageid"'), 'ParseUserEngagedRow'),
      (('SELECT StartTime, Payload, AppId FROM Activity '
        'WHERE instr(Payload, "UserEngaged") = 0'), 'ParseGenericRow')]

  SCHEMAS = [{
      'Activity': (
          'CREATE TABLE [Activity]([Id] GUID PRIMARY KEY NOT NULL, [AppId] '
          'TEXT NOT NULL, [PackageIdHash] TEXT, [AppActivityId] TEXT, '
          '[ActivityType] INT NOT NULL, [ActivityStatus] INT NOT NULL, '
          '[ParentActivityId] GUID, [Tag] TEXT, [Group] TEXT, [MatchId] TEXT, '
          '[LastModifiedTime] DATETIME NOT NULL, [ExpirationTime] DATETIME, '
          '[Payload] BLOB, [Priority] INT, [IsLocalOnly] INT, '
          '[PlatformDeviceId] TEXT, [CreatedInCloud] DATETIME, [StartTime] '
          'DATETIME, [EndTime] DATETIME, [LastModifiedOnClient] DATETIME, '
          '[GroupAppActivityId] TEXT, [ClipboardPayload] BLOB, [EnterpriseId] '
          'TEXT, [OriginalPayload] BLOB, [OriginalLastModifiedOnClient] '
          'DATETIME, [ETag] INT NOT NULL)'),
      'ActivityAssetCache': (
          'CREATE TABLE [ActivityAssetCache]([ResourceId] INTEGER PRIMARY KEY '
          'AUTOINCREMENT NOT NULL, [AppId] TEXT NOT NULL, [AssetHash] TEXT '
          'NOT NULL, [TimeToLive] DATETIME NOT NULL, [AssetUri] TEXT, '
          '[AssetId] TEXT, [AssetKey] TEXT, [Contents] BLOB)'),
      'ActivityOperation': (
          'CREATE TABLE [ActivityOperation]([OperationOrder] INTEGER PRIMARY '
          'KEY ASC NOT NULL, [Id] GUID NOT NULL, [OperationType] INT NOT '
          'NULL, [AppId] TEXT NOT NULL, [PackageIdHash] TEXT, [AppActivityId] '
          'TEXT, [ActivityType] INT NOT NULL, [ParentActivityId] GUID, [Tag] '
          'TEXT, [Group] TEXT, [MatchId] TEXT, [LastModifiedTime] DATETIME '
          'NOT NULL, [ExpirationTime] DATETIME, [Payload] BLOB, [Priority] '
          'INT, [CreatedTime] DATETIME, [Attachments] TEXT, '
          '[PlatformDeviceId] TEXT, [CreatedInCloud] DATETIME, [StartTime] '
          'DATETIME NOT NULL, [EndTime] DATETIME, [LastModifiedOnClient] '
          'DATETIME NOT NULL, [CorrelationVector] TEXT, [GroupAppActivityId] '
          'TEXT, [ClipboardPayload] BLOB, [EnterpriseId] TEXT, '
          '[OriginalPayload] BLOB, [OriginalLastModifiedOnClient] DATETIME, '
          '[ETag] INT NOT NULL)'),
      'Activity_PackageId': (
          'CREATE TABLE [Activity_PackageId]([ActivityId] GUID NOT NULL, '
          '[Platform] TEXT NOT NULL, [PackageName] TEXT NOT NULL, '
          '[ExpirationTime] DATETIME NOT NULL)'),
      'AppSettings': (
          'CREATE TABLE [AppSettings]([AppId] TEXT PRIMARY KEY NOT NULL, '
          '[SettingsPropertyBag] BLOB, [AppTitle] TEXT, [Logo4141] TEXT)'),
      'ManualSequence': (
          'CREATE TABLE [ManualSequence]([Key] TEXT PRIMARY KEY NOT NULL, '
          '[Value] INT NOT NULL)'),
      'Metadata': (
          'CREATE TABLE [Metadata]([Key] TEXT PRIMARY KEY NOT NULL, [Value] '
          'TEXT)')},{
      'Activity': (
          'CREATE TABLE [Activity]([Id] GUID PRIMARY KEY NOT NULL, [AppId] '
          'TEXT NOT NULL, [PackageIdHash] TEXT, [AppActivityId] TEXT, '
          '[ActivityType] INT NOT NULL, [ActivityStatus] INT NOT NULL, '
          '[ParentActivityId] GUID, [Tag] TEXT, [Group] TEXT, [MatchId] TEXT, '
          '[LastModifiedTime] DATETIME NOT NULL, [ExpirationTime] DATETIME, '
          '[Payload] BLOB, [Priority] INT, [IsLocalOnly] INT, '
          '[PlatformDeviceId] TEXT, [CreatedInCloud] DATETIME, [StartTime] '
          'DATETIME, [EndTime] DATETIME, [LastModifiedOnClient] DATETIME, '
          '[GroupAppActivityId] TEXT, [ClipboardPayload] BLOB, [EnterpriseId] '
          'TEXT, [OriginalPayload] BLOB, [UserActionState] INT,[IsRead] '
          'INT,[OriginalLastModifiedOnClient] DATETIME, [GroupItems] TEXT, '
          '[ETag] INT NOT NULL)'),
      'ActivityAssetCache': (
          'CREATE TABLE [ActivityAssetCache]([ResourceId] INTEGER PRIMARY KEY '
          'AUTOINCREMENT NOT NULL, [AppId] TEXT NOT NULL, [AssetHash] TEXT '
          'NOT NULL, [TimeToLive] DATETIME NOT NULL, [AssetUri] TEXT, '
          '[AssetId] TEXT, [AssetKey] TEXT, [Contents] BLOB)'),
      'ActivityOperation': (
          'CREATE TABLE [ActivityOperation]([OperationOrder] INTEGER PRIMARY '
          'KEY ASC NOT NULL, [Id] GUID NOT NULL, [OperationType] INT NOT '
          'NULL, [AppId] TEXT NOT NULL, [PackageIdHash] TEXT, [AppActivityId] '
          'TEXT, [ActivityType] INT NOT NULL, [ParentActivityId] GUID, [Tag] '
          'TEXT, [Group] TEXT, [MatchId] TEXT, [LastModifiedTime] DATETIME '
          'NOT NULL, [ExpirationTime] DATETIME, [Payload] BLOB, [Priority] '
          'INT, [CreatedTime] DATETIME, [OperationExpirationTime] '
          'DATETIME,[Attachments] TEXT, [PlatformDeviceId] TEXT, '
          '[CreatedInCloud] DATETIME, [StartTime] DATETIME NOT NULL, '
          '[EndTime] DATETIME, [LastModifiedOnClient] DATETIME NOT NULL, '
          '[CorrelationVector] TEXT, [GroupAppActivityId] TEXT, '
          '[ClipboardPayload] BLOB, [EnterpriseId] TEXT, [UserActionState] '
          'INT,[IsRead] INT,[OriginalPayload] BLOB, '
          '[OriginalLastModifiedOnClient] DATETIME, [UploadAllowedByPolicy] '
          'INT NOT NULL DEFAULT 1, [PatchFields] BLOB, [GroupItems] TEXT, '
          '[ETag] INT NOT NULL)'),
      'Activity_PackageId': (
          'CREATE TABLE [Activity_PackageId]([ActivityId] GUID NOT NULL, '
          '[Platform] TEXT NOT NULL COLLATE NOCASE, [PackageName] TEXT NOT '
          'NULL COLLATE NOCASE, [ExpirationTime] DATETIME NOT NULL)'),
      'AppSettings': (
          'CREATE TABLE [AppSettings]([AppId] TEXT PRIMARY KEY NOT NULL, '
          '[SettingsPropertyBag] BLOB, [AppTitle] TEXT, [Logo4141] TEXT)'),
      'DataEncryptionKeys': (
          'CREATE TABLE [DataEncryptionKeys]([KeyVersion] INTEGER PRIMARY KEY '
          'NOT NULL, [KeyValue] TEXT NOT NULL COLLATE NOCASE, '
          '[CreatedInCloudTime] DATETIME NOT NULL)'),
      'ManualSequence': (
          'CREATE TABLE [ManualSequence]([Key] TEXT PRIMARY KEY NOT NULL, '
          '[Value] INT NOT NULL)'),
      'Metadata': (
          'CREATE TABLE [Metadata]([Key] TEXT PRIMARY KEY NOT NULL, [Value] '
          'TEXT)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def ParseGenericRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a generic windows timeline row.

      Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    # Payload is JSON serialized as binary data in a BLOB field, with the text
    # encoded as UTF-8.
    payload_json_bytes = bytes(self._GetRowValue(query_hash, row, 'Payload'))
    payload_json_string = payload_json_bytes.decode('utf-8')
    payload = json.loads(payload_json_string)

    application_display_name = payload.get('appDisplayName', None)
    if not application_display_name:
      # Fall back to displayText if appDisplayName isn't available
      application_display_name = payload.get('displayText', None)

    # AppId is JSON stored as unicode text.
    appid_entries_string = self._GetRowValue(query_hash, row, 'AppId')
    appid_entries = json.loads(appid_entries_string)

    package_identifier = None

    # Attempt to populate the package_identifier field by checking each of
    # these fields in the AppId JSON.
    package_id_locations = [
        'packageId', 'x_exe_path', 'windows_win32', 'windows_universal',
        'alternateId']
    for location in package_id_locations:
      for entry in appid_entries:
        if entry['platform'] == location and entry['application'] != '':
          package_identifier = entry['application']
          break
      if package_identifier is None:
        # package_identifier has been populated and we're done.
        break

    event_data = WindowsTimelineGenericEventData()
    event_data.application_display_name = application_display_name
    event_data.description = payload.get('description', None)
    event_data.package_identifier = package_identifier
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'StartTime')

    parser_mediator.ProduceEventData(event_data)

  def ParseUserEngagedRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a timeline row that describes a user interacting with an app.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    # Payload is JSON serialized as binary data in a BLOB field, with the text
    # encoded as UTF-8.
    payload_json_bytes = bytes(self._GetRowValue(query_hash, row, 'Payload'))
    payload_json_string = payload_json_bytes.decode('utf-8')
    payload = json.loads(payload_json_string)

    active_duration_seconds = payload.get('activeDurationSeconds', None)
    if active_duration_seconds is not None:
      active_duration_seconds = int(active_duration_seconds)

    event_data = WindowsTimelineUserEngagedEventData()
    event_data.active_duration_seconds = active_duration_seconds
    event_data.package_identifier = self._GetRowValue(
        query_hash, row, 'PackageName')
    event_data.reporting_app = payload.get('reportingApp', None)
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'StartTime')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(WindowsTimelinePlugin)
