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
import threading

from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

try:
  from guppy import hpy
except ImportError:
  hpy = None

from plaso.engine import classifier
from plaso.lib import errors
from plaso.lib import queue
from plaso.parsers import context as parsers_context
from plaso.parsers import manager as parsers_manager


class EventExtractionWorker(queue.PathSpecQueueConsumer):
  """Class that extracts events for files and directories.

  This class is designed to watch a queue for path specifications of files
  and directories (file entries) for which events need to be extracted.

  The event extraction worker needs to determine if a parser suitable
  for parsing a particular file is available. All extracted event objects
  are pushed on a storage queue for further processing.
  """

  def __init__(
      self, identifier, process_queue, event_queue_producer,
      parse_error_queue_producer, knowledge_base, rpc_proxy=None):
    """Initializes the event extraction worker object.

    Args:
      identifier: A thread identifier, usually an incrementing integer.
      process_queue: the process queue (instance of Queue).
      event_queue_producer: the event object queue producer (instance of
                            EventObjectQueueProducer).
      parse_error_queue_producer: the parse error queue producer (instance of
                            ParseErrorQueueProducer).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
      rpc_proxy: A proxy object (instance of proxy.ProxyServer) that can be
                 used to setup RPC functionality for the worker. This is
                 optional and if not provided the worker will not listen to RPC
                 requests. The default value is None.
    """
    super(EventExtractionWorker, self).__init__(process_queue)
    self._enable_debug_output = False
    self._identifier = identifier
    self._knowledge_base = knowledge_base
    self._open_files = False
    self._parser_context = parsers_context.ParserContext(
        event_queue_producer, parse_error_queue_producer, knowledge_base)
    self._filestat_parser_object = None
    self._parser_objects = None
    self._rpc_proxy = rpc_proxy

    # We need a resolver context per process to prevent multi processing
    # issues with file objects stored in images.
    self._resolver_context = context.Context()
    self._single_process_mode = False
    self._event_queue_producer = event_queue_producer
    self._parse_error_queue_producer = parse_error_queue_producer

    # Attributes that contain the current status of the worker.
    self._current_working_file = u''
    self._is_running = False

    # Attributes for profiling.
    self._enable_profiling = False
    self._heapy = None
    self._profiling_sample = 0
    self._profiling_sample_rate = 1000
    self._profiling_sample_file = u'{0!s}.hpy'.format(self._identifier)

  def _ConsumePathSpec(self, path_spec):
    """Consumes a path specification callback for ConsumePathSpecs."""
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        path_spec, resolver_context=self._resolver_context)

    if file_entry is None:
      logging.warning(u'Unable to open file entry: {0:s}'.format(
          path_spec.comparable))
      return

    try:
      self.ParseFileEntry(file_entry)
    except IOError as exception:
      logging.warning(u'Unable to parse file: {0:s} with error: {1:s}'.format(
          path_spec.comparable, exception))

  def _ProfilingStart(self):
    """Starts the profiling."""
    self._heapy.setrelheap()
    self._profiling_sample = 0

    try:
      os.remove(self._profiling_sample_file)
    except OSError:
      pass

  def _ProfilingStop(self):
    """Stops the profiling."""
    self._ProfilingWriteSample()

  def _ProfilingUpdate(self):
    """Updates the profiling."""
    self._profiling_sample += 1

    if self._profiling_sample >= self._profiling_sample_rate:
      self._ProfilingWriteSample()
      self._profiling_sample = 0

  def _ProfilingWriteSample(self):
    """Writes a profiling sample to the sample file."""
    heap = self._heapy.heap()
    heap.dump(self._profiling_sample_file)

  def GetStatus(self):
    """Returns a status dictionary for the worker process."""
    return {
        'is_running': self._is_running,
        'identifier': u'Worker_{0:d}'.format(self._identifier),
        'current_file': self._current_working_file,
        'counter': self._parser_context.number_of_events}

  def InitalizeParserObjects(self, parser_filter_string=None):
    """Initializes the parser objects.

    The parser_filter_string is a simple comma separated value string that
    denotes a list of parser names to include and/or exclude. Each entry
    can have the value of:
      + Exact match of a list of parsers, or a preset (see
        plaso/frontend/presets.py for a full list of available presets).
      + A name of a single parser (case insensitive), eg. msiecfparser.
      + A glob name for a single parser, eg: '*msie*' (case insensitive).

    Args:
      parser_filter_string: Optional parser filter string. The default is None.
    """
    self._parser_objects = parsers_manager.ParsersManager.GetParserObjects(
        parser_filter_string=parser_filter_string)

    for parser_object in self._parser_objects:
      if parser_object.NAME == 'filestat':
        self._filestat_parser_object = parser_object
        break

  def _ParseFileEntryWithParser(self, parser_object, file_entry):
    """Parses a file entry with a specific parser.

    Args:
      parser_object: A parser object (instance of BaseParser).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    try:
      parser_object.Parse(self._parser_context, file_entry)

    except errors.UnableToParseFile as exception:
      logging.debug(u'Not a {0:s} file ({1:s}) - {2:s}'.format(
          parser_object.NAME, file_entry.name, exception))

    except IOError as exception:
      logging.debug(
          u'[{0:s}] Unable to parse: {1:s} with error: {2:s}'.format(
              parser_object.NAME, file_entry.path_spec.comparable,
              exception))

    # Casting a wide net, catching all exceptions. Done to keep the worker
    # running, despite the parser hitting errors, so the worker doesn't die
    # if a single file is corrupted or there is a bug in a parser.
    except Exception as exception:
      logging.warning(
          u'[{0:s}] Unable to process file: {1:s} with error: {2:s}.'.format(
              parser_object.NAME, file_entry.path_spec.comparable,
              exception))
      logging.debug(
          u'The path specification that caused the error: {0:s}'.format(
              file_entry.path_spec.comparable))
      logging.exception(exception)

      # Check for debug mode and single process mode, then we would like
      # to debug this problem.
      if self._single_process_mode and self._enable_debug_output:
        pdb.post_mortem()

  def ParseFileEntry(self, file_entry):
    """Parses a file entry.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    logging.debug(u'[ParseFileEntry] Parsing: {0:s}'.format(
        file_entry.path_spec.comparable))

    self._current_working_file = getattr(
        file_entry.path_spec, u'location', file_entry.name)

    if file_entry.IsDirectory() and self._filestat_parser_object:
      self._ParseFileEntryWithParser(self._filestat_parser_object, file_entry)

    elif file_entry.IsFile():
      # TODO: Not go through all parsers, just the ones
      # that the classifier classifies the file as.

      for parser_object in self._parser_objects:
        logging.debug(u'Trying to parse: {0:s} with parser: {1:s}'.format(
            file_entry.name, parser_object.NAME))

        self._ParseFileEntryWithParser(parser_object, file_entry)

    logging.debug(u'[ParseFileEntry] Done parsing: {0:s}'.format(
        file_entry.path_spec.comparable))

    if self._enable_profiling:
      self._ProfilingUpdate()

    if self._open_files:
      try:
        for sub_file_entry in classifier.Classifier.SmartOpenFiles(file_entry):
          self.ParseFileEntry(sub_file_entry)
      except IOError as exception:
        logging.warning(
            u'Unable to parse file: {0:s} with error: {1:s}'.format(
                file_entry.path_spec.comparable, exception))

  def Run(self, parser_filter_string=None):
    """Start the worker, monitor the queue and parse files.

    Args:
      parser_filter_string: Optional parser filter string. The default is None.
    """
    self.pid = os.getpid()
    logging.info(
        u'Worker {0:d} (PID: {1:d}) started monitoring process queue.'.format(
            self._identifier, self.pid))

    self.InitalizeParserObjects(parser_filter_string=parser_filter_string)

    self._parser_context.ResetCounters()

    if self._rpc_proxy:
      try:
        self._rpc_proxy.SetListeningPort(self.pid)
        self._rpc_proxy.Open()
        self._rpc_proxy.RegisterFunction('status', self.GetStatus)

        proxy_thread = threading.Thread(
            name='rpc_proxy', target=self._rpc_proxy.StartProxy)
        proxy_thread.start()
      except errors.ProxyFailedToStart as exception:
        logging.error(
            u'Unable to setup a RPC server for the worker: {0:d} [PID {1:d}] '
            u'with error: {2:s}'.format(self._identifier, self.pid, exception))

    if self._enable_profiling:
      self._ProfilingStart()

    self._is_running = True

    self.ConsumePathSpecs()

    logging.info(
        u'Worker {0:d} (PID: {1:d}) stopped monitoring process queue.'.format(
            self._identifier, os.getpid()))

    if self._enable_profiling:
      self._ProfilingStop()

    self._is_running = False
    self._current_working_file = u''

    self._resolver_context.Empty()

    if self._rpc_proxy:
      # Close the proxy, free up resources so we can shut down the thread.
      self._rpc_proxy.Close()

      if proxy_thread.isAlive():
        proxy_thread.join()

  def SetEnableDebugOutput(self, enable_debug_output):
    """Enables or disables debug output.

    Args:
      enable_debug_output: boolean value to indicate if the debug output
                           should be enabled.
    """
    self._enable_debug_output = enable_debug_output

  def SetEnableProfiling(self, enable_profiling, profiling_sample_rate=1000):
    """Enables or disables profiling.

    Args:
      enable_debug_output: boolean value to indicate if the profiling
                           should be enabled.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
    """
    if hpy:
      self._enable_profiling = enable_profiling
      self._profiling_sample_rate = profiling_sample_rate

    if self._enable_profiling and not self._heapy:
      self._heapy = hpy()

  def SetFilterObject(self, filter_object):
    """Sets the filter object.

    Args:
      filter_object: the filter object (instance of objectfilter.Filter).
    """
    self._parser_context.SetFilterObject(filter_object)

  def SetMountPath(self, mount_path):
    """Sets the mount path.

    Args:
      mount_path: string containing the mount path.
    """
    self._parser_context.SetMountPath(mount_path)

  # TODO: rename this mode.
  def SetOpenFiles(self, open_files):
    """Sets the open files mode.

    Args:
      file_files: boolean value to indicate if the worker should scan for
                  sun file entries inside files.
    """
    self._open_files = open_files

  def SetSingleProcessMode(self, single_process_mode):
    """Sets the single process mode.

    Args:
      single_process_mode: boolean value to indicate if the single process mode
                          should be enabled.
    """
    self._single_process_mode = single_process_mode

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: string that contains the text to prepend to every
                    event object.
    """
    self._parser_context.SetTextPrepend(text_prepend)

  @classmethod
  def SupportsProfiling(cls):
    """Returns a boolean value to indicate if profiling is supported."""
    return hpy is not None
