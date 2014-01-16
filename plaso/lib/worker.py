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

from plaso import parsers   # pylint: disable-msg=unused-import
from plaso.lib import classifier
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import utils
from plaso.pvfs import pfile
from plaso.pvfs import pvfs


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
    # We need a file system cache per thread to prevent multi threading
    # issues with file entries stored in images.
    self._fscache = pvfs.FilesystemCache()
    self._identifier = identifier
    self._parsers = putils.FindAllParsers(
        pre_obj, config, getattr(config, 'parsers', ''))
    self._pre_obj = pre_obj
    self._storage_queue_producer = storage_queue_producer
    self._user_mapping = pre_obj.GetUserMappings()
    self.config = config

    self._filter = None
    filter_query = getattr(config, 'filter', None)
    if filter_query:
      self._filter = pfilter.GetMatcher(filter_query)

  # TODO: implement PathBundle support, if needed.
  def _ConsumePathSpec(self, path_spec):
    """Consumes a path specification callback for ConsumePathSpecs."""
    if hasattr(self.config, 'text_prepend'):
      path_spec.path_prepend = self.config.text_prepend

    try:
      file_entry = pfile.PFileResolver.OpenFileEntry(
          path_spec, fscache=self._fscache)
      self.ParseFile(file_entry)
    except IOError as exception:
      logging.warning(u'Unable to parse file: {0:s} with error: {1:s}'.format(
          path_spec.comparable, exception))
      logging.warning(u'Proto\n{0:s}\n{1:s}\n{2:s}'.format(
          '-+' * 20, path_spec.comparable, '-+' * 20))

    if self.config.open_files:
      for sub_file_entry in classifier.SmartOpenFiles(file_entry):
        try:
          self.ParseFile(sub_file_entry)
        except IOError as exception:
          logging.warning((
              u'Unable to parse file: {0:s} within file: {1:s} with error: '
              u'{2:s}').format(
                  sub_file_entry.display_name, path_spec.comparable, exception))

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

    event_object.display_name = file_entry.display_name
    event_object.filename = file_entry.name
    event_object.pathspec = file_entry.pathspec_root
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
    logging.debug(u'[ParseFile] Parsing: {0:s}'.format(file_entry.display_name))

    # TODO: Not go through all parsers, just the ones
    # that the classifier classifies the file as.
    # Do this when classifier is ready.
    # The classifier will return a "type" back, which refers
    # to a key in the self._parsers dict. If the results are
    # inconclusive the "all" key is used, or the key is not found.
    # key = self._parsers.get(classification, 'all')
    stat_obj = file_entry.Stat()
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

      except errors.UnableToParseFile as e:
        logging.debug(u'Not a {0:s} file ({1:s}) - {2:s}'.format(
            parsing_object.parser_name, file_entry.name, e))
      except IOError as e:
        logging.debug(u'Unable to parse: {0:s} [{1:s}] using {2:s}'.format(
            file_entry.name, file_entry.display_name,
            parsing_object.parser_name))

      # Casting a wide net, catching all exceptions. Done to keep the worker
      # running, despite the parser hitting errors, so the worker doesn't die
      # if a single file is corrupted or there is a bug in a parser.
      except Exception as exception:
        logging.warning((
            u'Unable to process file: {0:s} using module {1:s} with error: '
            u'{2:s}.').format(
                file_entry.name, parsing_object.parser_name, exception))
        logging.debug((
            u'The PathSpec that caused the error:\n(root)\n{0:s}\n'
            u'{1:s}').format(
                file_entry.pathspec_root.comparable,
                file_entry.pathspec.comparable))
        logging.exception(e)

        # Check for debug mode and single-threaded, then we would like
        # to debug this problem.
        if self.config.single_thread and self.config.debug:
          pdb.post_mortem()

    logging.debug(u'[ParseFile] Parsing DONE: {0:s}'.format(
        file_entry.display_name))
