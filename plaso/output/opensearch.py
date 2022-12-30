# -*- coding: utf-8 -*-
"""An output module that saves events to OpenSearch."""

from plaso.output import manager
from plaso.output import shared_opensearch


class OpenSearchOutputModule(shared_opensearch.SharedOpenSearchOutputModule):
  """Output module for OpenSearch."""

  NAME = 'opensearch'
  DESCRIPTION = 'Saves the events into an OpenSearch database.'

  MAPPINGS_FILENAME = 'opensearch.mappings'

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
    event_document = {'index': {'_index': self._index_name}}

    field_values = self.GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self._event_documents.append(event_document)
    self._event_documents.append(field_values)
    self._number_of_buffered_events += 1

    if self._number_of_buffered_events > self._flush_interval:
      self._FlushEvents()

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

  def WriteHeader(self, output_mediator):
    """Connects to the OpenSearch server and creates the index.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, self._mappings)


manager.OutputManager.RegisterOutput(
    OpenSearchOutputModule, disabled=shared_opensearch.opensearchpy is None)
