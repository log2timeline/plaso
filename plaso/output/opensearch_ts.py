# -*- coding: utf-8 -*-
"""An output module that saves events to OpenSearch for Timesketch."""

from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_opensearch


class OpenSearchTimesketchOutputModule(
    shared_opensearch.SharedOpenSearchOutputModule):
  """Output module for Timesketch OpenSearch."""

  NAME = 'opensearch_ts'
  DESCRIPTION = (
      'Saves the events into an OpenSearch database for use '
      'with Timesketch.')

  MAPPINGS_FILENAME = 'plaso.mappings'
  MAPPINGS_PATH = '/etc/timesketch'

  def __init__(self):
    """Initializes an output module."""
    super(OpenSearchTimesketchOutputModule, self).__init__()
    self._timeline_identifier = None

  def _InsertEvent(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Inserts an event.

    Events are buffered in the form of documents and inserted to OpenSearch
    when the flush interval (threshold) has been reached.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    event_document = {
        '__ts_timeline_id': self._timeline_identifier,
        'index': {'_index': self._index_name}}

    field_values = self.GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self._event_documents.append(event_document)
    self._event_documents.append(field_values)
    self._number_of_buffered_events += 1

    if self._number_of_buffered_events > self._flush_interval:
      self._FlushEvents()

  def GetMissingArguments(self):
    """Retrieves a list of arguments that are missing from the input.

    Returns:
      list[str]: names of arguments that are required by the module and have
          not been specified.
    """
    if not self._timeline_identifier:
      return ['timeline_id']
    return []

  def SetTimelineIdentifier(self, timeline_identifier):
    """Sets the timeline identifier.

    Args:
      timeline_identifier (int): timeline identifier.
    """
    self._timeline_identifier = timeline_identifier
    logger.info('Timeline identifier: {0:d}'.format(self._timeline_identifier))

  def WriteHeader(self, output_mediator):
    """Connects to the OpenSearch server and creates the index.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, self._mappings)

  def WriteEventBody(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    self._InsertEvent(
        output_mediator, event, event_data, event_data_stream, event_tag)


manager.OutputManager.RegisterOutput(
    OpenSearchTimesketchOutputModule,
    disabled=shared_opensearch.opensearchpy is None)
