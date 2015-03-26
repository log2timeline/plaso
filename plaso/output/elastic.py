# -*- coding: utf-8 -*-
"""An output module that saves data into an ElasticSearch database."""

import logging
import requests
import sys
import uuid

import pyelasticsearch

from plaso.formatters import manager as formatters_manager
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


class ElasticSearchOutput(interface.LogOutputFormatter):
  """Saves the events into an ElasticSearch database."""

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

  NAME = u'elastic'
  DESCRIPTION = u'Saves the events into an ElasticSearch database.'

  def __init__(
      self, store, formatter_mediator, filehandle=sys.stdout, config=None,
      filter_use=None):
    """Initializes the log output formatter object.

    Args:
      store: A storage file object (instance of StorageFile) that defines
             the storage.
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
      config: Optional configuration object, containing config information.
              The default is None.
      filter_use: Optional filter object (instance of FilterObject).
                  The default is None.
    """
    super(ElasticSearchOutput, self).__init__(
        store, formatter_mediator, filehandle=filehandle, config=config,
        filter_use=filter_use)
    self._counter = 0
    self._data = []

    elastic_host = getattr(config, 'elastic_server', '127.0.0.1')
    elastic_port = getattr(config, 'elastic_port', 9200)
    self._elastic_db = pyelasticsearch.ElasticSearch(
        u'http://{0:s}:{1:d}'.format(elastic_host, elastic_port))

    case_name = getattr(config, 'case_name', u'')
    document_type = getattr(config, 'document_type', u'')

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

    # Build up a list of available hostnames in this storage file.
    self._hostnames = {}
    self._preprocesses = {}

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
        timezone=self.zone)
    msg, _ = formatters_manager.FormattersManager.GetMessageStrings(
        self._formatter_mediator, event_object)
    ret_dict['message'] = msg

    source_type, source = formatters_manager.FormattersManager.GetSourceStrings(
        event_object)

    ret_dict['source_short'] = source_type
    ret_dict['source_long'] = source

    hostname = getattr(event_object, 'hostname', '')
    if self.store and not not hostname:
      hostname = self._hostnames.get(event_object.store_number, '-')

    ret_dict['hostname'] = hostname

    # TODO: move this into a base output class.
    username = getattr(event_object, 'username', '-')
    if self.store:
      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)

        if check_user != '-':
          username = check_user

    if username == '-' and hasattr(event_object, 'user_sid'):
      username = getattr(event_object, 'user_sid', '-')

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

    Each event object contains both attributes that are considered "reserved"
    and others that aren't. The 'raw' representation of the object makes a
    distinction between these two types as well as extracting the format
    strings from the object.

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
    if self.store:
      self._hostnames = helper.BuildHostDict(self.store)
      for info in self.store.GetStorageInformation():
        if hasattr(info, 'store_range'):
          for store_number in range(info.store_range[0], info.store_range[1]):
            self._preprocesses[store_number] = info

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


manager.OutputManager.RegisterOutput(ElasticSearchOutput)
