# -*- coding: utf-8 -*-
"""The timeliner, which is used to generate events from event data."""

import collections
import copy
import datetime
import os
import pytz

from dfdatetime import interface as dfdatetime_interface
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

  _INT64_MIN = -1 << 63
  _INT64_MAX = (1 << 63) - 1

  _TIMELINER_CONFIGURATION_FILENAME = 'timeliner.yaml'

  def __init__(
      self, data_location=None, preferred_year=None,
      system_configurations=None):
    """Initializes an event data timeliner.

    Args:
      data_location (Optional[str]): path of the timeliner configuration file.
      preferred_year (Optional[int]): preferred initial year value for year-less
          date and time values.
      system_configurations (Optional[list[SystemConfigurationArtifact]]):
          system configurations.
    """
    super(EventDataTimeliner, self).__init__()
    self._attribute_mappings = {}
    self._base_years = {}
    self._current_year = self._GetCurrentYear()
    self._data_location = data_location
    self._place_holder_event = set()
    self._preferred_time_zone = None
    self._preferred_year = preferred_year
    self._time_zone_per_path_spec = None

    self.number_of_produced_events = 0
    self.parsers_counter = collections.Counter()

    self._CreateTimeZonePerPathSpec(system_configurations)
    self._ReadConfigurationFile()

  def _CreateTimeZonePerPathSpec(self, system_configurations):
    """Creates the time zone per path specification lookup table.

    Args:
      system_configurations (list[SystemConfigurationArtifact]): system
          configurations.
    """
    self._time_zone_per_path_spec = {}
    for system_configuration in system_configurations or []:
      if system_configuration.time_zone:
        for path_spec in system_configuration.path_specs:
          if path_spec.parent:
            self._time_zone_per_path_spec[path_spec.parent] = (
                system_configuration.time_zone)

  def _GetBaseYear(self, storage_writer, event_data):
    """Retrieves the base year.

    Args:
      storage_writer (StorageWriter): storage writer.
      event_data (EventData): event data.

    Returns:
      int: base year.
    """
    # If preferred year is set considered it a user override, otherwise try
    # to determine the year based on the year-less log helper or fallback to
    # the current year.

    if self._preferred_year:
      return self._preferred_year

    event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
    if not event_data_stream_identifier:
      return self._current_year

    lookup_key = event_data_stream_identifier.CopyToString()

    base_year = self._base_years.get(lookup_key, None)
    if base_year:
      return base_year

    filter_expression = '_event_data_stream_identifier == "{0:s}"'.format(
        lookup_key)
    year_less_log_helpers = list(storage_writer.GetAttributeContainers(
        events.YearLessLogHelper.CONTAINER_TYPE,
        filter_expression=filter_expression))
    if not year_less_log_helpers:
      message = (
          'missing year-less log helper, defaulting to current year: '
          '{0:d}').format(self._current_year)
      self._ProduceTimeliningWarning(storage_writer, event_data, message)

      base_year = self._current_year

    else:
      earliest_year = year_less_log_helpers[0].earliest_year
      last_relative_year = year_less_log_helpers[0].last_relative_year
      latest_year = year_less_log_helpers[0].latest_year

      if earliest_year is None and latest_year is None:
        message = (
            'missing earliest and latest year in year-less log helper, '
            'defaulting to current year: {0:d}').format(self._current_year)
        self._ProduceTimeliningWarning(storage_writer, event_data, message)

        base_year = self._current_year

      elif earliest_year + last_relative_year < self._current_year:
        base_year = earliest_year

      elif latest_year < self._current_year:
        message = (
            'earliest year: {0:d} as base year would exceed current year: '
            '{1:d} + {2:d}, using latest year: {3:d}').format(
                earliest_year, self._current_year, last_relative_year,
                latest_year)
        self._ProduceTimeliningWarning(storage_writer, event_data, message)

        base_year = latest_year - last_relative_year

      else:
        message = (
            'earliest year: {0:d} and latest: year: {1:d} as base year '
            'would exceed current year: {2:d} + {3:d}, using current '
            'year').format(
                earliest_year, latest_year, self._current_year,
                last_relative_year)
        self._ProduceTimeliningWarning(storage_writer, event_data, message)

        base_year = self._current_year - last_relative_year

    self._base_years[lookup_key] = base_year

    return base_year

  def _GetCurrentYear(self):
    """Retrieves current year.

    Returns:
      int: the current year.
    """
    datetime_object = datetime.datetime.now()
    return datetime_object.year

  def _GetEvent(
      self, storage_writer, event_data, event_data_stream, date_time,
      date_time_description):
    """Retrieves an event.

    Args:
      storage_writer (StorageWriter): storage writer.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date and
          time values.

    Returns:
      EventObject: event.
    """
    if date_time.is_delta:
      base_year = self._GetBaseYear(storage_writer, event_data)
      date_time = date_time.NewFromDeltaAndYear(base_year)

    timestamp = date_time.GetPlasoTimestamp()
    if timestamp is None:
      self._ProduceTimeliningWarning(
          storage_writer, event_data, 'unable to determine timestamp')

      date_time = dfdatetime_semantic_time.InvalidTime()
      timestamp = 0

    # Check for out of bounds timestamps, for example if a data format has
    # changed and the conversion leads to an incorrect large integer value.
    # Integer values that are larger than 64-bit will cause an OverflowError
    # in the SQLite storage.

    elif timestamp < self._INT64_MIN or timestamp > self._INT64_MAX:
      self._ProduceTimeliningWarning(
          storage_writer, event_data, 'timestamp out of bounds')

      date_time = dfdatetime_semantic_time.InvalidTime()
      timestamp = 0

    else:
      if date_time.is_local_time:
        time_zone = None
        if date_time.time_zone_hint:
          # TODO: cache time zones per hint.
          try:
            time_zone = pytz.timezone(date_time.time_zone_hint)
          except pytz.UnknownTimeZoneError:
            message = (
                'unsupported time zone hint: {0:s}, using default time '
                'zone').format(date_time.time_zone_hint)
            self._ProduceTimeliningWarning(storage_writer, event_data, message)

        if not time_zone and event_data_stream:
          try:
            time_zone = self._GetTimeZoneByPathSpec(event_data_stream.path_spec)
          except pytz.UnknownTimeZoneError:
            message = (
                'unsupported system time zone: {0:s}, using default time '
                'zone').format(date_time.time_zone_hint)
            self._ProduceTimeliningWarning(storage_writer, event_data, message)

        if not time_zone:
          time_zone = self._preferred_time_zone or self._DEFAULT_TIME_ZONE

        date_time = copy.deepcopy(date_time)
        date_time.is_local_time = False

        if time_zone != pytz.UTC:
          datetime_object = datetime.datetime(
              1970, 1, 1, 0, 0, 0, 0, tzinfo=None)
          datetime_object += datetime.timedelta(microseconds=timestamp)

          datetime_delta = time_zone.utcoffset(datetime_object, is_dst=False)
          seconds_delta = int(datetime_delta.total_seconds())
          timestamp -= seconds_delta * definitions.MICROSECONDS_PER_SECOND

          date_time.time_zone_offset = seconds_delta // 60

    event = events.EventObject()
    event.date_time = date_time
    event.timestamp = timestamp
    event.timestamp_desc = date_time_description

    event_data_identifier = event_data.GetIdentifier()
    event.SetEventDataIdentifier(event_data_identifier)

    return event

  def _GetTimeZoneByPathSpec(self, path_spec):
    """Retrieves a time zone for a specific path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      pytz.tzfile: time zone or None if not available.

    Raises:
      pytz.UnknownTimeZoneError: if the time zone is unknown.
    """
    if not path_spec or not path_spec.parent:
      return None

    time_zone = self._time_zone_per_path_spec.get(path_spec.parent, None)
    if not time_zone:
      return None

    if isinstance(time_zone, str):
      try:
        time_zone = pytz.timezone(time_zone)
        self._time_zone_per_path_spec[path_spec.parent] = time_zone
      except pytz.UnknownTimeZoneError as exeception:
        self._time_zone_per_path_spec[path_spec.parent] = None
        raise exeception

    return time_zone

  def _ProduceTimeliningWarning(self, storage_writer, event_data, message):
    """Produces a timelining warning.

    Args:
      storage_writer (StorageWriter): storage writer.
      event_data (EventData): event data.
      message (str): message of the warning.
    """
    parser_chain = getattr(event_data, '_parser_chain', None)
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

  def ProcessEventData(self, storage_writer, event_data, event_data_stream):
    """Generate events from event data.

    Args:
      storage_writer (StorageWriter): storage writer.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    self.number_of_produced_events = 0

    attribute_mappings = self._attribute_mappings.get(
        event_data.data_type) or {}
    if (not attribute_mappings and
        event_data.data_type not in self._place_holder_event):
      return

    parser_name = None
    parser_chain = getattr(event_data, '_parser_chain', None)
    if parser_chain:
      parser_name = parser_chain.rsplit('/', maxsplit=1)[-1]

    number_of_events = 0
    for attribute_name, time_description in attribute_mappings.items():
      attribute_values = getattr(event_data, attribute_name, None) or []
      if not isinstance(attribute_values, list):
        attribute_values = [attribute_values]

      for attribute_value in attribute_values:
        if not isinstance(attribute_value, dfdatetime_interface.DateTimeValues):
          message = 'unsupported date time attribute: {0:s}'.format(
              attribute_name)
          self._ProduceTimeliningWarning(storage_writer, event_data, message)
          continue

        event = self._GetEvent(
            storage_writer, event_data, event_data_stream, attribute_value,
            time_description)

        try:
          storage_writer.AddAttributeContainer(event)
        except OverflowError as exception:
          message = 'unable to add event with error: {0!s}'.format(exception)
          self._ProduceTimeliningWarning(storage_writer, event_data, message)
          continue

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
          storage_writer, event_data, event_data_stream, date_time,
          definitions.TIME_DESCRIPTION_NOT_A_TIME)

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
    time_zone = None
    if time_zone_string:
      try:
        time_zone = pytz.timezone(time_zone_string)
      except pytz.UnknownTimeZoneError:
        raise ValueError('Unsupported time zone: {0!s}'.format(
            time_zone_string))

    self._preferred_time_zone = time_zone
