# -*- coding: utf-8 -*-
"""An output module that saves data into an ElasticSearch database."""

import logging
import requests
import sys
import uuid

import pyelasticsearch

from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import manager


class ElasticSearchOutputModule(interface.OutputModule):
  """Saves the events into an ElasticSearch database."""

  NAME = u'elastic'
  DESCRIPTION = u'Saves the events into an ElasticSearch database.'

  # Add configuration data for this output module.
  ARGUMENTS = [
      ('--case_name', {
          'dest': 'case_name',
          'type': unicode,
          'help': 'Add a case name. This will be the name of the index in '
                  'ElasticSearch.',
          'action': 'store',
          'default': ''}),
      ('--document_type', {
          'dest': 'document_type',
          'type': unicode,
          'help': 'Name of the document type. This is the name of the document '
                  'type that will be used in ElasticSearch.',
          'action': 'store',
          'default': ''}),
      ('--elastic_server_ip', {
          'dest': 'elastic_server',
          'type': unicode,
          'help': (
              'If the ElasticSearch database resides on a different server '
              'than localhost this parameter needs to be passed in. This '
              'should be the IP address or the hostname of the server.'),
          'action': 'store',
          'default': '127.0.0.1'}),
      ('--elastic_port', {
          'dest': 'elastic_port',
          'type': int,
          'help': (
              'By default ElasticSearch uses the port number 9200, if the '
              'database is listening on a different port this parameter '
              'can be defined.'),
          'action': 'store',
          'default': 9200})]

  def __init__(self, output_mediator, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
    """
    super(ElasticSearchOutputModule, self).__init__(output_mediator, **kwargs)
    self._counter = 0
    self._data = []

    elastic_host = self._output_mediator.GetConfigurationValue(
        u'elastic_server', default_value=u'127.0.0.1')
    elastic_port = self._output_mediator.GetConfigurationValue(
        u'elastic_port', default_value=9200)
    self._elastic_db = pyelasticsearch.ElasticSearch(
        u'http://{0:s}:{1:d}'.format(elastic_host, elastic_port))

    case_name = self._output_mediator.GetConfigurationValue(
        u'case_name', default_value=u'')
    document_type = self._output_mediator.GetConfigurationValue(
        u'document_type', default_value=u'')

    # case_name becomes the index name in Elastic.
    if case_name:
      self._index_name = case_name.lower()
    else:
      self._index_name = uuid.uuid4().hex

    # Name of the doc_type that holds the plaso events.
    if document_type:
      self._doc_type = document_type.lower()
    else:
      self._doc_type = u'event'

  def _EventToDict(self, event_object):
    """Returns a dict built from an event object.

    Args:
      event_object: the event object (instance of EventObject).
    """
    ret_dict = event_object.GetValues()

    # Get rid of few attributes that cause issues (and need correcting).
    if 'pathspec' in ret_dict:
      del ret_dict['pathspec']

    #if 'tag' in ret_dict:
    #  del ret_dict['tag']
    #  tag = getattr(event_object, 'tag', None)
    #  if tag:
    #    tags = tag.tags
    #    ret_dict['tag'] = tags
    #    if getattr(tag, 'comment', ''):
    #      ret_dict['comment'] = tag.comment
    ret_dict['tag'] = []

    # To not overload the index, remove the regvalue index.
    if 'regvalue' in ret_dict:
      del ret_dict['regvalue']

    # Adding attributes in that are calculated/derived.
    # We want to remove millisecond precision (causes some issues in
    # conversion).
    ret_dict['datetime'] = timelib.Timestamp.CopyToIsoFormat(
        timelib.Timestamp.RoundToSeconds(event_object.timestamp),
        timezone=self._output_mediator.timezone)

    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    ret_dict['message'] = message

    source_short, source = self._output_mediator.GetFormattedSources(
        event_object)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              getattr(event_object, u'data_type', u'UNKNOWN')))

    ret_dict['source_short'] = source_short
    ret_dict['source_long'] = source

    hostname = self._output_mediator.GetHostname(event_object)
    ret_dict['hostname'] = hostname

    username = self._output_mediator.GetUsername(event_object)
    ret_dict['username'] = username

    return ret_dict

  def Close(self):
    """Disconnects from the elastic search server."""
    self._elastic_db.bulk_index(self._index_name, self._doc_type, self._data)
    self._data = []
    sys.stdout.write('. [DONE]\n')
    sys.stdout.write('ElasticSearch index name: {0:s}\n'.format(
        self._index_name))
    sys.stdout.flush()

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._data.append(self._EventToDict(event_object))
    self._counter += 1

    # Check if we need to flush.
    if self._counter % 5000 == 0:
      self._elastic_db.bulk_index(self._index_name, self._doc_type, self._data)
      self._data = []
      sys.stdout.write('.')
      sys.stdout.flush()

  def WriteHeader(self):
    """Writes the header to the output."""
    mapping = {
        self._doc_type: {
            u'_timestamp': {
                u'enabled': True,
                u'path': 'datetime',
                u'format': 'date_time_no_millis'},
        }
    }
    # Check if the mappings exist (only create if not there).
    try:
      old_mapping_index = self._elastic_db.get_mapping(self._index_name)
      old_mapping = old_mapping_index.get(self._index_name, {})
      if self._doc_type not in old_mapping:
        self._elastic_db.put_mapping(
            self._index_name, self._doc_type, mapping=mapping)
    except (pyelasticsearch.ElasticHttpNotFoundError,
            pyelasticsearch.exceptions.ElasticHttpError):
      try:
        self._elastic_db.create_index(self._index_name, settings={
            'mappings': mapping})
      except pyelasticsearch.IndexAlreadyExistsError:
        raise RuntimeError(u'Unable to created the index')
    except requests.exceptions.ConnectionError as exception:
      logging.error(
          u'Unable to proceed, cannot connect to ElasticSearch backend '
          u'with error: {0:s}.\nPlease verify connection.'.format(exception))
      raise RuntimeError(u'Unable to connect to ElasticSearch backend.')

    # pylint: disable=unexpected-keyword-arg
    self._elastic_db.health(wait_for_status='yellow')

    sys.stdout.write('Inserting data')
    sys.stdout.flush()


manager.OutputManager.RegisterOutput(ElasticSearchOutputModule)
