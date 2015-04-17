# -*- coding: utf-8 -*-
"""An output module that saves events to Timesketch."""

from collections import Counter
from datetime import datetime
import logging
import sys
import uuid

from elasticsearch import exceptions as elastic_exceptions
from flask import current_app
import timesketch
from timesketch.lib.datastores.elastic import ElasticSearchDataStore
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.user import User

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

  ARGUMENTS = [
      (u'--name', {
          u'dest': u'name',
          u'type': unicode,
          u'help': (u'The name of the timeline in Timesketch. Default: '
                    u'hostname if present in the storage file. If no hostname '
                    u'is found then manual input is used.'),
          u'action': u'store',
          u'required': False,
          u'default': u''}),
      (u'--index', {
          u'dest': u'index',
          u'type': unicode,
          u'help': u'The name of the Elasticsearch index. Default: Generate a '
                   u'random UUID',
          u'action': u'store',
          u'required': False,
          u'default': uuid.uuid4().hex}),
      (u'--owner', {
          u'dest': u'owner',
          u'type': unicode,
          u'help': u'The username of the Timesketch user that will be the '
                   u'owner of this timeline. Default: None',
          u'action': u'store',
          u'required': False,
          u'default': u''}),
      (u'--flush_interval', {
          u'dest': u'flush_interval',
          u'type': int,
          u'help': u'The number of events to queue up before sent in bulk '
                   u'to Elasticsearch. Default: 1000',
          u'action': u'store',
          u'required': False,
          u'default': 1000})]

  def __init__(self, output_mediator, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(TimesketchOutputModule, self).__init__(output_mediator, **kwargs)

    # Get Elasticsearch config from Timesketch.
    self._timesketch = timesketch.create_app()
    with self._timesketch.app_context():
      self._elastic_db = ElasticSearchDataStore(
          host=current_app.config[u'ELASTIC_HOST'],
          port=current_app.config[u'ELASTIC_PORT'])

    self._counter = Counter()
    self._doc_type = u'plaso_event'
    self._events = []
    self._flush_interval = self._output_mediator.GetConfigurationValue(
        u'flush_interval')
    self._index_name = self._output_mediator.GetConfigurationValue(u'index')
    self._timeline_name = self._output_mediator.GetConfigurationValue(u'name')
    self._timeline_owner = self._output_mediator.GetConfigurationValue(u'owner')
    self._timing_start = datetime.now()

    hostname = self._output_mediator.GetStoredHostname()
    if hostname:
      logging.info(u'Hostname: {0:s}'.format(hostname))

    # Make sure we have a name for the timeline. Prompt the user if not.
    if not self._timeline_name:
      if hostname:
        self._timeline_name = hostname
      else:
        # This should not be handles in this module.
        # TODO: Move this to CLI code when available.
        self._timeline_name = raw_input(u'Timeline name: ')

    logging.info(u'Timeline name: {0:s}'.format(self._timeline_name))
    logging.info(u'Index: {0:s}'.format(self._index_name))

  def _GetSanitizedEventValues(self, event_object):
    """Builds a dictionary from an event_object.

    The values from the event object need to be sanitized to prevent
    values causing problems when indexing them with ElasticSearch.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      Dictionary with sanitized event object values.
    """
    event_values = event_object.GetValues()

    # Get rid of few attributes that cause issues (and need correcting).
    if u'pathspec' in event_values:
      del event_values[u'pathspec']

    # To not overload the index, remove the regvalue index.
    # TODO: Investigate if this is really necessary?
    if u'regvalue' in event_values:
      del event_values[u'regvalue']

    # Adding attributes in that are calculated/derived.
    # We want to remove millisecond precision (causes some issues in
    # conversion).
    event_values[u'datetime'] = timelib.Timestamp.CopyToIsoFormat(
        timelib.Timestamp.RoundToSeconds(event_object.timestamp),
        timezone=self._output_mediator.timezone)

    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    event_values[u'message'] = message

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

  def Close(self):
    """Closes the connection to TimeSketch Elasticsearch database.

    Sends the remaining events for indexing and adds the timeline to Timesketch.
    """
    self._FlushEventsToElasticsearch()

    with self._timesketch.app_context():
      # Get Timesketch user object, or None if user do not exist. This is a
      # SQLAlchemy query against the Timesketch database.
      user_query = User.query.filter_by(username=self._timeline_owner)
      user = user_query.first()
      search_index = SearchIndex(
          name=self._timeline_name, description=self._timeline_name, user=user,
          index_name=self._index_name)

    # Grant all users read permission on the mapping object.
    search_index.grant_permission(None, u'read')
    # Save the mapping object to the Timesketch database.
    db_session.add(search_index)
    db_session.commit()

    # Clean up stdout.
    # TODO: an output module should not call sys.stdout directly.
    sys.stdout.write(u'\n')
    sys.stdout.flush()

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
      # Show indexing progress.
      timing_delta = datetime.now() - self._timing_start
      events_per_second = 0
      if timing_delta.seconds > 0:
        events_per_second, _ = divmod(
            self._counter[u'events'], timing_delta.seconds)

      # TODO: an output module should not call sys.stdout directly.
      sys.stdout.write((
          u'[INFO] Insert data: {0:d} events inserted '
          u'(~{1:d} events/s)\r').format(
              self._counter[u'events'], events_per_second))
      sys.stdout.flush()

  def WriteHeader(self):
    """Creates the Elasticsearch index with Timesketch specific settings."""
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

    logging.info(u'Adding events to Timesketch..')


manager.OutputManager.RegisterOutput(TimesketchOutputModule)
