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

    # Add timeline_id on the event level. It is used in Timesketch to
    # support shared indices.
    field_values['__ts_timeline_id'] = self._timeline_identifier

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


manager.OutputManager.RegisterOutput(
    OpenSearchTimesketchOutputModule,
    disabled=shared_opensearch.opensearchpy is None)
