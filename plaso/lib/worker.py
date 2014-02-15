#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The event extraction worker."""

import logging
import os
import pdb

from dfvfs.lib import definitions
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso import parsers   # pylint: disable-msg=unused-import
from plaso.lib import classifier
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import utils


class EventExtractionWorker(queue.PathSpecQueueConsumer):
  """Class that extracts events for files and directories.

  This class is designed to watch a queue for path specifications of files
  and directories (file entries) for which events need to be extracted.

  The event extraction worker needs to determine if a parser suitable
  for parsing a particular file is available. All extracted event objects
  are pushed on a storage queue for further processing.
  """

  def __init__(
      self, identifier, process_queue, storage_queue_producer, config, pre_obj):
    """Initializes the event extraction worker object.

    Args:
      identifier: A thread identifier, usually an incrementing integer.
      process_queue: the process queue (instance of Queue).
      storage_queue_producer: the storage queue producer (instance of
                              EventObjectQueueProducer).
      config: A config object that contains all the tool's configuration.
      pre_obj: A preprocess object containing information collected from
               image (instance of PreprocessObject).
    """
    super(EventExtractionWorker, self).__init__(process_queue)
    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    self._resolver_context = context.Context()
    self._identifier = identifier
    self._parsers = putils.FindAllParsers(
        pre_obj, config, getattr(config, 'parsers', ''))
    self._pre_obj = pre_obj
    self._storage_queue_producer = storage_queue_producer
    if pre_obj:
      self._user_mapping = pre_obj.GetUserMappings()
    else:
      self._user_mapping = {}
    self.config = config

    self._filter = None
    filter_query = getattr(config, 'filter', None)
    if filter_query:
      self._filter = pfilter.GetMatcher(filter_query)

  # TODO: implement PathBundle support, if needed.
  def _ConsumePathSpec(self, path_spec):
    """Consumes a path specification callback for ConsumePathSpecs."""
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        path_spec, resolver_context=self._resolver_context)
    try:
      self.ParseFile(file_entry)
    except IOError as exception:
      logging.warning(u'Unable to parse file: {0:s} with error: {1:s}'.format(
          path_spec.comparable, exception))

    if self.config.open_files:
      try:
        for sub_file_entry in classifier.Classifier.SmartOpenFiles(file_entry):
          self.ParseFile(sub_file_entry)
      except IOError as exception:
        logging.warning(
            u'Unable to parse file: {0:s} with error: {1:s}'.format(
                file_entry.path_spec.comparable, exception))

  def Run(self):
    """Start the worker, monitor the queue and parse files."""
    self.pid = os.getpid()
    logging.info(
        u'Worker {0:d} (PID: {1:d}) started monitoring process queue.'.format(
        self._identifier, self.pid))

    self.ConsumePathSpecs()

    logging.info(
        'Worker {0:d} (PID: {1:d}) stopped monitoring process queue.'.format(
        self._identifier, os.getpid()))

  def _ParseEvent(self, event_object, file_entry, parser_name, stat_obj):
    """Adjust value of an extracted EventObject before storing it."""
    # TODO: Make some more adjustments to the event object.
    # Need to apply time skew, and other information extracted from
    # the configuration of the tool.

    # TODO: dfVFS refactor: deperecate text_prepend in favor of an event tag.
    if self.config.text_prepend:
      event_object.text_prepend = self.config.text_prepend

    file_path = getattr(file_entry.path_spec, 'location', file_entry.name)
    # If we are parsing a mount point we don't want to include the full
    # path to file's location here, we are only interested in the relative
    # path to the mount point.
    type_indicator = getattr(file_entry.path_spec, 'type_indicator', '')
    # TODO: Solve this differently, quite possibly inside dfVFS using mount
    # path spec.
    if type_indicator == definitions.TYPE_INDICATOR_OS and getattr(
        self.config, 'os', None):
      mount_path = getattr(self.config, 'filename', '')
      if mount_path:
        # Let's keep the end separator so paths begin with '/' or '\'.
        if mount_path.endswith(os.sep):
          mount_path = mount_path[:-1]
        _, _, file_path = file_path.partition(mount_path)

    # TODO: dfVFS refactor: move display name to output since the path
    # specification contains the full information.
    event_object.display_name = u'{:s}:{:s}'.format(
        file_entry.path_spec.type_indicator, file_path)

    event_object.filename = file_path
    event_object.pathspec = file_entry.path_spec
    event_object.parser = parser_name

    if hasattr(self._pre_obj, 'hostname'):
      event_object.hostname = self._pre_obj.hostname
    if not hasattr(event_object, 'inode') and hasattr(stat_obj, 'ino'):
      event_object.inode = utils.GetInodeValue(stat_obj.ino)

    # Set the username that is associated to the record.
    if getattr(event_object, 'user_sid', None) and self._user_mapping:
      username = self._user_mapping.get(event_object.user_sid, None)
      if username:
        event_object.username = username

    if not self._filter or self._filter.Matches(event_object):
      self._storage_queue_producer.ProduceEventObject(event_object)

  def ParseFile(self, file_entry):
    """Run through classifier and appropriate parsers.

    Args:
      file_entry: A file entry object.
    """
    logging.debug(u'[ParseFile] Parsing: {0:s}'.format(
        file_entry.path_spec.comparable))

    # TODO: Not go through all parsers, just the ones
    # that the classifier classifies the file as.
    # Do this when classifier is ready.
    # The classifier will return a "type" back, which refers
    # to a key in the self._parsers dict. If the results are
    # inconclusive the "all" key is used, or the key is not found.
    # key = self._parsers.get(classification, 'all')
    stat_obj = file_entry.GetStat()
    for parsing_object in self._parsers['all']:
      logging.debug(u'Checking [{0:s}] against: {1:s}'.format(
          file_entry.name, parsing_object.parser_name))
      try:
        for event_object in parsing_object.Parse(file_entry):
          if not event_object:
            continue

          if isinstance(event_object, event.EventObject):
            self._ParseEvent(
                event_object, file_entry, parsing_object.parser_name, stat_obj)
          elif isinstance(event_object, event.EventContainer):
            for sub_event in event_object:
              self._ParseEvent(
                  sub_event, file_entry, parsing_object.parser_name, stat_obj)

      except errors.UnableToParseFile as exception:
        logging.debug(u'Not a {0:s} file ({1:s}) - {2:s}'.format(
            parsing_object.parser_name, file_entry.name, exception))

      except IOError as exception:
        logging.debug(
            u'[{0:s}] Unable to parse: {1:s} with error: {2:s}'.format(
                parsing_object.parser_name, file_entry.path_spec.comparable,
                exception))

      # Casting a wide net, catching all exceptions. Done to keep the worker
      # running, despite the parser hitting errors, so the worker doesn't die
      # if a single file is corrupted or there is a bug in a parser.
      except Exception as exception:
        logging.warning(
            u'[{0:s}] Unable to process file: {1:s} with error: {2:s}.'.format(
                parsing_object.parser_name, file_entry.path_spec.comparable,
                exception))
        logging.debug(
            u'The path specification that caused the error: {0:s}'.format(
                file_entry.path_spec.comparable))
        logging.exception(exception)

        # Check for debug mode and single-threaded, then we would like
        # to debug this problem.
        if self.config.single_thread and self.config.debug:
          pdb.post_mortem()

    logging.debug(u'Done parsing: {0:s}'.format(
        file_entry.path_spec.comparable))
