# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple iOS Mobile Backup plist files.

The plist contains history of opened applications in the Mobile Backup.
"""

from dfdatetime import posix_time as dfdatetime_posix_time
import datetime

from plaso.containers import events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class IOSMobileBackupEventData(events.EventData):
  """Apple iOS Mobile Backup history event data.

  Attributes:
    activity_description (str): activity description.
    activity_time (dfdatetime.DateTimeValues): activity last run date and
        time.
  """

  DATA_TYPE = 'ios:mobile:backup:entry'

  def __init__(self):
    """Initializes event data."""
    super(IOSMobileBackupEventData, self).__init__(data_type=self.DATA_TYPE)
    self.activity_description = None
    self.activity_time = None


class IOSMobileBackupPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for Apple iOS Mobile Backup plist files."""

  NAME = 'ios_mobilebackup'
  DATA_FORMAT = 'Apple iOS Mobile Backup plist file'

  PLIST_PATH_FILTERS = frozenset([
      interface.PlistPathFilter('com.apple.MobileBackup.plist')])

  PLIST_KEYS = frozenset(['AccountEnabledDate','BackupStateInfo'])

  def _getEventData(self, description, datetime_value):
    event_data = IOSMobileBackupEventData()
    event_data.activity_description = description
    timestamp = datetime.datetime.timestamp(datetime_value)
    timestamp = int(timestamp * definitions.NANOSECONDS_PER_SECOND)
    event_data.activity_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
        timestamp=timestamp)
    
    return event_data

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
    """Extract Mobile Backup history entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """

    datetime_value = match.get('AccountEnabledDate', {})
    parser_mediator.ProduceEventData(self._getEventData("AccountEnabledDate", datetime_value))

    plist_key = match.get('BackupStateInfo', {})
    for key, value in plist_key.items():
      if key == "date":
        parser_mediator.ProduceEventData(self._getEventData(f"BackupStateInfo - date", value))

      elif key == "errors":
        for val in value:
          parser_mediator.ProduceEventData(self._getEventData(f"BackupStateInfo - {val['localizedDescription']}", val['date']))

plist.PlistParser.RegisterPlugin(IOSMobileBackupPlistPlugin)
