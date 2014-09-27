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
"""The processing engine."""

import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import resolver as path_spec_resolver

from plaso import preprocessors
from plaso.artifacts import knowledge_base
from plaso.engine import collector
from plaso.engine import worker
from plaso.lib import errors
from plaso.lib import queue
from plaso.preprocessors import interface as preprocess_interface


class Engine(object):
  """Class that defines the processing engine."""

  def __init__(self, collection_queue, storage_queue, parse_error_queue):
    """Initialize the engine object.

    Args:
      collection_queue: the collection queue object (instance of Queue).
      storage_queue: the storage queue object (instance of Queue).
      parse_error_queue: the parser error queue object (instance of Queue).
    """
    self._collection_queue = collection_queue
    self._source = None
    self._source_path_spec = None
    self._source_file_entry = None
    self._event_queue_producer = queue.EventObjectQueueProducer(storage_queue)
    self._parse_error_queue_producer = queue.ParseErrorQueueProducer(
        parse_error_queue)
    self.knowledge_base = knowledge_base.KnowledgeBase()

  def CreateCollector(
      self, include_directory_stat, vss_stores=None, filter_find_specs=None,
      resolver_context=None):
    """Creates a collector.

    Args:
      include_directory_stat: Boolean value to indicate whether directory
                              stat information should be collected.
      vss_stores: Optional list of VSS stores to include in the collection,
                  where 1 represents the first store. Set to None if no
                  VSS stores should be processed. The default is None.
      filter_find_specs: Optional list of filter find specifications (instances
                         of dfvfs.FindSpec). The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_path_spec:
      raise RuntimeError(u'Missing source.')

    collector_object = collector.Collector(
        self._collection_queue, self._event_queue_producer, self._source,
        self._source_path_spec, resolver_context=resolver_context)

    collector_object.collect_directory_metadata = include_directory_stat

    if vss_stores:
      collector_object.SetVssInformation(vss_stores)

    if filter_find_specs:
      collector_object.SetFilter(filter_find_specs)

    return collector_object

  def CreateExtractionWorker(self, worker_number, rpc_proxy=None):
    """Creates an extraction worker object.

    Args:
      worker_number: A number that identifies the worker.
      rpc_proxy: A proxy object (instance of proxy.ProxyServer) that can be
                 used to setup RPC functionality for the worker. This is
                 optional and if not provided the worker will not listen to RPC
                 requests.

    Returns:
      An extraction worker (instance of worker.ExtractionWorker).
    """
    return worker.EventExtractionWorker(
        worker_number, self._collection_queue, self._event_queue_producer,
        self._parse_error_queue_producer, self.knowledge_base,
        rpc_proxy=rpc_proxy)

  def GetSourceFileSystemSearcher(self, resolver_context=None):
    """Retrieves the file system searcher of the source.

    Args:
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      The file system searcher object (instance of dfvfs.FileSystemSearcher).

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_path_spec:
      raise RuntimeError(u'Missing source.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        self._source_path_spec, resolver_context=resolver_context)

    type_indicator = self._source_path_spec.type_indicator
    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
      mount_point = self._source_path_spec
    else:
      mount_point = self._source_path_spec.parent

    return file_system_searcher.FileSystemSearcher(file_system, mount_point)

  def PreprocessSource(self, platform, resolver_context=None):
    """Preprocesses the source and fills the preprocessing object.

    Args:
      platform: string that indicates the platform (operating system).
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.
    """
    searcher = self.GetSourceFileSystemSearcher(
        resolver_context=resolver_context)
    if not platform:
      platform = preprocess_interface.GuessOS(searcher)
    self.knowledge_base.platform = platform

    for weight in preprocessors.PreProcessorsManager.GetWeightList(platform):
      for plugin in preprocessors.PreProcessorsManager.GetWeight(
          platform, weight):
        try:
          plugin.Run(searcher, self.knowledge_base)
        except (IOError, errors.PreProcessFail) as exception:
          logging.warning((
              u'Unable to run preprocessor: {0:s} for attribute: {1:s} '
              u'with error: {2:s}').format(
                  plugin.plugin_name, plugin.ATTRIBUTE, exception))

  def SetSource(self, source_path_spec, resolver_context=None):
    """Sets the source.

    Args:
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Raises:
      BadConfigOption: if source cannot be set.
    """
    path_spec = source_path_spec
    while path_spec.parent:
      path_spec = path_spec.parent

    # Note that source should be used for output purposes only.
    self._source = getattr(path_spec, 'location', u'')
    self._source_path_spec = source_path_spec

    self._source_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
       self._source_path_spec, resolver_context=resolver_context)

    if not self._source_file_entry:
      raise errors.BadConfigOption(
          u'No such device, file or directory: {0:s}.'.format(self._source))

    if (not self._source_file_entry.IsDirectory() and
        not self._source_file_entry.IsFile() and
        not self._source_file_entry.IsDevice()):
      raise errors.CollectorError(
          u'Source path: {0:s} not a device, file or directory.'.format(
              self._source))

    if self._source_path_spec.type_indicator in [
        dfvfs_definitions.TYPE_INDICATOR_OS,
        dfvfs_definitions.TYPE_INDICATOR_FAKE]:

      if self._source_file_entry.IsFile():
        logging.debug(u'Starting a collection on a single file.')
        # No need for multiple workers when parsing a single file.

      elif not self._source_file_entry.IsDirectory():
        raise errors.BadConfigOption(
            u'Source: {0:s} has to be a file or directory.'.format(
                self._source))

  def SignalEndOfInputStorageQueue(self):
    """Signals the storage queue no input remains."""
    self._event_queue_producer.SignalEndOfInput()

  def SourceIsDirectory(self):
    """Determines if the source is a directory.

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_file_entry:
      raise RuntimeError(u'Missing source.')

    return (not self.SourceIsStorageMediaImage() and
            self._source_file_entry.IsDirectory())

  def SourceIsFile(self):
    """Determines if the source is a file.

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_file_entry:
      raise RuntimeError(u'Missing source.')

    return (not self.SourceIsStorageMediaImage() and
            self._source_file_entry.IsFile())

  def SourceIsStorageMediaImage(self):
    """Determines if the source is storage media image file or device.

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_path_spec:
      raise RuntimeError(u'Missing source.')

    return self._source_path_spec.type_indicator not in [
        dfvfs_definitions.TYPE_INDICATOR_OS,
        dfvfs_definitions.TYPE_INDICATOR_FAKE]
