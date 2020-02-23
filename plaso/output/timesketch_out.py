# -*- coding: utf-8 -*-
"""Timesketch output module."""

from __future__ import unicode_literals

try:
  from flask import current_app
  import timesketch
  from timesketch.models import db_session as timesketch_db_session
  from timesketch.models import sketch as timesketch_sketch
  from timesketch.models import user as timesketch_user
except ImportError:
  timesketch = None

from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_elastic


class TimesketchOutputModule(shared_elastic.SharedElasticsearchOutputModule):
  """Output module for Timesketch."""

  NAME = 'timesketch'
  DESCRIPTION = 'Create a Timesketch timeline.'

  def __init__(self, output_mediator):
    """Initializes a Timesketch output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    hostname = output_mediator.GetStoredHostname()
    if hostname:
      logger.debug('Hostname: {0:s}'.format(hostname))

    super(TimesketchOutputModule, self).__init__(output_mediator)
    self._timeline_name = hostname
    self._timeline_owner = None
    self._timesketch = timesketch.create_app()

  def Close(self):
    """Closes the connection to TimeSketch Elasticsearch database.

    Sends the remaining events for indexing and removes the processing status on
    the Timesketch search index object.
    """
    super(TimesketchOutputModule, self).Close()

    with self._timesketch.app_context():
      search_index = timesketch_sketch.SearchIndex.query.filter_by(
          index_name=self._index_name).first()
      search_index.set_status('ready')

  def GetMissingArguments(self):
    """Retrieves a list of arguments that are missing from the input.

    Returns:
      list[str]: names of arguments that are required by the module and have
          not been specified.
    """
    if not self._timeline_name:
      return ['timeline_name']
    return []

  def SetTimelineName(self, timeline_name):
    """Sets the timeline name.

    Args:
      timeline_name (str): timeline name.
    """
    self._timeline_name = timeline_name
    logger.info('Timeline name: {0:s}'.format(self._timeline_name))

  def SetTimelineOwner(self, username):
    """Sets the username of the user that should own the timeline.

    Args:
      username (str): username.
    """
    self._timeline_owner = username
    logger.info('Owner of the timeline: {0!s}'.format(self._timeline_owner))

  def WriteHeader(self):
    """Sets up the Elasticsearch index and the Timesketch database object.

    Creates the Elasticsearch index with Timesketch specific settings and the
    Timesketch SearchIndex database object.
    """
    # This cannot be static because we use the value of self._document_type
    # from arguments.
    mappings = {
        'properties': {
            'timesketch_label': {
                'type': 'nested'
            },
            'datetime': {
                'type': 'date'
            }
        }
    }

    # TODO: Remove once Elasticsearch v6.x is deprecated.
    if self._GetClientMajorVersion() < 7:
      mappings = {self._document_type: mappings}

    # Get Elasticsearch host and port from Timesketch configuration.
    with self._timesketch.app_context():
      self._host = current_app.config['ELASTIC_HOST']
      self._port = current_app.config['ELASTIC_PORT']

    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, mappings)

    user = None
    if self._timeline_owner:
      user = timesketch_user.User.query.filter_by(
          username=self._timeline_owner).first()
      if not user:
        raise RuntimeError(
            'Unknown Timesketch user: {0:s}'.format(self._timeline_owner))
    else:
      logger.warning('Timeline will be visible to all Timesketch users')

    with self._timesketch.app_context():
      search_index = timesketch_sketch.SearchIndex.get_or_create(
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
      timesketch_db_session.add(search_index)
      timesketch_db_session.commit()

    logger.debug('Adding events to Timesketch.')


manager.OutputManager.RegisterOutput(TimesketchOutputModule, disabled=(
    shared_elastic.elasticsearch is None or timesketch is None))
