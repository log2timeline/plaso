# -*- coding: utf-8 -*-
"""Plugin for the Windows 10 Timeline SQLite database.

Timeline events on Windows are stored in a SQLite
database file usually found in ActivitiesCache.db,
path is usually something like:
%APPDATA%\\Local\\ConnectedDevicesPlatform\\L.<username>
"""

from __future__ import unicode_literals

import json

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

class WindowsTimelineGenericEventData(events.EventData):
  """Windows Timeline database generic event data.

  Attributes:
    package_identifier (str): the package ID or path to the executable run.
        Depending on the program, this either looks like a path
        (for example, c:\\python34\\python.exe) or like a package name
        (for example Docker.DockerForWindows.Settings).
    description (str): this is an optional field, used to describe the action in
        the timeline view, and is usually populated with the path of the file
        currently open in the program described by package_identifier.
        Otherwise None.
    application_display_name (str): a more human-friendly version of the
        package_identifier, such as 'Docker for Windows' or 'Microsoft Store'.
  """

  DATA_TYPE = 'windows:timeline:generic'

  def __init__(self):
    """Initialize event data"""
    super(WindowsTimelineGenericEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.package_identifier = None
    self.description = None
    self.application_display_name = None

class WindowsTimelineUserEngagedEventData(events.EventData):
  """Windows Timeline database User Engaged event data.

  Contains information describing how long a user interacted with an application
  for.

  Attributes:
    package_identifier (str): the package ID or location of the executable
        the user interacted with.
    reporting_app (str): the name of the application that reported the user's
        interaction. This is the name of a monitoring tool, for example
        "ShellActivityMonitor".
    active_duration_seconds (int): the number of seconds the user spent
        interacting with the program.
  """

  DATA_TYPE = 'windows:timeline:user_engaged'

  def __init__(self):
    """Initialize event data"""
    super(WindowsTimelineUserEngagedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.package_identifier = None
    self.reporting_app = None
    self.active_duration_seconds = None

class WindowsTimelinePlugin(interface.SQLitePlugin):
  """Parse the Windows Timeline SQLite database."""

  NAME = 'windows_timeline'
  DESCRIPTION = 'Parser for the Windows Timeline SQLite database'

  REQUIRED_STRUCTURE = {
      'Activity': frozenset([
          'StartTime', 'Payload', 'PackageName', 'Id', 'AppId']),
      'Activity_PackageId': frozenset([
          'ActivityId'])}

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
          'TEXT)')}]

  def ParseGenericRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a generic windows timeline row.

      Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = WindowsTimelineGenericEventData()

    # Payload is JSON serialized as binary data in a BLOB field, with the text
    # encoded as UTF-8.
    payload_json_bytes = bytes(self._GetRowValue(query_hash, row, 'Payload'))
    payload_json_string = payload_json_bytes.decode('utf-8')
    # AppId is JSON stored as unicode text.
    appid_entries_string = self._GetRowValue(query_hash, row, 'AppId')

    payload = json.loads(payload_json_string)
    appid_entries = json.loads(appid_entries_string)

    # Attempt to populate the package_identifier field by checking each of
    # these fields in the AppId JSON.
    package_id_locations = [
        'packageId', 'x_exe_path', 'windows_win32', 'windows_universal',
        'alternateId']
    for location in package_id_locations:
      for entry in appid_entries:
        if entry['platform'] == location and entry['application'] != '':
          event_data.package_identifier = entry['application']
          break
      if event_data.package_identifier is None:
        # package_identifier has been populated and we're done.
        break

    if 'description' in payload:
      event_data.description = payload['description']
    else:
      event_data.description = ''

    if 'appDisplayName' in payload and payload['appDisplayName'] != '':
      event_data.application_display_name = payload['appDisplayName']
    elif 'displayText' in payload and payload['displayText'] != '':
      # Fall back to displayText if appDisplayName isn't available
      event_data.application_display_name = payload['displayText']

    timestamp = self._GetRowValue(query_hash, row, 'StartTime')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_START)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseUserEngagedRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a timeline row that describes a user interacting with an app.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = WindowsTimelineUserEngagedEventData()
    event_data.package_identifier = self._GetRowValue(
        query_hash, row, 'PackageName')

    # Payload is JSON serialized as binary data in a BLOB field, with the text
    # encoded as UTF-8.
    payload_json_bytes = bytes(self._GetRowValue(query_hash, row, 'Payload'))
    payload_json_string = payload_json_bytes.decode('utf-8')
    payload = json.loads(payload_json_string)

    if 'reportingApp' in payload:
      event_data.reporting_app = payload['reportingApp']
    if 'activeDurationSeconds' in payload:
      event_data.active_duration_seconds = int(payload['activeDurationSeconds'])

    timestamp = self._GetRowValue(query_hash, row, 'StartTime')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_START)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(WindowsTimelinePlugin)
