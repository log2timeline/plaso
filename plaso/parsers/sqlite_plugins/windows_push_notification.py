# -*- coding: utf-8 -*-
"""SQLite parser plugin for Windows 10 push notification database files."""

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class WindowsPushNotificationEventData(events.EventData):
  """Windows push notification event data.

  Attributes:
    arrival_time (dfdatetime.DateTimeValues): date and time the push
        notification was received.
    boot_time (dfdatetime.DateTimeValues): date and time the of the last boot.
    expiration_time (dfdatetime.DateTimeValues): date and time the push
        notification expires.
    handler_identifier (str): identifier of the corresponding notification
        handler.
    notification_type (str): notification type.
    payload (dfdatetime.DateTimeValues): payload.
  """

  DATA_TYPE = 'windows:wpndatabase:notification'

  def __init__(self):
    """Initialize event data."""
    super(WindowsPushNotificationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.arrival_time = None
    self.boot_time = None
    self.expiration_time = None
    self.handler_identifier = None
    self.notification_type = None
    self.payload = None


class WindowsPushNotificationHandlerEventData(events.EventData):
  """Windows push notification handler event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): date and time the push
        notification handler was created.
    handler_type (str): handler type.
    identifier (str): identifier.
    modification_time (dfdatetime.DateTimeValues): date and time the push
        notification handler was last modified.
    service_identifier (str): Windows Push Notification Service (WNS)
        identifier.
  """

  DATA_TYPE = 'windows:wpndatabase:notification_handler'

  def __init__(self):
    """Initialize event data."""
    super(WindowsPushNotificationHandlerEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.creation_time = None
    self.handler_type = None
    self.identifier = None
    self.modification_time = None
    self.service_identifier = None


class WindowsPushNotificationPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Windows 10 push notification database files.

  The Windows 10 push notification database file is typically stored in:
  %APPDATA%\\Local\\Microsoft\\Windows\\Notifications\\wpndatabase.db
  """

  NAME = 'windows_push_notification'
  DATA_FORMAT = (
      'Windows 10 push notification SQLite database (wpndatabase.db) file')

  REQUIRED_STRUCTURE = {
      'Metadata': frozenset([
          'Key', 'Value']),
      'Notification': frozenset([
          'ActivityId', 'ArrivalTime', 'BootId', 'DataVersion',
          'ExpiresOnReboot', 'ExpiryTime', 'HandlerId', 'Group', 'Id',
          'Order', 'Payload', 'PayloadType', 'Tag', 'Type']),
      'NotificationHandler': frozenset([
          'ContainerSid', 'CreatedTime', 'HandlerType', 'ModifiedTime',
          'ParentId', 'PrimaryId', 'RecordId', 'SystemDataPropertySet',
          'WNFEventName', 'WNSId'])}

  QUERIES = [
      (('SELECT RecordId, PrimaryId, WNSId, HandlerType, WNFEventName, '
        'SystemDataPropertySet, CreatedTime, ModifiedTime, ParentId, '
        'ContainerSid FROM NotificationHandler'),
       'ParseNotificationHandlerRow'),
      # Note that Order and Group must be escaped other they are interpreted
      # as SQL keywords.
      (('SELECT "Order", Id, ActivityId, Type, Payload, Tag, "Group", '
        'ExpiryTime, ArrivalTime, DataVersion, PayloadType, BootId, '
        'ExpiresOnReboot, PrimaryId FROM Notification, NotificationHandler '
        'WHERE Notification.HandlerId == NotificationHandler.RecordId'),
       'ParseNotificationRow')]

  SCHEMAS = [{
      'HandlerAssets': (
          'CREATE TABLE [HandlerAssets]( [HandlerId] INTEGER '
          'CONSTRAINT[AssetsToHandler] '
          'REFERENCES[NotificationHandler]([RecordId]) ON DELETE CASCADE ON '
          'UPDATE CASCADE, [AssetKey] TEXT NOT NULL, [AssetValue] TEXT, '
          'CONSTRAINT[] PRIMARY KEY([AssetKey], [HandlerId]) ON CONFLICT '
          'REPLACE)'),
      'HandlerSettings': (
          'CREATE TABLE [HandlerSettings]( [HandlerId] INTEGER '
          'CONSTRAINT[SettingsToHandler] '
          'REFERENCES[NotificationHandler]([RecordId]) ON DELETE CASCADE ON '
          'UPDATE CASCADE, [SettingKey] TEXT NOT NULL, [Value] INT, '
          'CONSTRAINT[] PRIMARY KEY([SettingKey], [HandlerId]) ON CONFLICT '
          'REPLACE)'),
      'Metadata': (
          'CREATE TABLE [Metadata]( [Key] TEXT, [Value] INT64, CONSTRAINT[] '
          'PRIMARY KEY([Key]) ON CONFLICT REPLACE)'),
      'Notification': (
          'CREATE TABLE [Notification]( [Order] INTEGER NOT NULL PRIMARY KEY, '
          '[Id] INTEGER NOT NULL, [HandlerId] INTEGER '
          'CONSTRAINT[NotificationToHandler] '
          'REFERENCES[NotificationHandler]([RecordId]) ON DELETE CASCADE ON '
          'UPDATE CASCADE, [ActivityId] GUID,[Type] TEXT NOT NULL, [Payload] '
          'BLOB, [Tag] TEXT, [Group] TEXT, [ExpiryTime] INT64, [ArrivalTime] '
          'INT64, [DataVersion] INT64 DEFAULT \'0\', [PayloadType] TEXT NOT '
          'NULL, [BootId] INT64 DEFAULT \'0\', [ExpiresOnReboot] BOOLEAN '
          'DEFAULT \'FALSE\', UNIQUE([Id]) ON CONFLICT REPLACE)'),
      'NotificationData': (
          'CREATE TABLE [NotificationData]( [NotificationId] INTEGER '
          'CONSTRAINT[DataToNotification] REFERENCES[Notification]([Id]) ON '
          'DELETE CASCADE ON UPDATE CASCADE, [Key] TEXT NOT NULL, [Value] '
          'TEXT, CONSTRAINT[] PRIMARY KEY([Key], [NotificationId]) ON '
          'CONFLICT REPLACE)'),
      'NotificationHandler': (
          'CREATE TABLE [NotificationHandler] ( [RecordId] INTEGER PRIMARY '
          'KEY, [PrimaryId] TEXT NOT NULL COLLATE NOCASE, [WNSId] TEXT '
          'COLLATE NOCASE, [HandlerType] TEXT, [WNFEventName] INT64, '
          '[SystemDataPropertySet] BLOB, [CreatedTime] DATETIME, '
          '[ModifiedTime] DATETIME, [ParentId] TEXT COLLATE NOCASE, '
          '[ContainerSid] TEXT COLLATE NOCASE)'),
      'TransientTable': (
          'CREATE TABLE [TransientTable]( [OfflineCacheCount] INTEGER, '
          '[NotificationId] INTEGER CONSTRAINT[TransientToNotification] '
          'REFERENCES[Notification]([Id]) ON DELETE CASCADE ON UPDATE '
          'CASCADE, [OfflineBundleId] TEXT, [ServerCacheRollover] BOOLEAN '
          'DEFAULT \'FALSE\', [CrossDeviceMatchId] TEXT, [SuppressPopup] '
          'BOOLEAN DEFAULT \'FALSE\', [IsMirroringDisabled] BOOLEAN DEFAULT '
          '\'FALSE\', [RecurrenceId] GUID, [MessageId] GUID, [Priority] '
          'INTEGER NOT NULL, [CV] TEXT)'),
      'WNSPushChannel': (
          'CREATE TABLE [WNSPushChannel]( [ChannelId] TEXT NOT NULL, '
          '[HandlerId] INTEGER REFERENCES[NotificationHandler]([RecordId]) ON '
          'DELETE CASCADE ON UPDATE CASCADE, [Uri] TEXT, [ExpiryTime] INT64, '
          '[CreatedTime] INT64, [DeviceVersion] INT64 DEFAULT \'0\', '
          'CONSTRAINT[] PRIMARY KEY([ChannelId]) ON CONFLICT REPLACE)')}]

  def ParseNotificationHandlerRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row of the NotificationHandler table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = WindowsPushNotificationHandlerEventData()
    event_data.creation_time = self._GetDateTimeStringRowValue(
        query_hash, row, 'CreatedTime')
    event_data.handler_type = self._GetRowValue(query_hash, row, 'HandlerType')
    event_data.identifier = self._GetRowValue(query_hash, row, 'PrimaryId')
    event_data.modification_time = self._GetDateTimeStringRowValue(
        query_hash, row, 'ModifiedTime')
    event_data.service_identifier = self._GetRowValue(query_hash, row, 'WNSId')

    # TODO: add support for WNFEventName

    parser_mediator.ProduceEventData(event_data)

  def ParseNotificationRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row of the Notification table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    payload = None
    payload_type = self._GetRowValue(query_hash, row, 'PayloadType')

    if payload_type.lower() == 'xml':
      payload = self._GetRowValue(query_hash, row, 'Payload')
      payload = payload.decode('utf-8')
      # TODO: parse payload
    else:
      parser_mediator.ProduceExtractionWarning(
          f'unsupported payload type: {payload_type:s}')

    event_data = WindowsPushNotificationEventData()
    event_data.arrival_time = self._GeFiletimeRowValue(
        query_hash, row, 'ArrivalTime')
    event_data.boot_time = self._GeFiletimeRowValue(
        query_hash, row, 'BootId')
    event_data.expiration_time = self._GeFiletimeRowValue(
        query_hash, row, 'ExpiryTime')
    event_data.handler_identifier = self._GetRowValue(
        query_hash, row, 'PrimaryId')
    event_data.notification_type = self._GetRowValue(query_hash, row, 'Type')
    event_data.payload = payload

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(WindowsPushNotificationPlugin)
