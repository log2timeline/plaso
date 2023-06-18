# -*- coding: utf-8 -*-
"""The output and formatting multi-processing engine."""

import collections
import heapq
import os

from plaso.containers import events
from plaso.engine import processing_status
from plaso.lib import bufferlib
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_process import engine
from plaso.multi_process import logger
from plaso.output import mediator as output_mediator
from plaso.storage import time_range as storage_time_range


class PsortEventHeap(object):
  """Psort event heap."""

  _MAXIMUM_CACHED_HASHES = 500000

  def __init__(self):
    """Initializes a psort events heap."""
    super(PsortEventHeap, self).__init__()
    self._event_values_hash_cache = collections.OrderedDict()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of events on the heap."""
    return len(self._heap)

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      tuple: containing:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
        EventObject: event.
        EventData: event data.
        EventDataStream: event data stream.
    """
    try:
      (event_values_hash, _, event, event_data,
       event_data_stream) = heapq.heappop(self._heap)
      return event_values_hash, event, event_data, event_data_stream

    except IndexError:
      return None

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      tuple: containing:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
        EventObject: event.
        EventData: event data.
        EventDataStream: event data stream.
    """
    heap_values = self.PopEvent()
    while heap_values:
      yield heap_values
      heap_values = self.PopEvent()

  def PushEvent(self, event, event_data, event_data_stream):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    event_values_hash = getattr(event_data, '_event_values_hash', None)

    if not event_values_hash:
      # Note that this is kept for backwards compatibility for event_data
      # containers that do not have a _event_values_hash attribute value.
      event_data_identifier = event_data.GetIdentifier()
      lookup_key = event_data_identifier.CopyToString()

      event_values_hash = self._event_values_hash_cache.get(lookup_key, None)
      if not event_values_hash:
        event_values_hash = events.CalculateEventValuesHash(
            event_data, event_data_stream)
        if len(self._event_values_hash_cache) >= self._MAXIMUM_CACHED_HASHES:
          self._event_values_hash_cache.popitem(last=True)

        self._event_values_hash_cache[lookup_key] = event_values_hash

      self._event_values_hash_cache.move_to_end(lookup_key, last=False)

    timestamp_desc = event.timestamp_desc
    if timestamp_desc is None:
      logger.warning('Missing timestamp_desc attribute')
      timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    # Note that only events with the same timestamp are stored in the event
    # heap. The event values hash is stored first to cluster events with
    # similar event values.
    heapq.heappush(self._heap, (
        event_values_hash, timestamp_desc, event, event_data,
        event_data_stream))


class OutputAndFormattingMultiProcessEngine(engine.MultiProcessEngine):
  """Output and formatting multi-processing engine."""

  # TODO: move this to a single process engine.
  # pylint: disable=abstract-method

  _HEAP_MAXIMUM_EVENTS = 100000

  _MESSAGE_FORMATTERS_DIRECTORY_NAME = 'formatters'

  _MESSAGE_FORMATTERS_FILE_NAME = 'formatters.yaml'

  def __init__(self):
    """Initializes an output and formatting multi-processing engine."""
    super(OutputAndFormattingMultiProcessEngine, self).__init__()
    # The export event heap is used to make sure the events are sorted in
    # a deterministic way.
    self._events_status = processing_status.EventsStatus()
    self._export_event_heap = PsortEventHeap()
    self._export_event_timestamp = 0
    self._number_of_consumed_events = 0
    self._output_mediator = None
    self._processing_configuration = None
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._status_update_callback = None

  def _CreateOutputMediator(self, storage_reader, processing_configuration):
    """Creates an output mediator.

    Args:
      storage_reader (StorageReader): storage reader.
      processing_configuration (ProcessingConfiguration): processing
          configuration.

    Returns:
      OutputMediator: mediates interactions between output modules and other
          components, such as storage and dfVFS.

    Raises:
      BadConfigOption: if the message formatters file or directory cannot be
          read.
    """
    mediator = output_mediator.OutputMediator(
        storage_reader, data_location=processing_configuration.data_location,
        dynamic_time=processing_configuration.dynamic_time,
        preferred_encoding=processing_configuration.preferred_encoding)

    if processing_configuration.preferred_language:
      try:
        mediator.SetPreferredLanguageIdentifier(
            processing_configuration.preferred_language)
      except (KeyError, TypeError):
        logger.warning('Unable to to set preferred language: {0!s}.'.format(
              processing_configuration.preferred_language))

    mediator.SetTimeZone(processing_configuration.preferred_time_zone)

    self._ReadMessageFormatters(
        mediator, processing_configuration.data_location,
        processing_configuration.custom_formatters_path)

    return mediator

  def _ExportEvent(
      self, storage_reader, output_module, event, event_data, event_data_stream,
      deduplicate_events=True):
    """Exports an event using an output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
    """
    if (event.timestamp != self._export_event_timestamp or
        self._export_event_heap.number_of_events > self._HEAP_MAXIMUM_EVENTS):
      self._FlushExportBuffer(
          storage_reader, output_module, deduplicate_events=deduplicate_events)
      self._export_event_timestamp = event.timestamp

    self._export_event_heap.PushEvent(event, event_data, event_data_stream)

  def _ExportEvents(
      self, storage_reader, output_module, deduplicate_events=True,
      event_filter=None, time_slice=None, use_time_slicer=False):
    """Exports events using an output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      event_filter (Optional[EventObjectFilter]): event filter.
      time_slice (Optional[TimeRange]): time range that defines a time slice
          to filter events.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.
    """
    self._status = definitions.STATUS_INDICATOR_EXPORTING

    time_slice_buffer = None
    time_slice_range = None

    if time_slice:
      if time_slice.event_timestamp is not None:
        time_slice_range = storage_time_range.TimeRange(
            time_slice.start_timestamp, time_slice.end_timestamp)

      if use_time_slicer:
        time_slice_buffer = bufferlib.CircularBuffer(time_slice.duration)

    filter_limit = getattr(event_filter, 'limit', None)
    forward_entries = 0

    self._events_status.number_of_filtered_events = 0
    self._events_status.number_of_events_from_time_slice = 0

    for event in storage_reader.GetSortedEvents(time_range=time_slice_range):
      event_data_identifier = event.GetEventDataIdentifier()
      event_data = storage_reader.GetAttributeContainerByIdentifier(
          events.EventData.CONTAINER_TYPE, event_data_identifier)

      event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
      if event_data_stream_identifier:
        event_data_stream = storage_reader.GetAttributeContainerByIdentifier(
            events.EventDataStream.CONTAINER_TYPE, event_data_stream_identifier)
      else:
        event_data_stream = None

      event_identifier = event.GetIdentifier()
      event_tag = storage_reader.GetEventTagByEventIdentifer(event_identifier)

      if time_slice_range and event.timestamp != time_slice.event_timestamp:
        self._events_status.number_of_events_from_time_slice += 1

      if event_filter:
        filter_match = event_filter.Match(
            event, event_data, event_data_stream, event_tag)
      else:
        filter_match = None

      # pylint: disable=singleton-comparison
      if filter_match == False:
        if not time_slice_buffer:
          self._events_status.number_of_filtered_events += 1

        elif forward_entries == 0:
          time_slice_buffer.Append((event, event_data))
          self._events_status.number_of_filtered_events += 1

        elif forward_entries <= time_slice_buffer.size:
          self._ExportEvent(
              storage_reader, output_module, event, event_data,
              event_data_stream, deduplicate_events=deduplicate_events)
          self._number_of_consumed_events += 1
          self._events_status.number_of_events_from_time_slice += 1
          forward_entries += 1

        else:
          # We reached the maximum size of the time slice and don't need to
          # include other entries.
          self._events_status.number_of_filtered_events += 1
          forward_entries = 0

      else:
        # pylint: disable=singleton-comparison
        if filter_match == True and time_slice_buffer:
          # Empty the time slice buffer.
          for event_in_buffer, event_data_in_buffer in (
              time_slice_buffer.Flush()):
            self._ExportEvent(
                storage_reader, output_module, event_in_buffer,
                event_data_in_buffer, event_data_stream,
                deduplicate_events=deduplicate_events)
            self._number_of_consumed_events += 1
            self._events_status.number_of_filtered_events += 1
            self._events_status.number_of_events_from_time_slice += 1

          forward_entries = 1

        self._ExportEvent(
            storage_reader, output_module, event, event_data, event_data_stream,
            deduplicate_events=deduplicate_events)
        self._number_of_consumed_events += 1

        # pylint: disable=singleton-comparison
        if (filter_match == True and filter_limit and
            filter_limit == self._number_of_consumed_events):
          break

    self._FlushExportBuffer(storage_reader, output_module)

  def _FlushExportBuffer(
      self, storage_reader, output_module, deduplicate_events=True):
    """Flushes buffered events and writes them to the output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
    """
    last_event_values_hash = None
    last_macb_group_identifier = None
    last_timestamp_desc = None
    macb_group = []

    for (event_values_hash, event, event_data,
         event_data_stream) in self._export_event_heap.PopEvents():
      timestamp_desc = event.timestamp_desc

      if (deduplicate_events and timestamp_desc == last_timestamp_desc and
          event_values_hash == last_event_values_hash):
        self._events_status.number_of_duplicate_events += 1
        continue

      event_identifier = event.GetIdentifier()
      event_tag = storage_reader.GetEventTagByEventIdentifer(event_identifier)

      if timestamp_desc in (
          definitions.TIME_DESCRIPTION_LAST_ACCESS,
          definitions.TIME_DESCRIPTION_CREATION,
          definitions.TIME_DESCRIPTION_METADATA_MODIFICATION,
          definitions.TIME_DESCRIPTION_MODIFICATION):
        macb_group_identifier = event_values_hash
      else:
        macb_group_identifier = None

      if macb_group_identifier is None:
        if macb_group:
          output_module.WriteFieldValuesOfMACBGroup(
              self._output_mediator, macb_group)
          macb_group = []

        output_module.WriteFieldValues(
            self._output_mediator, event, event_data, event_data_stream,
            event_tag)

      else:
        if (last_macb_group_identifier == macb_group_identifier or
            not macb_group):
          macb_group.append((event, event_data, event_data_stream, event_tag))

        else:
          output_module.WriteFieldValuesOfMACBGroup(
              self._output_mediator, macb_group)
          macb_group = [(event, event_data, event_data_stream, event_tag)]

        self._events_status.number_of_macb_grouped_events += 1

      last_event_values_hash = event_values_hash
      last_macb_group_identifier = macb_group_identifier
      last_timestamp_desc = timestamp_desc

    if macb_group:
      output_module.WriteFieldValuesOfMACBGroup(
          self._output_mediator, macb_group)

  def _ReadMessageFormatters(
      self, output_mediator_object, data_location, custom_formatters_path):
    """Reads the message formatters from a formatters file or directory.

    Args:
      output_mediator_object (OutputMediator): mediates interactions between
          output modules and other components, such as storage and dfVFS.
      data_location (str): path to the data files.
      custom_formatters_path (str): path to custom formatter definitions file.

    Raises:
      BadConfigOption: if the message formatters file or directory cannot be
          read.
    """
    formatters_directory = os.path.join(
        data_location, self._MESSAGE_FORMATTERS_DIRECTORY_NAME)
    formatters_file = os.path.join(
        data_location, self._MESSAGE_FORMATTERS_FILE_NAME)

    if os.path.isdir(formatters_directory):
      try:
        output_mediator_object.ReadMessageFormattersFromDirectory(
            formatters_directory)
      except KeyError as exception:
        raise errors.BadConfigOption((
            'Unable to read message formatters from directory: {0:s} with '
            'error: {1!s}').format(formatters_directory, exception))

    elif os.path.isfile(formatters_file):
      try:
        output_mediator_object.ReadMessageFormattersFromFile(formatters_file)
      except KeyError as exception:
        raise errors.BadConfigOption((
            'Unable to read message formatters from file: {0:s} with error: '
            '{1!s}').format(formatters_file, exception))

    else:
      raise errors.BadConfigOption('Missing formatters file and directory.')

    if custom_formatters_path:
      try:
        output_mediator_object.ReadMessageFormattersFromFile(
            custom_formatters_path, override_existing=True)
      except KeyError as exception:
        raise errors.BadConfigOption((
            'Unable to read custrom message formatters from file: {0:s} with '
            'error: {1!s}').format(formatters_file, exception))

  def _UpdateForemanProcessStatus(self):
    """Update the foreman process status."""
    used_memory = self._process_information.GetUsedMemory() or 0

    self._processing_status.UpdateForemanStatus(
        self._name, self._status, self._pid, used_memory, '',
        0, 0, 0, 0, self._number_of_consumed_events, 0, 0, 0, 0, 0)

    self._processing_status.UpdateEventsStatus(self._events_status)

  def _UpdateStatus(self):
    """Update the status."""
    self._UpdateForemanProcessStatus()

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def ExportEvents(
      self, storage_reader, output_module, processing_configuration,
      deduplicate_events=True, event_filter=None, status_update_callback=None,
      time_slice=None, use_time_slicer=False):
    """Exports events using an output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      event_filter (Optional[EventObjectFilter]): event filter.
      status_update_callback (Optional[function]): callback function for status
          updates.
      time_slice (Optional[TimeSlice]): slice of time to output.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.

    Raises:
      BadConfigOption: if the message formatters file or directory cannot be
          read.
    """
    self._events_status = processing_status.EventsStatus()
    self._processing_configuration = processing_configuration
    self._status_update_callback = status_update_callback

    total_number_of_events = 0
    if storage_reader.HasAttributeContainers('parser_count'):
      parsers_counter = {
          parser_count.name: parser_count.number_of_events
          for parser_count in storage_reader.GetAttributeContainers(
              'parser_count')}

      total_number_of_events = parsers_counter['total']

    self._events_status.total_number_of_events = total_number_of_events

    self._output_mediator = self._CreateOutputMediator(
        storage_reader, processing_configuration)

    output_module.WriteHeader(output_mediator)

    self._StartStatusUpdateThread()

    self._StartProfiling(self._processing_configuration.profiling)

    try:
      self._ExportEvents(
          storage_reader, output_module, deduplicate_events=deduplicate_events,
          event_filter=event_filter, time_slice=time_slice,
          use_time_slicer=use_time_slicer)

      self._status = definitions.STATUS_INDICATOR_COMPLETED

    finally:
      # Stop the status update thread after close of the storage writer
      # so we include the storage sync to disk in the status updates.
      self._StopStatusUpdateThread()

    output_module.WriteFooter()

    # Update the status view one last time.
    self._UpdateStatus()

    self._StopProfiling()

    # Reset values.
    self._events_status = None
    self._output_mediator = None
    self._processing_configuration = None
    self._status_update_callback = None
