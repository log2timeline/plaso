# -*- coding: utf-8 -*-
"""The timeliner, which is used to generate events from event data."""

import collections
import datetime
import os
import pytz

from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import warnings
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

  def __init__(self, knowledge_base, data_location=None, preferred_year=None):
    """Initializes an event data timeliner.

    Args:
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for generation of the time line.
      data_location (Optional[str]): path of the timeliner configuration file.
      preferred_year (Optional[int]): preferred initial year value for year-less
          date and time values.
    """
    super(EventDataTimeliner, self).__init__()
    self._attribute_mappings = {}
    self._data_location = data_location
    self._knowledge_base = knowledge_base
    self._place_holder_event = set()
    self._preferred_year = preferred_year
    self._time_zone = None

    self.number_of_produced_events = 0
    self.parsers_counter = collections.Counter()

    self._ReadConfigurationFile()

  def _GetEvent(
      self, date_time, date_time_description, event_data_identifier, base_year):
    """Retrieves an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date and
          time values.
      event_data_identifier (AttributeContainerIdentifier): attribute container
          identifier of the event data.
      base_year (int): base year of a date time delta.

    Returns:
      EventObject: event.
    """
    if date_time.is_delta and base_year:
      date_time = date_time.NewFromDeltaAndYear(base_year)

    timestamp = date_time.GetPlasoTimestamp()
    if (date_time.is_local_time and self._time_zone and
        self._time_zone != pytz.UTC):
      datetime_object = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=None)
      datetime_object += datetime.timedelta(microseconds=timestamp)

      datetime_delta = self._time_zone.utcoffset(datetime_object, is_dst=False)
      seconds_delta = int(datetime_delta.total_seconds())
      timestamp -= seconds_delta * definitions.MICROSECONDS_PER_SECOND

      date_time.is_local_time = False
      date_time.time_zone_offset = seconds_delta // 60

    event = events.EventObject()
    event.date_time = date_time
    event.timestamp = timestamp
    event.timestamp_desc = date_time_description

    event.SetEventDataIdentifier(event_data_identifier)

    return event

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

      if timeliner_definition.place_holder_event:
        self._place_holder_event.add(timeliner_definition.data_type)

  def _ProducTimeliningWarning(self, storage_writer, event_data, message):
    """Produces a timelining warning.

    Args:
      storage_writer (StorageWriter): storage writer.
      event_data (EventData): event data.
      message (str): message of the warning.
    """
    parser_chain = event_data.parser
    path_spec = None

    event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
    if event_data_stream_identifier:
      event_data_stream = storage_writer.GetAttributeContainerByIdentifier(
          events.EventDataStream.CONTAINER_TYPE, event_data_stream_identifier)
      if event_data_stream:
        path_spec = event_data_stream.path_spec

    warning = warnings.TimeliningWarning(
        message=message, parser_chain=parser_chain, path_spec=path_spec)
    storage_writer.AddAttributeContainer(warning)

  def ProcessEventData(self, storage_writer, event_data):
    """Generate events from event data.

    Args:
      storage_writer (StorageWriter): storage writer.
      event_data (EventData): event data.
    """
    self.number_of_produced_events = 0

    attribute_mappings = self._attribute_mappings.get(event_data.data_type)
    if not attribute_mappings:
      return

    event_data_identifier = event_data.GetIdentifier()

    # If preferred year is set considered it a user override, otherwise try
    # to determine the year based on the file entry or fallback to the current
    # year.

    base_year = self._preferred_year
    if not base_year:
      event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
      if event_data_stream_identifier:
        lookup_key = event_data_stream_identifier.CopyToString()
        filter_expression = '_event_data_stream_identifier == "{0:s}"'.format(
            lookup_key)
        year_less_log_helpers = list(storage_writer.GetAttributeContainers(
            events.YearLessLogHelper.CONTAINER_TYPE,
            filter_expression=filter_expression))
        if year_less_log_helpers:
          base_year = year_less_log_helpers[0].estimated_creation_year

      # TODO: use relative_year to determine base_year

    # TODO: fallback to current year

    if event_data.parser:
      parser_name = event_data.parser.rsplit('/', maxsplit=1)[-1]
    else:
      parser_name = None

    number_of_events = 0
    for attribute_name, time_description in attribute_mappings.items():
      attribute_values = getattr(event_data, attribute_name, None) or []
      if not isinstance(attribute_values, list):
        attribute_values = [attribute_values]

      for attribute_value in attribute_values:
        try:
          event = self._GetEvent(
              attribute_value, time_description, event_data_identifier,
              base_year)

        except ValueError as exception:
          self._ProducTimeliningWarning(
              storage_writer, event_data, str(exception))
          continue

        storage_writer.AddAttributeContainer(event)

        number_of_events += 1

        if parser_name:
          self.parsers_counter[parser_name] += 1
        self.parsers_counter['total'] += 1

        self.number_of_produced_events += 1

    # Create a place holder event for event_data without date and time
    # values to map.
    if (not number_of_events and
        event_data.data_type in self._place_holder_event):
      date_time = dfdatetime_semantic_time.NotSet()
      event = self._GetEvent(
          date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME,
          event_data_identifier, base_year)

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
