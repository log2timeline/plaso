# -*- coding: utf-8 -*-
"""An output module that saves events to Timesketch."""

from collections import Counter
import logging

try:
  from elasticsearch import exceptions as elastic_exceptions
  from flask import current_app
  import timesketch
  from timesketch.lib.datastores.elastic import ElasticSearchDataStore
  from timesketch.models import db_session
  from timesketch.models.sketch import SearchIndex
except ImportError:
  timesketch = None

from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager

# Configure Elasticsearch logger
elastic_logger = logging.getLogger(u'elasticsearch')
elastic_logger.propagate = False


class TimesketchOutputModule(interface.OutputModule):
  """Output module for Timesketch."""

  NAME = u'timesketch'
  DESCRIPTION = u'Create a Timesketch timeline.'

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(TimesketchOutputModule, self).__init__(output_mediator)

    self._counter = Counter()
    self._doc_type = u'plaso_event'
    self._events = []
    self._flush_interval = None
    self._index_name = None
    self._timesketch = timesketch.create_app()

    # TODO: Support reading in server and port information and set this using
    # options.
    with self._timesketch.app_context():
      self._elastic_db = ElasticSearchDataStore(
          host=current_app.config[u'ELASTIC_HOST'],
          port=current_app.config[u'ELASTIC_PORT'])

    hostname = self._output_mediator.GetStoredHostname()
    if hostname:
      logging.info(u'Hostname: {0:s}'.format(hostname))
      self._timeline_name = hostname
    else:
      self._timeline_name = None

  def _GetSanitizedEventValues(self, event_object):
    """Builds a dictionary from an event_object.

    The values from the event object need to be sanitized to prevent
    values causing problems when indexing them with ElasticSearch.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      Dictionary with sanitized event object values.
    """
    event_values = {}
    for attribute_name, attribute_value in event_object.GetAttributes():
      # Ignore attributes that cause issues (and need correcting).
      if attribute_name in (u'pathspec', u'regvalue'):
        continue

      event_values[attribute_name] = attribute_value

    # Adding attributes in that are calculated/derived.

    # We want to remove millisecond precision (causes some issues in
    # conversion).
    attribute_value = timelib.Timestamp.RoundToSeconds(event_object.timestamp)
    attribute_value = timelib.Timestamp.CopyToIsoFormat(
        attribute_value, timezone=self._output_mediator.timezone)
    event_values[u'datetime'] = attribute_value

    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    event_values[u'message'] = message

    try:
      labels = list(event_values[u'tag'].labels)
    except (KeyError, AttributeError):
      labels = []
    event_values[u'tag'] = labels

    source_short, source = self._output_mediator.GetFormattedSources(
        event_object)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    event_values[u'source_short'] = source_short
    event_values[u'source_long'] = source

    return event_values

  def _FlushEventsToElasticsearch(self):
    """Insert events in bulk to Elasticsearch."""
    self._elastic_db.client.bulk(
        index=self._index_name, doc_type=self._doc_type, body=self._events)
    # Clear the events list.
    self._events = []
    logging.info(u'{0:d} events added'.format(self._counter[u'events']))

  def Close(self):
    """Closes the connection to TimeSketch Elasticsearch database.

    Sends the remaining events for indexing and removes the processing status on
    the Timesketch search index object.
    """
    self._FlushEventsToElasticsearch()
    with self._timesketch.app_context():
      search_index = SearchIndex.query.filter_by(
          index_name=self._index_name).first()
      search_index.status.remove(search_index.status[0])
      db_session.add(search_index)
      db_session.commit()

  def GetMissingArguments(self):
    """Return a list of arguments that are missing from the input.

    Returns:
      a list of argument names that are missing and necessary for the
      module to continue to operate.
    """
    if not self._timeline_name:
      return [u'timeline_name']

    return []

  def SetFlushInterval(self, flush_interval):
    """Set the flush interval.

    Args:
      flush_interval: the flush interval.
    """
    self._flush_interval = flush_interval

  def SetIndex(self, index):
    """Set the index name.

    Args:
      index: the index name.
    """
    self._index_name = index
    logging.info(u'Index: {0:s}'.format(self._index_name))

  def SetName(self, name):
    """Set the timeline name.

    Args:
      name: the timeline name.
    """
    self._timeline_name = name
    logging.info(u'Timeline name: {0:s}'.format(self._timeline_name))

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    # This is the format Elasticsearch expects the data to be in when inserting
    # the events in bulk. Reference:
    # http://www.elastic.co/guide/en/elasticsearch/reference/1.4/docs-bulk.html
    self._events.append(
        {u'index': {u'_index': self._index_name, u'_type': self._doc_type}})
    self._events.append(self._GetSanitizedEventValues(event_object))
    self._counter[u'events'] += 1

    # Check if we need to flush, i.e. send the events we have so far to
    # Elasticsearch for indexing.
    if self._counter[u'events'] % self._flush_interval == 0:
      self._FlushEventsToElasticsearch()

  def WriteHeader(self):
    """Setup the Elasticsearch index and the Timesketch database object.

    Creates the Elasticsearch index with Timesketch specific settings and the
    Timesketch SearchIndex database object.
    """
    # This cannot be static because we use the value of self._doc_type from
    # arguments.
    _document_mapping = {
        self._doc_type: {
            u'_timestamp': {
                u'enabled': True,
                u'path': u'datetime',
                u'format': u'date_time_no_millis'
            },
            u'properties': {u'timesketch_label': {u'type': u'nested'}}
        }
    }

    if not self._elastic_db.client.indices.exists(self._index_name):
      try:
        self._elastic_db.client.indices.create(
            index=self._index_name, body={u'mappings': _document_mapping})
      except elastic_exceptions.ConnectionError as exception:
        logging.error((
            u'Unable to proceed, cannot connect to Timesketch backend '
            u'with error: {0:s}.\nPlease verify connection.').format(exception))
        raise RuntimeError(u'Unable to connect to Timesketch backend.')

    with self._timesketch.app_context():
      search_index = SearchIndex.get_or_create(
          name=self._timeline_name, description=self._timeline_name, user=None,
          index_name=self._index_name)
      # Grant all users read permission on the mapping object and set status.
      search_index.grant_permission(None, u'read')
      search_index.set_status(u'processing')
      # Save the mapping object to the Timesketch database.
      db_session.add(search_index)
      db_session.commit()

    logging.info(u'Adding events to Timesketch..')


manager.OutputManager.RegisterOutput(
    TimesketchOutputModule, disabled=timesketch is None)
