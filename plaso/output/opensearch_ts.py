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

  def __init__(self, output_mediator):
    """Initializes a Timesketch OpenSearch output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(OpenSearchTimesketchOutputModule, self).__init__(output_mediator)
    self._timeline_identifier = None

  def _GetSanitizedEventValues(
      self, event, event_data, event_data_stream, event_tag):
    """Sanitizes the event for use in OpenSearch.

    The event values need to be sanitized to prevent certain values from
    causing problems when indexing with OpenSearch. For example the path
    specification is a nested dictionary which will cause problems for
    OpenSearch automatic indexing.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, object]: sanitized event values.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event data.
    """
    event_values = (
        super(OpenSearchTimesketchOutputModule, self)._GetSanitizedEventValues(
            event=event, event_data=event_data,
            event_data_stream=event_data_stream, event_tag=event_tag))

    event_values['__ts_timeline_id'] = self._timeline_identifier

    return event_values

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

  def WriteHeader(self):
    """Connects to the OpenSearch server and creates the index."""
    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, self._mappings)


manager.OutputManager.RegisterOutput(
    OpenSearchTimesketchOutputModule,
    disabled=shared_opensearch.opensearchpy is None)
