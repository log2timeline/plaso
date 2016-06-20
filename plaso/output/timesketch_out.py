# -*- coding: utf-8 -*-
"""An output module that saves events to Timesketch."""

import logging

try:
  from flask import current_app
  import timesketch
  from timesketch.models import db_session
  from timesketch.models.sketch import SearchIndex
except ImportError:
  timesketch = None

from plaso.output import interface
from plaso.output import manager
from plaso.output.elastic import ElasticSearchHelper

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

    self._output_mediator = output_mediator
    self._host = None
    self._port = None
    self._flush_interval = None
    self._index_name = None
    self._doc_type = None
    self._mapping = None
    self._elastic = None
    self._timesketch = timesketch.create_app()

    hostname = self._output_mediator.GetStoredHostname()
    if hostname:
      logging.info(u'Hostname: {0:s}'.format(hostname))
      self._timeline_name = hostname
    else:
      self._timeline_name = None

  def Close(self):
    """Closes the connection to TimeSketch Elasticsearch database.

    Sends the remaining events for indexing and removes the processing status on
    the Timesketch search index object.
    """
    self._elastic.AddEvent(event_object=None, force_flush=True)
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
    logging.info(u'Flush interval: {0:d}'.format(self._flush_interval))

  def SetIndexName(self, index_name):
    """Set the index name.

    Args:
      index_name: the index name.
    """
    self._index_name = index_name
    logging.info(u'Index name: {0:s}'.format(self._index_name))

  def SetTimelineName(self, timeline_name):
    """Set the timeline name.

    Args:
      timeline_name: the timeline name.
    """
    self._timeline_name = timeline_name
    logging.info(u'Timeline name: {0:s}'.format(self._timeline_name))

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._elastic.AddEvent(event_object)

  def WriteHeader(self):
    """Setup the Elasticsearch index and the Timesketch database object.

    Creates the Elasticsearch index with Timesketch specific settings and the
    Timesketch SearchIndex database object.
    """
    # This cannot be static because we use the value of self._doc_type from
    # arguments.
    _document_mapping = {
        self._doc_type: {
            u'properties': {
                u'timesketch_label': {
                    u'type': u'nested'
                }
            }
        }
    }
    _doc_type = u'plaso_event'

    # Get Elasticsearch host and port from Timesketch configuration.
    with self._timesketch.app_context():
      _host = current_app.config[u'ELASTIC_HOST']
      _port = current_app.config[u'ELASTIC_PORT']

    self._elastic = ElasticSearchHelper(
        self._output_mediator, _host, _port, self._flush_interval,
        self._index_name, _document_mapping, _doc_type)

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
