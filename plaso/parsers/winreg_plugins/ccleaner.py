# -*- coding: utf-8 -*-
"""Parser for the CCleaner Registry key."""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerUpdateEventData(events.EventData):
  """CCleaner update event data.

  Attributes:
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = u'ccleaner:update'

  def __init__(self):
    """Initializes event data."""
    super(CCleanerUpdateEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None


class CCleanerPlugin(interface.WindowsRegistryPlugin):
  """Gathers the CCleaner Keys for NTUSER hive."""

  NAME = u'ccleaner'
  DESCRIPTION = u'Parser for CCleaner Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner')])

  URLS = [(u'http://cheeky4n6monkey.blogspot.com/2012/02/writing-ccleaner'
           u'-regripper-plugin-part_05.html')]

  _SOURCE_APPEND = u': CCleaner Registry key'

  # Date and time string in the form: MM/DD/YYYY hh:mm:ss [A|P]M
  # e.g. 07/13/2013 10:03:14 AM
  # TODO: determine if this is true for other locales.
  _UPDATE_DATE_TIME_RE = re.compile(
      r'([0-9][0-9])/([0-9][0-9])/([0-9][0-9][0-9][0-9]) '
      r'([0-9][0-9]):([0-9][0-9]):([0-9][0-9]) ([A|P]M)')

  def _ParseUpdateKeyValue(self, parser_mediator, registry_value, key_path):
    """Parses the UpdateKey value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_value (dfwinreg.WinRegistryValue): Windows Registry value.
      key_path (str): Windows Registry key path.
    """
    if not registry_value.DataIsString():
      parser_mediator.ProduceExtractionError(
          u'unsupported UpdateKey value data type: {0:s}'.format(
              registry_value.data_type_string))
      return

    date_time_string = registry_value.GetDataAsObject()
    if not date_time_string:
      parser_mediator.ProduceExtractionError(u'missing UpdateKey value data')
      return

    re_match = self._UPDATE_DATE_TIME_RE.match(date_time_string)
    if not re_match:
      parser_mediator.ProduceExtractionError(
          u'unsupported UpdateKey value data: {0!s}'.format(date_time_string))
      return

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
      parser_mediator.ProduceExtractionError(
          u'invalid UpdateKey date time value: {0!s}'.format(date_time_string))
      return

    if part_of_day == u'PM':
      hours += 12

    time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'invalid UpdateKey date time value: {0!s}'.format(
              time_elements_tuple))
      return

    event_data = CCleanerUpdateEventData()
    event_data.key_path = key_path

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_UPDATE,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}
    for registry_value in registry_key.GetValues():
      if not registry_value.name or not registry_value.data:
        continue

      if registry_value.name == u'UpdateKey':
        self._ParseUpdateKeyValue(
            parser_mediator, registry_value, registry_key.path)
      else:
        values_dict[registry_value.name] = registry_value.GetDataAsObject()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND
    event_data.urls = self.URLS

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(CCleanerPlugin)
