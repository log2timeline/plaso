# -*- coding: utf-8 -*-
"""The timeliner, which is used to generate events from event data."""

import collections
import os
import pytz

from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import time_events
from plaso.engine import yaml_timeliner_file
from plaso.lib import definitions


class EventDataTimeliner(object):
  """The event data timeliner.

  Attributes:
    number_of_produced_events (int): number of produced events.
    parsers_counter (collections.Counter): number of events per parser or
        parser plugin.
  """

  _DEFAULT_TIME_ZONE = pytz.UTC

  _TIMELINER_CONFIGURATION_FILENAME = 'timeliner.yaml'

  def __init__(self, knowledge_base, data_location=None):
    """Initializes an event data timeliner.

    Args:
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for generation of the time line.
      data_location (Optional[str]): path of the timeliner configuration file.
    """
    super(EventDataTimeliner, self).__init__()
    self._attribute_mappings = {}
    self._data_location = data_location
    self._knowledge_base = knowledge_base
    self._time_zone = None

    self.number_of_produced_events = 0
    self.parsers_counter = collections.Counter()

    self._ReadConfigurationFile()

  def _ReadConfigurationFile(self):
    """Reads a timeliner configuration file.

    Raises:
      KeyError: if the attribute mappings are already set for the corresponding
          data type.
    """
    path = os.path.join(
        self._data_location, self._TIMELINER_CONFIGURATION_FILENAME)

    configuration_file = yaml_timeliner_file.YAMLTimelinerConfigurationFile()
    for timeliner_definition in configuration_file.ReadFromFile(path):
      if timeliner_definition.data_type in self._attribute_mappings:
        raise KeyError(
            'Attribute mappings for data type: {0:s} already set.'.format(
                timeliner_definition.data_type))

      self._attribute_mappings[timeliner_definition.data_type] = (
          timeliner_definition.attribute_mappings)

  def ProcessEventData(self, storage_writer, event_data):
    """Generate events from event data.

    Args:
      storage_writer (StorageWriter): storage writer.
      event_data (EventData): event data.
    """
    attribute_mappings = self._attribute_mappings.get(event_data.data_type)
    if not attribute_mappings:
      return

    event_data_identifier = event_data.GetIdentifier()

    if event_data.parser:
      parser_name = event_data.parser.rsplit('/', maxsplit=1)[-1]
    else:
      parser_name = None

    number_of_events = 0
    for attribute_name, time_description in attribute_mappings.items():
      attribute_value = getattr(event_data, attribute_name, None)
      if attribute_value:
        event = time_events.DateTimeValuesEvent(
            attribute_value, time_description, time_zone=self._time_zone)
        event.SetEventDataIdentifier(event_data_identifier)

        storage_writer.AddAttributeContainer(event)

        number_of_events += 1

        if parser_name:
          self.parsers_counter[parser_name] += 1
        self.parsers_counter['total'] += 1

        self.number_of_produced_events += 1

    # Create a place holder event for event_data without date and time
    # values to map.
    # TODO: add extraction option to control this behavior.
    if not number_of_events:
      date_time = dfdatetime_semantic_time.NotSet()
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
      event.SetEventDataIdentifier(event_data_identifier)

      storage_writer.AddAttributeContainer(event)

      if parser_name:
        self.parsers_counter[parser_name] += 1
      self.parsers_counter['total'] += 1

      self.number_of_produced_events += 1

  def SetPreferredTimeZone(self, time_zone_string):
    """Sets the preferred time zone for zone-less date and time values.

    Args:
      time_zone_string (str): time zone such as "Europe/Amsterdam" or None if
          the time zone determined by preprocessing or the default should be
          used.

    Raises:
      ValueError: if the time zone is not supported.
    """
    self._time_zone = None

    if time_zone_string:
      try:
        self._time_zone = pytz.timezone(time_zone_string)
      except pytz.UnknownTimeZoneError:
        raise ValueError('Unsupported time zone: {0!s}'.format(
            time_zone_string))

    if not self._time_zone:
      self._time_zone = self._knowledge_base.timezone or self._DEFAULT_TIME_ZONE
