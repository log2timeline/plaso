# -*- coding: utf-8 -*-
"""Shared functionality for Elasticsearch output modules."""

from __future__ import unicode_literals

import os
import logging

from dfvfs.serializer.json_serializer import JsonPathSpecSerializer

try:
  import elasticsearch
except ImportError:
  elasticsearch = None

from plaso.lib import errors
from plaso.lib import py2to3
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
    self._use_ssl = None
    self._ca_certs = None
    self._url_prefix = None

  def _Connect(self):
    """Connects to an Elasticsearch server."""
    elastic_host = {'host': self._host, 'port': self._port}

    if self._url_prefix:
      elastic_host['url_prefix'] = self._url_prefix

    elastic_http_auth = None
    if self._username is not None:
      elastic_http_auth = (self._username, self._password)

    self._client = elasticsearch.Elasticsearch(
        [elastic_host],
        http_auth=elastic_http_auth,
        use_ssl=self._use_ssl,
        ca_certs=self._ca_certs
    )

    logger.debug(
        ('Connected to Elasticsearch server: {0:s} port: {1:d}'
         'URL prefix {2!s}.').format(self._host, self._port, self._url_prefix))

  def _CreateIndexIfNotExists(self, index_name, mappings):
    """Creates an Elasticsearch index if it does not exist.

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

    except elasticsearch.exceptions.ConnectionError as exception:
      raise RuntimeError(
          'Unable to create Elasticsearch index with error: {0!s}'.format(
              exception))

  def _FlushEvents(self):
    """Inserts the buffered event documents into Elasticsearch."""
    try:
      # pylint: disable=unexpected-keyword-arg
      bulk_arguments = {
          'body': self._event_documents,
          'index': self._index_name,
          'request_timeout': self._DEFAULT_REQUEST_TIMEOUT}

      # TODO: Remove once Elasticsearch v6.x is deprecated.
      if self._GetClientMajorVersion() < 7:
        bulk_arguments['doc_type'] = self._document_type

      self._client.bulk(**bulk_arguments)

    except (
        ValueError,
        elasticsearch.exceptions.ElasticsearchException) as exception:
      # Ignore problematic events
      logger.warning('Unable to bulk insert with error: {0!s}'.format(
          exception))

    logger.debug('Inserted {0:d} events into Elasticsearch'.format(
        self._number_of_buffered_events))

    self._event_documents = []
    self._number_of_buffered_events = 0

  def _GetSanitizedEventValues(self, event, event_data, event_tag):
    """Sanitizes the event for use in Elasticsearch.

    The event values need to be sanitized to prevent certain values from
    causing problems when indexing with Elasticsearch. For example the path
    specification is a nested dictionary which will cause problems for
    Elasticsearch automatic indexing.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, object]: sanitized event values.

    Raises:
      NoFormatterFound: if no event formatter can be found to match the data
          type in the event data.
    """
    event_values = {}
    for attribute_name, attribute_value in event_data.GetAttributes():
      # TODO: remove regvalue, which is kept for backwards compatibility.
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

      if isinstance(attribute_value, py2to3.BYTES_TYPE):
        # Some parsers have written bytes values to storage.
        attribute_value = attribute_value.decode('utf-8', 'replace')
        logger.warning(
            'Found bytes value for attribute "{0:s}" for data type: '
            '{1!s}. Value was converted to UTF-8: "{2:s}"'.format(
                attribute_name, event_data.data_type, attribute_value))
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

    event_values['timestamp'] = event.timestamp
    event_values['timestamp_desc'] = event.timestamp_desc

    message, _ = self._output_mediator.GetFormattedMessages(event_data)
    if message is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    event_values['message'] = message

    # Tags needs to be a list for Elasticsearch to index correctly.
    labels = []
    if event_tag:
      try:
        labels = list(event_tag.labels)
      except (AttributeError, KeyError):
        pass

    event_values['tag'] = labels

    source_short, source = self._output_mediator.GetFormattedSources(
        event, event_data)
    if source is None or source_short is None:
      data_type = getattr(event_data, 'data_type', 'UNKNOWN')
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    event_values['source_short'] = source_short
    event_values['source_long'] = source

    return event_values

  def _InsertEvent(self, event, event_data, event_tag):
    """Inserts an event.

    Events are buffered in the form of documents and inserted to Elasticsearch
    when the flush interval (threshold) has been reached.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    event_document = {'index': {'_index': self._index_name}}

    # TODO: Remove once Elasticsearch v6.x is deprecated.
    if self._GetClientMajorVersion() < 7:
      event_document['index']['_type'] = self._document_type

    event_values = self._GetSanitizedEventValues(event, event_data, event_tag)

    self._event_documents.append(event_document)
    self._event_documents.append(event_values)
    self._number_of_buffered_events += 1

    if self._number_of_buffered_events > self._flush_interval:
      self._FlushEvents()

  def Close(self):
    """Closes connection to Elasticsearch.

    Inserts any remaining buffered event documents.
    """
    self._FlushEvents()

    self._client = None

  def _GetClientMajorVersion(self):
    """Get the major version of the Elasticsearch client library.

    Returns:
      int: Major version number.
    """
    return elasticsearch.__version__[0]

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
    logger.debug('Elasticsearch server: {0!s} port: {1:d}'.format(
        server, port))

  def SetUsername(self, username):
    """Sets the username.

    Args:
      username (str): username to authenticate with.
    """
    self._username = username
    logger.debug('Elasticsearch username: {0!s}'.format(username))

  def SetUseSSL(self, use_ssl):
    """Sets the use of ssl.

    Args:
      use_ssl (bool): enforces use of ssl.
    """
    self._use_ssl = use_ssl
    logger.debug('Elasticsearch use_ssl: {0!s}'.format(use_ssl))

  def SetCACertificatesPath(self, ca_certificates_path):
    """Sets the path to the CA certificates.

    Args:
      ca_certificates_path (str): path to file containing a list of root
        certificates to trust.

    Raises:
      BadConfigOption: if the CA certificates file does not exist.
    """
    if not ca_certificates_path:
      return

    if not os.path.exists(ca_certificates_path):
      raise errors.BadConfigOption(
          'No such certificate file: {0:s}.'.format(ca_certificates_path))

    self._ca_certs = ca_certificates_path
    logger.debug('Elasticsearch ca_certs: {0!s}'.format(ca_certificates_path))

  def SetURLPrefix(self, url_prefix):
    """Sets the URL prefix.

    Args:
      url_prefix (str): URL prefix.
    """
    self._url_prefix = url_prefix
    logger.debug('Elasticsearch URL prefix: {0!s}')

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    self._InsertEvent(event, event_data, event_tag)
