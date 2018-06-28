# -*- coding: utf-8 -*-
"""Shared code for Elasticsearch based output modules."""

from __future__ import unicode_literals

import logging

from dfvfs.serializer.json_serializer import JsonPathSpecSerializer

try:
  import elasticsearch
  from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
except ImportError:
  elasticsearch = None

from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import logger


# Configure the Elasticsearch logger.
if elasticsearch:
  elastic_logger = logging.getLogger('elasticsearch.trace')
  elastic_logger.setLevel(logging.WARNING)


class SharedElasticsearchOutputModule(interface.OutputModule):
  """Shared functionality for an Elasticsearch output module."""

  # pylint: disable=abstract-method

  NAME = 'elastic_shared'

  _DEFAULT_DOCUMENT_TYPE = 'plaso_event'

  _DEFAULT_FLUSH_INTERVAL = 1000

  # Number of seconds to wait before a request to Elasticsearch is timed out.
  _DEFAULT_REQUEST_TIMEOUT = 300

  def __init__(self, output_mediator):
    """Initializes an Elasticsearch output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(SharedElasticsearchOutputModule, self).__init__(output_mediator)
    self._client = None
    self._document_type = self._DEFAULT_DOCUMENT_TYPE
    self._event_documents = []
    self._flush_interval = self._DEFAULT_FLUSH_INTERVAL
    self._host = None
    self._index_name = None
    self._number_of_buffered_events = 0
    self._password = None
    self._port = None
    self._username = None

  def _Connect(self):
    """Connects to an Elasticsearch server."""
    elastic_hosts = [{'host': self._host, 'port': self._port}]

    elastic_http_auth = None
    if self._username is not None:
      elastic_http_auth = (self._username, self._password)

    self._client = elasticsearch.Elasticsearch(
        elastic_hosts, http_auth=elastic_http_auth)

    logger.debug('Connected to Elasticsearch server: {0:s} port: {1:d}.'.format(
        self._host, self._port))

  def _CreateIndexIfNotExists(self, index_name, mappings):
    """Creates an Elasticsearch index if it not already exists.

    Args:
      index_name (str): mame of the index.
      mappings (dict[str, object]): mappings of the index.

    Raises:
      RuntimeError: if the Elasticsearch index cannot be created.
    """
    try:
      if not self._client.indices.exists(index_name):
        self._client.indices.create(
            body={'mappings': mappings}, index=index_name)

    except ElasticConnectionError as exception:
      raise RuntimeError(
          'Unable to create Elasticsearch index with error: {0!s}'.format(
              exception))

  def _FlushEvents(self):
    """Inserts the buffered event documents into Elasticsearch."""
    try:
      # pylint: disable=unexpected-keyword-arg
      # pylint does not recognizes request_timeout as a valid kwarg. According
      # to http://elasticsearch-py.readthedocs.io/en/master/api.html#timeout
      # it should be supported.
      self._client.bulk(
          body=self._event_documents, doc_type=self._document_type,
          index=self._index_name, request_timeout=self._DEFAULT_REQUEST_TIMEOUT)

    except ValueError as exception:
      # Ignore problematic events
      logger.warning('Unable to bulk insert with error: {0!s}'.format(
          exception))

    logger.debug('Inserted {0:d} events into Elasticsearch'.format(
        self._number_of_buffered_events))

    self._event_documents = []
    self._number_of_buffered_events = 0

  def _GetSanitizedEventValues(self, event):
    """Sanitizes the event for use in Elasticsearch.

    The event values need to be sanitized to prevent certain values from
    causing problems when indexing with Elasticsearch. For example the path
    specification is a nested dictionary which will cause problems for
    Elasticsearch automatic indexing.

    Args:
      event (EventObject): event.

    Returns:
      dict[str, object]: sanitized event values.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event.
    """
    event_values = {}
    for attribute_name, attribute_value in event.GetAttributes():
      # Ignore the regvalue attribute as it cause issues when indexing.
      if attribute_name == 'regvalue':
        continue

      if attribute_name == 'pathspec':
        try:
          attribute_value = JsonPathSpecSerializer.WriteSerialized(
              attribute_value)
        except TypeError:
          continue
      event_values[attribute_name] = attribute_value

    # Add a string representation of the timestamp.
    try:
      attribute_value = timelib.Timestamp.RoundToSeconds(event.timestamp)
    except TypeError as exception:
      logger.warning((
          'Unable to round timestamp {0!s}. error: {1!s}. '
          'Defaulting to 0').format(event.timestamp, exception))
      attribute_value = 0

    attribute_value = timelib.Timestamp.CopyToIsoFormat(
        attribute_value, timezone=self._output_mediator.timezone)
    event_values['datetime'] = attribute_value

    message, _ = self._output_mediator.GetFormattedMessages(event)
    if message is None:
      data_type = getattr(event, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    event_values['message'] = message

    # Tags needs to be a list for Elasticsearch to index correctly.
    try:
      labels = list(event_values['tag'].labels)
    except (KeyError, AttributeError):
      labels = []
    event_values['tag'] = labels

    source_short, source = self._output_mediator.GetFormattedSources(
        event)
    if source is None or source_short is None:
      data_type = getattr(event, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    event_values['source_short'] = source_short
    event_values['source_long'] = source

    return event_values

  def _InsertEvent(self, event, force_flush=False):
    """Inserts an event.

    Events are buffered in the form of documents and inserted to Elasticsearch
    when either forced to flush or when the flush interval (threshold) has been
    reached.

    Args:
      event (EventObject): event.
      force_flush (bool): True if buffered event documents should be inserted
          into Elasticsearch.
    """
    if event:
      event_document = {'index': {
          '_index': self._index_name, '_type': self._document_type}}
      event_values = self._GetSanitizedEventValues(event)

      self._event_documents.append(event_document)
      self._event_documents.append(event_values)
      self._number_of_buffered_events += 1

    if force_flush or self._number_of_buffered_events > self._flush_interval:
      self._FlushEvents()

  def Close(self):
    """Closes connection to Elasticsearch.

    Inserts any remaining buffered event documents.
    """
    self._InsertEvent(None, force_flush=True)

    self._client = None

  def SetDocumentType(self, document_type):
    """Sets the document type.

    Args:
      document_type (str): document type.
    """
    self._document_type = document_type
    logger.debug('Elasticsearch document type: {0:s}'.format(document_type))

  def SetFlushInterval(self, flush_interval):
    """Set the flush interval.

    Args:
      flush_interval (int): number of events to buffer before doing a bulk
          insert.
    """
    self._flush_interval = flush_interval
    logger.debug('Elasticsearch flush interval: {0:d}'.format(flush_interval))

  def SetIndexName(self, index_name):
    """Set the index name.

    Args:
      index_name (str): name of the index.
    """
    self._index_name = index_name
    logger.debug('Elasticsearch index name: {0:s}'.format(index_name))

  def SetPassword(self, password):
    """Set the password.

    Args:
      password (str): password to authenticate with.
    """
    self._password = password
    logger.debug('Elastic password: ********')

  def SetServerInformation(self, server, port):
    """Set the server information.

    Args:
      server (str): IP address or hostname of the server.
      port (int): Port number of the server.
    """
    self._host = server
    self._port = port
    logger.debug('Elasticsearch server: {0!s} port: {1:d}'.format(server, port))

  def SetUsername(self, username):
    """Sets the username.

    Args:
      username (str): username to authenticate with.
    """
    self._username = username
    logger.debug('Elasticsearch username: {0!s}'.format(username))

  def WriteEventBody(self, event):
    """Writes an event to the output.

    Args:
      event (EventObject): event.
    """
    self._InsertEvent(event)
