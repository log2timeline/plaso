# -*- coding: utf-8 -*-
"""Parser for the CCleaner Registry key."""

from __future__ import unicode_literals

import re

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class CCleanerConfigurationEventData(events.EventData):
  """CCleaner configuration event data.

  Attributes:
    configuration (str): CCleaner configuration.
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = 'ccleaner:configuration'

  def __init__(self):
    """Initializes event data."""
    super(CCleanerConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.configuration = None
    self.key_path = None


class CCleanerUpdateEventData(events.EventData):
  """CCleaner update event data.

  Attributes:
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = 'ccleaner:update'

  def __init__(self):
    """Initializes event data."""
    super(CCleanerUpdateEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None


class CCleanerPlugin(interface.WindowsRegistryPlugin):
  """Gathers the CCleaner Keys for NTUSER hive.

  Known Windows Registry values within the CCleaner key:
  * (App)Cookies [REG_SZ], contains "True" if the cookies should be cleaned;
  * (App)Delete Index.dat files [REG_SZ]
  * (App)History [REG_SZ]
  * (App)Last Download Location [REG_SZ]
  * (App)Other Explorer MRUs [REG_SZ]
  * (App)Recent Documents [REG_SZ]
  * (App)Recently Typed URLs [REG_SZ]
  * (App)Run (in Start Menu) [REG_SZ]
  * (App)Temporary Internet Files [REG_SZ]
  * (App)Thumbnail Cache [REG_SZ]
  * CookiesToSave [REG_SZ]
  * UpdateKey [REG_SZ], contains a date and time formatted as:
      "MM/DD/YYYY hh:mm:ss [A|P]M", for example "07/13/2013 10:03:14 AM";
  * WINDOW_HEIGHT [REG_SZ], contains the windows height in number of pixels;
  * WINDOW_LEFT [REG_SZ]
  * WINDOW_MAX [REG_SZ]
  * WINDOW_TOP [REG_SZ]
  * WINDOW_WIDTH [REG_SZ], contains the windows width in number of pixels;

  Also see:
  http://cheeky4n6monkey.blogspot.com/2012/02/writing-ccleaner-regripper-plugin-part_05.html
  """

  NAME = 'ccleaner'
  DESCRIPTION = 'Parser for CCleaner Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner')])

  # Date and time string formatted as: "MM/DD/YYYY hh:mm:ss [A|P]M"
  # for example "07/13/2013 10:03:14 AM"
  # TODO: determine if this is true for other locales.
  _UPDATE_DATE_TIME_RE = re.compile(
      r'([0-9][0-9])/([0-9][0-9])/([0-9][0-9][0-9][0-9]) '
      r'([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([A|P]M)')

  def _ParseUpdateKeyValue(self, parser_mediator, registry_value):
    """Parses the UpdateKey value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_value (dfwinreg.WinRegistryValue): Windows Registry value.

    Returns:
      dfdatetime_time_elements.TimeElements: date and time value or None
          if not available.
    """
    if not registry_value.DataIsString():
      parser_mediator.ProduceExtractionWarning(
          'unsupported UpdateKey value data type: {0:s}'.format(
              registry_value.data_type_string))
      return None

    date_time_string = registry_value.GetDataAsObject()
    if not date_time_string:
      parser_mediator.ProduceExtractionWarning('missing UpdateKey value data')
      return None

    re_match = self._UPDATE_DATE_TIME_RE.match(date_time_string)
    if not re_match:
      parser_mediator.ProduceExtractionWarning(
          'unsupported UpdateKey value data: {0!s}'.format(date_time_string))
      return None

    month, day_of_month, year, hours, minutes, seconds, part_of_day = (
        re_match.groups())

    try:
      year = int(year, 10)
      month = int(month, 10)
      day_of_month = int(day_of_month, 10)
      hours = int(hours, 10)
      minutes = int(minutes, 10)
      seconds = int(seconds, 10)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'invalid UpdateKey date time value: {0!s}'.format(date_time_string))
      return None

    if part_of_day == 'PM':
      hours += 12

    time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid UpdateKey date time value: {0!s}'.format(
              time_elements_tuple))
      return None

    return date_time

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    configuration = []
    date_time = None

    for registry_value in registry_key.GetValues():
      if not registry_value.name or not registry_value.data:
        continue

      if registry_value.name == 'UpdateKey':
        date_time = self._ParseUpdateKeyValue(parser_mediator, registry_value)
      else:
        value = registry_value.GetDataAsObject()
        configuration.append('{0:s}: {1!s}'.format(registry_value.name, value))

    if date_time:
      event_data = CCleanerUpdateEventData()
      event_data.key_path = registry_key.path

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_UPDATE,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    event_data = CCleanerConfigurationEventData()
    event_data.configuration = ' '.join(sorted(configuration)) or None
    event_data.key_path = registry_key.path

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(CCleanerPlugin)
