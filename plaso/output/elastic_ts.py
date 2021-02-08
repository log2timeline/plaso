# -*- coding: utf-8 -*-
"""An output module that saves events to Elasticsearch for Timesketch."""

from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_elastic


class ElasticTimesketchOutputModule(
    shared_elastic.SharedElasticsearchOutputModule):
  """Output module for Timesketch Elasticsearch."""

  NAME = 'elastic_ts'
  DESCRIPTION = (
      'Saves the events into an Elasticsearch database for use '
      'with Timesketch.')

  MAPPINGS_FILENAME = 'plaso.mappings'
  MAPPINGS_PATH = '/etc/timesketch'

  def __init__(self, output_mediator):
    """Initializes a Timesketch Elasticsearch output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(ElasticTimesketchOutputModule, self).__init__(output_mediator)
    self._timeline_identifier = None

  def _GetSanitizedEventValues(
      self, event, event_data, event_data_stream, event_tag):
    """Sanitizes the event for use in Elasticsearch.

    The event values need to be sanitized to prevent certain values from
    causing problems when indexing with Elasticsearch. For example the path
    specification is a nested dictionary which will cause problems for
    Elasticsearch automatic indexing.

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
        super(ElasticTimesketchOutputModule, self)._GetSanitizedEventValues(
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
    """Connects to the Elasticsearch server and creates the index."""
    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, self._mappings)


manager.OutputManager.RegisterOutput(
    ElasticTimesketchOutputModule,
    disabled=shared_elastic.elasticsearch is None)
