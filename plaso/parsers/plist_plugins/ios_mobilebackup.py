# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple iOS Mobile Backup plist files.

The plist contains history of opened applications in the Mobile Backup.
"""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSMobileBackupEventData(events.EventData):
  """Apple iOS Mobile Backup event data.

  Attributes:
    account_enabled_time (dfdatetime.DateTimeValues): date and time the mobile
        backup account was enabled.
    backup_state_time (dfdatetime.DateTimeValues): date and time if the backup
        state.
    backup_state (int): backup state.
  """

  DATA_TYPE = 'ios:mobile_backup:entry'

  def __init__(self):
    """Initializes event data."""
    super(IOSMobileBackupEventData, self).__init__(data_type=self.DATA_TYPE)
    self.account_enabled_time = None
    self.backup_state = None
    self.backup_state_time = None


class IOSMobileBackupStateEventData(events.EventData):
  """Apple iOS Mobile Backup state event data.

  Attributes:
    backup_time (dfdatetime.DateTimeValues): date and time of the backup.
    description (str): localized description of the backup state.
  """

  DATA_TYPE = 'ios:mobile_backup:state'

  def __init__(self):
    """Initializes event data."""
    super(IOSMobileBackupStateEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.backup_time = None
    self.description = None


class IOSMobileBackupPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Apple iOS Mobile Backup plist files."""

  NAME = 'ios_mobile_backup'
  DATA_FORMAT = 'Apple iOS Mobile Backup plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.MobileBackup.plist')])

  PLIST_KEYS = frozenset(['AccountEnabledDate', 'BackupStateInfo'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extract Mobile Backup history entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    event_data = IOSMobileBackupEventData()
    event_data.account_enabled_time = self._GetDateTimeValueFromPlistKey(
        top_level, 'AccountEnabledDate')

    # TODO: add support for LastOnConditionEvents
    # TODO: add support for RemoteConfigurationExpiration

    backup_state_info = top_level.get('BackupStateInfo')
    if backup_state_info:
      event_data.backup_state = backup_state_info.get('state')
      # TODO: determine what this time represents.
      event_data.backup_state_time = self._GetDateTimeValueFromPlistKey(
          backup_state_info, 'date')

    parser_mediator.ProduceEventData(event_data)

    if backup_state_info:
      for error in backup_state_info.get('errors', []):
        event_data = IOSMobileBackupStateEventData()
        event_data.description = error.get('localizedDescription')
        # TODO: determine if this is the start or end time of the backup.
        event_data.backup_time = self._GetDateTimeValueFromPlistKey(
            error, 'date')

        parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(IOSMobileBackupPlistPlugin)
