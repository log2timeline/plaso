# -*- coding: utf-8 -*-
"""Timesketch output module."""

from __future__ import unicode_literals

import logging

try:
  from flask import current_app
  import timesketch
  from timesketch.models import db_session
  from timesketch.models.sketch import SearchIndex
  from timesketch.models.user import User
except ImportError:
  timesketch = None

from plaso.output import interface
from plaso.output import manager
from plaso.output.elastic import ElasticSearchHelper

# Configure Elasticsearch logger
elastic_logger = logging.getLogger('elasticsearch')
elastic_logger.propagate = False


class TimesketchOutputModule(interface.OutputModule):
  """Output module for Timesketch."""

  NAME = 'timesketch'
  DESCRIPTION = 'Create a Timesketch timeline.'

  def __init__(self, output_mediator):
    """Initializes a Timesketch output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(TimesketchOutputModule, self).__init__(output_mediator)
    self._doc_type = None
    self._elastic = None
    self._flush_interval = None
    self._host = None
    self._index_name = None
    self._mapping = None
    self._port = None
    self._timesketch = timesketch.create_app()
    self._username = None

    hostname = self._output_mediator.GetStoredHostname()
    if hostname:
      logging.info('Hostname: {0:s}'.format(hostname))
      self._timeline_name = hostname
    else:
      self._timeline_name = None

  def Close(self):
    """Closes the connection to TimeSketch Elasticsearch database.

    Sends the remaining events for indexing and removes the processing status on
    the Timesketch search index object.
    """
    self._elastic.AddEvent(None, force_flush=True)
    with self._timesketch.app_context():
      search_index = SearchIndex.query.filter_by(
          index_name=self._index_name).first()
      search_index.status.remove(search_index.status[0])
      db_session.add(search_index)
      db_session.commit()

  def GetMissingArguments(self):
    """Return a list of arguments that are missing from the input.

    Returns:
      list[str]: names of arguments that are required by the module and have
          not been specified.
    """
    if not self._timeline_name:
      return ['timeline_name']
    return []

  def SetDocType(self, doc_type):
    """Sets the Elasticsearch document type.

    Args:
      doc_type (str): document type.
    """
    self._doc_type = doc_type
    logging.info('Document type: {0:s}'.format(self._doc_type))

  def SetFlushInterval(self, flush_interval):
    """Sets the flush interval.

    Args:
      flush_interval (int): flush interval.
    """
    self._flush_interval = flush_interval
    logging.info('Flush interval: {0:d}'.format(self._flush_interval))

  def SetIndexName(self, index_name):
    """Sets the index name.

    Args:
      index_name (str): index name.
    """
    self._index_name = index_name
    logging.info('Index name: {0:s}'.format(self._index_name))

  def SetTimelineName(self, timeline_name):
    """Sets the timeline name.

    Args:
      timeline_name (str): timeline name.
    """
    self._timeline_name = timeline_name
    logging.info('Timeline name: {0:s}'.format(self._timeline_name))

  def SetUserName(self, username):
    """Sets the username of the user that should own the timeline.

    Args:
      username (str): username.
    """
    self._username = username
    logging.info('Owner of the timeline: {0:s}'.format(self._username))

  def WriteEventBody(self, event):
    """Writes the body of an event to the output.

    Args:
      event (EventObject): event.
    """
    self._elastic.AddEvent(event)

  def WriteHeader(self):
    """Setup the Elasticsearch index and the Timesketch database object.

    Creates the Elasticsearch index with Timesketch specific settings and the
    Timesketch SearchIndex database object.
    """
    # This cannot be static because we use the value of self._doc_type from
    # arguments.
    _document_mapping = {
        self._doc_type: {
            'properties': {
                'timesketch_label': {
                    'type': 'nested'
                }
            }
        }
    }

    # Get Elasticsearch host and port from Timesketch configuration.
    with self._timesketch.app_context():
      _host = current_app.config['ELASTIC_HOST']
      _port = current_app.config['ELASTIC_PORT']

    self._elastic = ElasticSearchHelper(
        self._output_mediator, _host, _port, self._flush_interval,
        self._index_name, _document_mapping, self._doc_type)

    user = None
    if self._username:
      user = User.query.filter_by(username=self._username).first()
      if not user:
        raise RuntimeError(
            'Unknown Timesketch user: {0:s}'.format(self._username))
    else:
      logging.warning('Timeline will be visible to all Timesketch users')

    with self._timesketch.app_context():
      search_index = SearchIndex.get_or_create(
          name=self._timeline_name, description=self._timeline_name, user=user,
          index_name=self._index_name)

      # Grant the user read permission on the mapping object and set status.
      # If user is None the timeline becomes visible to all users.
      search_index.grant_permission(user=user, permission='read')

      # In case we have a user grant additional permissions.
      if user:
        search_index.grant_permission(user=user, permission='write')
        search_index.grant_permission(user=user, permission='delete')

      # Let the Timesketch UI know that the timeline is processing.
      search_index.set_status('processing')

      # Save the mapping object to the Timesketch database.
      db_session.add(search_index)
      db_session.commit()

    logging.info('Adding events to Timesketch.')


manager.OutputManager.RegisterOutput(
    TimesketchOutputModule, disabled=timesketch is None)
