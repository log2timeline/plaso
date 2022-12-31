# -*- coding: utf-8 -*-
"""An output module that saves events to OpenSearch."""

from plaso.output import manager
from plaso.output import shared_opensearch


class OpenSearchOutputModule(shared_opensearch.SharedOpenSearchOutputModule):
  """Output module for OpenSearch."""

  NAME = 'opensearch'
  DESCRIPTION = 'Saves the events into an OpenSearch database.'

  MAPPINGS_FILENAME = 'opensearch.mappings'

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Events are buffered in the form of documents and inserted to OpenSearch
    when the flush interval (threshold) has been reached.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    event_document = {'index': {'_index': self._index_name}}

    self._event_documents.append(event_document)
    self._event_documents.append(field_values)
    self._number_of_buffered_events += 1

    if self._number_of_buffered_events > self._flush_interval:
      self._FlushEvents()

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
