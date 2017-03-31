# -*- coding: utf-8 -*-
"""An output module that saves events to Elasticsearch."""

from collections import Counter
import logging

from dfvfs.serializer.json_serializer import JsonPathSpecSerializer

try:
  from elasticsearch import Elasticsearch
  from elasticsearch.exceptions import ConnectionError
except ImportError:
  Elasticsearch = None

from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager

# Configure Elasticsearch logger
elastic_logger = logging.getLogger(u'elasticsearch.trace')
elastic_logger.setLevel(logging.WARNING)


class ElasticSearchHelper(object):
  """Elasticsearch helper class."""

  def __init__(
      self, output_mediator, host, port, flush_interval, index_name, mapping,
      doc_type, elastic_password=None, elastic_user=None):
    """Create a Elasticsearch helper.

    Args:
      output_mediator (OutputMediator): The output mediator object.
      host (str): IP address or hostname for the server.
      port (int): Port number for the server.
      flush_interval (int): How many events to queue before being indexed.
      index_name (str): Name of the Elasticsearch index.
      mapping (dict): Elasticsearch index configuration.
      doc_type (str): Elasticsearch document type name.
      elastic_passsword (Optional[str]): Elasticsearch password to authenticate
          with.
      elastic_user (Optional[str]): Elasticsearch username to authenticate with.
    """
    super(ElasticSearchHelper, self).__init__()

    elastic_hosts = [{u'host': host, u'port': port}]
    if elastic_user is None:
      self.client = Elasticsearch(elastic_hosts)
    else:
      self.client = Elasticsearch(
          elastic_hosts, http_auth=(elastic_user, elastic_password))

    self._output_mediator = output_mediator
    self._index = self._EnsureIndexExists(index_name, mapping)
    self._doc_type = doc_type
    self._flush_interval = flush_interval
    self._events = []
    self._counter = Counter()
    self._elastic_user = elastic_user
    self._elastic_password = elastic_password

  def AddEvent(self, event_object, force_flush=False):
    """Index event in Elasticsearch.

    Args:
      event_object (EventObject): the event object.
      force_flush (bool): Force bulk insert of events in the queue.
    """
    if event_object:
      self._events.append(
          {u'index': {u'_index': self._index, u'_type': self._doc_type}})
      self._events.append(self._GetSanitizedEventValues(event_object))
      self._counter[u'events'] += 1

    # Check if we need to flush the queued events
    if force_flush or self._counter[u'events'] % self._flush_interval == 0:
      self._FlushEventsToElasticSearch()

  def _EnsureIndexExists(self, index_name, mapping):
    """Create Elasticsearch index.

    Args:
      index_name: Name of the index.
      mapping: Mapping for the index

    Returns:
      Name of the index.
    """
    try:
      if not self.client.indices.exists(index_name):
        self.client.indices.create(
            index=index_name, body={u'mappings': mapping})
    except ConnectionError:
      raise RuntimeError(u'Unable to connect to Elasticsearch backend.')
    return index_name

  def _GetSanitizedEventValues(self, event_object):
    """Builds a dictionary from an event_object.

    The event object need to be sanitized to prevent certain values from causing
    problems when indexing with Elasticsearch. For example the value of
    the pathspec attribute is a nested dictionary which will cause problems for
    Elasticsearch automatic indexing.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      Dictionary with sanitized event object values.
    """
    event_values = {}
    for attribute_name, attribute_value in event_object.GetAttributes():
      # Ignore the regvalue attribute as it cause issues when indexing
      if attribute_name == u'regvalue':
        continue

      if attribute_name == u'pathspec':
        try:
          attribute_value = JsonPathSpecSerializer.WriteSerialized(
              attribute_value)
        except TypeError:
          continue
      event_values[attribute_name] = attribute_value

    # Add string representation of the timestamp
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

    # Tags needs to be a list for Elasticsearch to index correctly.
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

  def _FlushEventsToElasticSearch(self):
    """Insert events in bulk to Elasticsearch."""
    try:
      self.client.bulk(
          index=self._index, doc_type=self._doc_type, body=self._events)
    except ValueError as e:
      # Ignore problematic events
      logging.warning(u'{0:s}'.format(e))

    # Clear the events list
    self._events = []
    logging.info(u'{0:d} events added'.format(self._counter[u'events']))


class ElasticSearchOutputModule(interface.OutputModule):
  """Output module for Elasticsearch."""

  NAME = u'elastic'
  DESCRIPTION = u'Saves the events into an Elasticsearch database.'

  # Strings longer than this will not be analyzed by elasticsearch.
  _ELASTIC_ANALYZER_STRING_LIMIT = 10922

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(ElasticSearchOutputModule, self).__init__(output_mediator)
    self._doc_type = None
    self._elastic = None
    self._elastic_password = None
    self._elastic_user = None
    self._flush_interval = None
    self._host = None
    self._index_name = None
    self._mapping = None
    self._output_mediator = output_mediator
    self._port = None
    self._raw_fields = False

  def Close(self):
    """Close connection to the Elasticsearch database.

    Sends any remaining buffered events for indexing.
    """
    self._elastic.AddEvent(event_object=None, force_flush=True)

  def SetServerInformation(self, server, port):
    """Set the Elasticsearch server information.

    Args:
      server (str): IP address or hostname of the server.
      port (int): Port number of the server.
    """
    self._host = server
    self._port = port
    logging.info(u'Server address: {0:s}'.format(self._host))
    logging.info(u'Server port: {0:d}'.format(self._port))

  def SetFlushInterval(self, flush_interval):
    """Set the flush interval.

    Args:
      flush_interval (int): Number of events to buffer before bulk insert.
    """
    self._flush_interval = flush_interval
    logging.info(u'Flush interval: {0:d}'.format(self._flush_interval))

  def SetIndexName(self, index_name):
    """Set the index name.

    Args:
      index_name: the index name.
    """
    self._index_name = index_name
    logging.info(u'Index name: {0:s}'.format(self._index_name))

  def SetDocType(self, doc_type):
    """Set the port.

    Args:
      doc_type (str): The document type to use when indexing.
    """
    self._doc_type = doc_type
    logging.info(u'Document type: {0:s}'.format(self._doc_type))

  def SetRawFields(self, raw_fields):
    """Set raw (not analyzed) fields.

    This is used for sorting and aggregations in Elasticsearch.
    https://www.elastic.co/guide/en/elasticsearch/guide/current/
    multi-fields.html

    Args:
      raw_fields (bool): Add not-analyzed index for string fields.
    """
    self._raw_fields = raw_fields
    logging.info(u'Add non analyzed string fields: {0!s}'.format(
        self._raw_fields))

  def SetElasticUser(self, elastic_user):
    """Set the Elastic username.

    Args:
      elastic_user (str): Elastic user to authenticate with.
    """
    self._elastic_user = elastic_user
    logging.info(u'Elastic user: {0:s}'.format(self._elastic_user))

  def SetElasticPassword(self, elastic_password):
    """Set the Elastic password.

    Args:
      elastic_password (str): Elastic password to authenticate with.
    """
    self._elastic_password = elastic_password
    logging.info(u'Elastic password: {0:s}'.format(u'****'))

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._elastic.AddEvent(event_object)

  def WriteHeader(self):
    """Setup the Elasticsearch index."""
    if not self._mapping:
      self._mapping = {}

    if self._raw_fields:
      if self._doc_type not in self._mapping:
        self._mapping[self._doc_type] = {}

      _raw_field_mapping = [{
          u'strings': {
              u'match_mapping_type': u'string',
              u'mapping': {
                  u'fields': {
                      u'raw': {
                          u'type': u'string',
                          u'index': u'not_analyzed',
                          u'ignore_above': self._ELASTIC_ANALYZER_STRING_LIMIT
                      }
                  }
              }
          }
      }]
      self._mapping[self._doc_type][u'dynamic_templates'] = _raw_field_mapping

    self._elastic = ElasticSearchHelper(
        self._output_mediator, self._host, self._port, self._flush_interval,
        self._index_name, self._mapping, self._doc_type,
        elastic_password=self._elastic_password,
        elastic_user=self._elastic_user)
    logging.info(u'Adding events to Elasticsearch..')


manager.OutputManager.RegisterOutput(
    ElasticSearchOutputModule, disabled=Elasticsearch is None)
