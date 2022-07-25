# -*- coding: utf-8 -*-
"""The output and formatting multi-processing engine."""

import collections
import heapq

from plaso.containers import events
from plaso.engine import processing_status
from plaso.lib import bufferlib
from plaso.lib import definitions
from plaso.multi_process import engine
from plaso.multi_process import logger
from plaso.storage import time_range as storage_time_range


class PsortEventHeap(object):
  """Psort event heap."""

  _IDENTIFIER_EXCLUDED_ATTRIBUTES = frozenset([
      'data_type',
      'parser',
      'tag',
      'timestamp',
      'timestamp_desc'])

  _MAXIMUM_CACHED_IDENTIFIERS = 500000

  def __init__(self):
    """Initializes a psort events heap."""
    super(PsortEventHeap, self).__init__()
    self._event_data_content_identifier_cache = collections.OrderedDict()
    self._heap = []

  @property
  def number_of_events(self):
    """int: number of events on the heap."""
    return len(self._heap)

  def _GetEventDataContentIdentifier(self, event_data, event_data_stream):
    """Retrieves the event data content identifier.

    Args:
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      str: identifier of the event data content.
    """
    event_data_identifier = event_data.GetIdentifier()
    lookup_key = event_data_identifier.CopyToString()

    content_identifier = self._event_data_content_identifier_cache.get(
        lookup_key, None)
    if not content_identifier:
      event_attributes = list(event_data.GetAttributes())
      if event_data_stream:
        event_data_stream_attributes = event_data_stream.GetAttributes()
        event_attributes.extend(event_data_stream_attributes)

      attributes = ['data_type: {0:s}'.format(event_data.data_type)]

      for attribute_name, attribute_value in sorted(event_attributes):
        if (attribute_name in self._IDENTIFIER_EXCLUDED_ATTRIBUTES or
            attribute_value is None):
          continue

        # Note that support for event_data.pathspec is kept for backwards
        # compatibility. The current value is event_data_stream.path_spec.
        if attribute_name in ('path_spec', 'pathspec'):
          attribute_value = attribute_value.comparable

        elif isinstance(attribute_value, dict):
          attribute_value = sorted(attribute_value.items())

        elif isinstance(attribute_value, set):
          attribute_value = sorted(list(attribute_value))

        elif isinstance(attribute_value, bytes):
          attribute_value = repr(attribute_value)

        try:
          attribute_string = '{0:s}: {1!s}'.format(
              attribute_name, attribute_value)
        except UnicodeDecodeError:
          logger.error('Failed to decode attribute {0:s}'.format(
              attribute_name))
        attributes.append(attribute_string)

      content_identifier = ', '.join(attributes)

      if len(self._event_data_content_identifier_cache) >= (
          self._MAXIMUM_CACHED_IDENTIFIERS):
        self._event_data_content_identifier_cache.popitem(last=True)

      self._event_data_content_identifier_cache[lookup_key] = content_identifier

    self._event_data_content_identifier_cache.move_to_end(
        lookup_key, last=False)
    return content_identifier

  def _GetEventIdentifiers(self, event, event_data, event_data_stream):
    """Retrieves different identifiers of the event.

    The event data attributes and values can be represented as a string and used
    for sorting and uniquely identifying events. This function determines
    multiple identifiers:
    * an identifier of the attributes and values without the timestamp
      description (or usage). This is referred to as the MACB group
      identifier.
    * an identifier of the attributes and values including the timestamp
      description (or usage). This is referred to as the event content
      identifier.

    The identifier without the timestamp description can be used to group
    events that have the same MACB (modification, access, change, birth)
    timestamps. The PsortEventHeap will store these events individually and
    relies on PsortMultiProcessEngine to do the actual grouping of events.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.

    Returns:
      tuple: containing:

        str: identifier of the event MACB group or None if the event cannot
            be grouped.
        str: identifier of the event content.
    """
    content_identifier = self._GetEventDataContentIdentifier(
        event_data, event_data_stream)

    if event.timestamp_desc in (
        definitions.TIME_DESCRIPTION_LAST_ACCESS,
        definitions.TIME_DESCRIPTION_CHANGE,
        definitions.TIME_DESCRIPTION_CREATION,
        definitions.TIME_DESCRIPTION_MODIFICATION):
      macb_group_identifier = content_identifier
    else:
      macb_group_identifier = None

    timestamp_desc = event.timestamp_desc
    if timestamp_desc is None:
      logger.warning('Missing timestamp_desc attribute')
      timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    content_identifier = ', '.join([timestamp_desc, content_identifier])

    return macb_group_identifier, content_identifier

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
      (macb_group_identifier, content_identifier, event, event_data,
       event_data_stream) = heapq.heappop(self._heap)
      if macb_group_identifier == '':
        macb_group_identifier = None
      return (macb_group_identifier, content_identifier, event, event_data,
              event_data_stream)

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
    macb_group_identifier, content_identifier = self._GetEventIdentifiers(
        event, event_data, event_data_stream)

    # We can ignore the timestamp here because the psort engine only stores
    # events with the same timestamp in the event heap.
    heap_values = (
        macb_group_identifier or '', content_identifier, event, event_data,
        event_data_stream)
    heapq.heappush(self._heap, heap_values)


class OutputAndFormattingMultiProcessEngine(engine.MultiProcessEngine):
  """Output and formatting multi-processing engine."""

  # TODO: move this to a single process engine.
  # pylint: disable=abstract-method

  _HEAP_MAXIMUM_EVENTS = 100000

  def __init__(self):
    """Initializes an output and formatting multi-processing engine."""
    super(OutputAndFormattingMultiProcessEngine, self).__init__()
    # The export event heap is used to make sure the events are sorted in
    # a deterministic way.
    self._events_status = processing_status.EventsStatus()
    self._export_event_heap = PsortEventHeap()
    self._export_event_timestamp = 0
    self._knowledge_base = None
    self._number_of_consumed_events = 0
    self._processing_configuration = None
    self._status = definitions.STATUS_INDICATOR_IDLE
    self._status_update_callback = None

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
    last_macb_group_identifier = None
    last_content_identifier = None
    macb_group = []

    generator = self._export_event_heap.PopEvents()

    for (macb_group_identifier, content_identifier, event, event_data,
         event_data_stream) in generator:
      if deduplicate_events and last_content_identifier == content_identifier:
        self._events_status.number_of_duplicate_events += 1
        continue

      event_identifier = event.GetIdentifier()
      event_tag = storage_reader.GetEventTagByEventIdentifer(event_identifier)

      if macb_group_identifier is None:
        if macb_group:
          output_module.WriteEventMACBGroup(macb_group)
          macb_group = []

        output_module.WriteEvent(
            event, event_data, event_data_stream, event_tag)

      else:
        if (last_macb_group_identifier == macb_group_identifier or
            not macb_group):
          macb_group.append((event, event_data, event_data_stream, event_tag))

        else:
          output_module.WriteEventMACBGroup(macb_group)
          macb_group = [(event, event_data, event_data_stream, event_tag)]

        self._events_status.number_of_macb_grouped_events += 1

      last_macb_group_identifier = macb_group_identifier
      last_content_identifier = content_identifier

    if macb_group:
      output_module.WriteEventMACBGroup(macb_group)

  def _UpdateForemanProcessStatus(self):
    """Update the foreman process status."""
    used_memory = self._process_information.GetUsedMemory() or 0

    self._processing_status.UpdateForemanStatus(
        self._name, self._status, self._pid, used_memory, '',
        0, 0, self._number_of_consumed_events, 0, 0, 0, 0, 0)

    self._processing_status.UpdateEventsStatus(self._events_status)

  def _UpdateStatus(self):
    """Update the status."""
    self._UpdateForemanProcessStatus()

    if self._status_update_callback:
      self._status_update_callback(self._processing_status)

  def ExportEvents(
      self, knowledge_base_object, storage_reader, output_module,
      processing_configuration, deduplicate_events=True, event_filter=None,
      status_update_callback=None, time_slice=None, use_time_slicer=False):
    """Exports events using an output module.

    Args:
      knowledge_base_object (KnowledgeBase): contains information from
          the source data needed for processing.
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
    """
    self._events_status = processing_status.EventsStatus()
    self._knowledge_base = knowledge_base_object
    self._processing_configuration = processing_configuration
    self._status_update_callback = status_update_callback

    if storage_reader.HasAttributeContainers('parser_count'):
      parsers_counter = {
          parser_count.name: parser_count.number_of_events
          for parser_count in storage_reader.GetAttributeContainers(
              'parser_count')}

      total_number_of_events = parsers_counter['total']

    else:
      # Fallback for older formats.
      total_number_of_events = 0
      for stored_session in storage_reader.GetSessions():
        # There is an edge case where no parser_count attribute containers
        # are stored since no events were extracted.
        if stored_session.parsers_counter:
          total_number_of_events += stored_session.parsers_counter.get(
              'total', 0)

    self._events_status.total_number_of_events = total_number_of_events

    output_module.WriteHeader()

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
    self._status_update_callback = None
    self._processing_configuration = None
    self._knowledge_base = None
    self._events_status = None
