# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the CCleaner Registry key.

Also see:
  https://winreg-kb.readthedocs.io/en/latest/sources/application-keys/CCleaner.html
"""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class CCleanerConfigurationEventData(events.EventData):
  """CCleaner configuration event data.

  Attributes:
    configuration (str): CCleaner configuration.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'ccleaner:configuration'

  def __init__(self):
    """Initializes event data."""
    super(CCleanerConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.configuration = None
    self.key_path = None
    self.last_written_time = None


class CCleanerUpdateEventData(events.EventData):
  """CCleaner update event data.

  Attributes:
    key_path (str): Windows Registry key path.
    update_time (dfdatetime.DateTimeValues): date and time CCleaner last
        checked for an update.
  """

  DATA_TYPE = 'ccleaner:update'

  def __init__(self):
    """Initializes event data."""
    super(CCleanerUpdateEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    self.update_time = None


class CCleanerPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin to parse the CCleaner Registry key."""

  NAME = 'ccleaner'
  DATA_FORMAT = 'CCleaner Registry data'

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
          and other components, such as storage and dfVFS.
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
          and other components, such as storage and dfVFS.
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
      event_data.update_time = date_time

      parser_mediator.ProduceEventData(event_data)

    event_data = CCleanerConfigurationEventData()
    event_data.configuration = ' '.join(sorted(configuration)) or None
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(CCleanerPlugin)
