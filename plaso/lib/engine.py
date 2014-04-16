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
import multiprocessing
import os
import pdb
import signal
import sys
import traceback

import plaso
from plaso import preprocessors
from plaso import output as output_plugins   # pylint: disable=unused-import

from plaso.collector import collector
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import preprocess_interface
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import storage
from plaso.lib import timelib
from plaso.lib import worker

import pytz


class Engine(object):
  """Class that defines the processing engine."""

  # The minimum amount of worker processes that are started.
  MINIMUM_WORKERS = 3
  # The maximum amount of worker processes started.
  MAXIMUM_WORKERS = 15

  def __init__(self, config):
    """Initialize the Plaso engine.

    Initializes some variables used in the tool as well
    as going over the configuration and veryfing each one.

    Args:
      config: A configuration object, either an optparse or an argparse one.

    Raises:
      errors.BadConfigOption: If the configuration options are wrong.
    """
    self._byte_offset = None
    self._collector = None
    self._debug_mode = config.debug
    self._file_filter = config.file_filter
    self._output = None
    self._process_image = False
    self._process_vss = False
    self._run_preprocess = config.preprocess
    self._single_thread_mode = config.single_thread
    self._storage_queue_producer = None
    self._vss_stores = None

    self.worker_threads = []
    self.config = config

    config.zone = pytz.timezone(config.tzone)

    if config.workers < 1:
      # One worker for each "available" CPU (minus other processes).
      # The number three here is derived from the fact that the engine starts
      # up:
      #   + A collector process.
      #   + A storage process.
      # If we want to utilize all CPU's on the system we therefore need to start
      # up workers that amounts to the total number of CPU's - 3 (these two plus
      # the main process). Thus the number three.
      cpus = multiprocessing.cpu_count() - 3

      if cpus <= self.MINIMUM_WORKERS:
        cpus = self.MINIMUM_WORKERS
      elif cpus >= self.MAXIMUM_WORKERS:
        # Let's have a maximum amount of workers.
        cpus = self.MAXIMUM_WORKERS

      config.workers = cpus

  def _GetCollector(self, pre_obj, collection_queue, storage_queue):
    """Returns a collector object based on config."""
    # Indicate whether the collection agent should collect directory
    # stat information - this depends on whether the stat parser is
    # loaded or not.
    include_directory_stat = False
    if hasattr(pre_obj, 'collection_information'):
      loaded_parsers = pre_obj.collection_information.get('parsers', [])
      if 'PfileStatParser' in loaded_parsers:
        include_directory_stat = True

    if self._process_image:
      # Note that os.path.isfile() will return false when self._source
      # points to a device file.
      if os.path.isdir(self._source):
        raise errors.BadConfigOption(
            u'Source: {0:s} cannot be a directory.'.format(self._source))

      if self._file_filter:
        logging.debug(u'Starting a collection on image with filter.')
      else:
        logging.debug(u'Starting a collection on image.')

    else:
      if (not os.path.isfile(self._source) and
          not os.path.isdir(self._source)):
        raise errors.BadConfigOption(
            u'Source: {0:s} has to be a file or directory.'.format(
                self._source))

      if self._file_filter:
        logging.debug(u'Starting a collection on directory with filter.')
      elif self.config.recursive:
        logging.debug(u'Starting a collection on directory.')
      else:
        # No need for multiple workers when parsing a single file.
        self.config.workers = 1

    collector_object = collector.Collector(
        collection_queue, storage_queue, self._source,
        source_path_spec=self._source_path_spec)

    if self._process_image:
      collector_object.SetImageInformation(self._byte_offset)

      if self._process_vss:
        collector_object.SetVssInformation(vss_stores=self._vss_stores)

    if self._file_filter:
      collector_object.SetFilter(self._file_filter, pre_obj)

    collector_object.collect_directory_metadata = include_directory_stat

    return collector_object

  def _PreProcess(self, pre_obj):
    """Run the preprocessors."""
    logging.info(u'Starting to collect preprocessing information.')
    logging.info(u'Filename: {0:s}'.format(self._source))

    if not self._process_image and not self.config.recursive:
      return

    preprocess_collector = collector.GenericPreprocessCollector(
        pre_obj, self._source, source_path_spec=self._source_path_spec)

    if self._process_image:
      preprocess_collector.SetImageInformation(self._byte_offset)

    if not getattr(self.config, 'os', None):
      self.config.os = preprocess_interface.GuessOS(preprocess_collector)

    plugin_list = preprocessors.PreProcessList(pre_obj)
    pre_obj.guessed_os = self.config.os

    for weight in plugin_list.GetWeightList(self.config.os):
      for plugin in plugin_list.GetWeight(self.config.os, weight):
        try:
          plugin.Run(preprocess_collector)
        except (IOError, errors.PreProcessFail) as exception:
          logging.warning((
              u'Unable to run preprocessor: {} with error: {} - attribute [{}] '
              u'not set').format(
                  plugin.plugin_name, exception, plugin.ATTRIBUTE))

    # Set the timezone.
    if hasattr(pre_obj, 'time_zone_str'):
      logging.info(u'Setting timezone to: {0:s}'.format(pre_obj.time_zone_str))
      try:
        pre_obj.zone = pytz.timezone(pre_obj.time_zone_str)
      except pytz.UnknownTimeZoneError:
        if hasattr(self.config, 'zone'):
          logging.warning(
              (u'Unable to automatically configure timezone, falling back '
               'to the user supplied one [{0:s}]').format(
                  self.config.zone.zone))
          pre_obj.zone = self.config.zone
        else:
          logging.warning(u'TimeZone was not properly set, defaults to UTC')
    else:
      pre_obj.zone = self.config.zone

  def Start(self):
    """Start the process, set up all processing."""

    if self._single_thread_mode:
      logging.info(u'Starting the tool in a single thread.')
      try:
        self._StartSingleThread()
      except Exception as e:
        # The tool should generally not be run in single threaded mode
        # for other reasons than to debug. Hence the general error
        # catching.
        logging.error(u'An uncaught exception occured: {0:s}.\n{1:s}'.format(
            e, traceback.format_exc()))
        if self._debug_mode:
          pdb.post_mortem()
      return

    if self.config.local:
      logging.debug(u'Starting a local instance.')
      self._StartLocal()
      return

    logging.error(u'This version only supports local instance.')
    # TODO: Implement a more distributed version that is
    # scalable. That way each part of the tool can be run in a separate
    # machine.

  def _StartSingleThread(self):
    """Start everything up in a single thread.

    This should not normally be used, since running the tool in a single
    thread buffers up everything into memory until the storage is called.

    Just to make it clear, this starts up the collection, completes that
    before calling the worker that extracts all EventObjects and stores
    them in memory. when that is all done, the storage function is called
    to drain the buffer. Hence the tool's excessive use of memory in this
    mode and the reason why it is not suggested to be used except for
    debugging reasons (and mostly to get into the debugger).

    This is therefore mostly useful during debugging sessions for some
    limited parsing.
    """
    pre_obj = self._StartRuntime()
    collection_queue = queue.SingleThreadedQueue()
    storage_queue = queue.SingleThreadedQueue()

    logging.debug(u'Starting collection.')

    self._collector = self._GetCollector(
        pre_obj, collection_queue, storage_queue)
    self._collector.Collect()

    logging.debug(u'Collection done.')

    self.worker_threads = []

    logging.debug(u'Starting worker.')
    self._storage_queue_producer = queue.EventObjectQueueProducer(storage_queue)
    my_worker = worker.EventExtractionWorker(
        0, collection_queue, self._storage_queue_producer, self.config, pre_obj)
    my_worker.Run()

    logging.debug(u'Worker process done.')

    self._storage_queue_producer.SignalEndOfInput()

    logging.debug(u'Starting storage.')
    if self.config.output_module:
      storage_writer = storage.BypassStorageWriter(
          storage_queue, self._output,
          output_module_string=self.config.output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          storage_queue, self._output,
          buffer_size=self.config.buffer_size, pre_obj=pre_obj)

    storage_writer.WriteEventObjects()
    logging.debug(u'Storage done.')

  def _StartRuntime(self):
    """Run preprocessing and other actions needed before starting threads."""
    pre_obj = None
    if self.config.old_preprocess and os.path.isfile(self._output):
      # Check if the storage file contains a pre processing object.
      try:
        with storage.StorageFile(
            self._output, read_only=True) as store:
          storage_information = store.GetStorageInformation()
          if storage_information:
            logging.info(u'Using preprocessing information from a prior run.')
            pre_obj = storage_information[-1]
            self._run_preprocess = False
      except IOError:
        logging.warning(u'Storage file does not exist, running pre process.')

    if not pre_obj:
      pre_obj = event.PreprocessObject()

    # Run preprocessing if necessary.
    if self._run_preprocess:
      try:
        self._PreProcess(pre_obj)
      except errors.UnableToOpenFilesystem as e:
        logging.error(u'Unable to open the filesystem: {0:s}'.format(e))
        return
      except IOError as e:
        logging.error(u'Unable to preprocess, with error: {0:s}'.format(e))
        return

    if not getattr(pre_obj, 'zone', None):
      pre_obj.zone = self.config.zone

    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.
    if not getattr(self.config, 'filter', None):
      self.config.filter = u''

    if not self.config.filter:
      self.config.filter = u''

    parser_filter_string = u''

    # If no parser filter is set, let's use our best guess of the OS
    # to build that list.
    if not getattr(self.config, 'parsers', ''):
      if hasattr(pre_obj, 'osversion'):
        os_version = pre_obj.osversion.lower()
        # TODO: Improve this detection, this should be more 'intelligent', since
        # there are quite a lot of versions out there that would benefit from
        # loading up the set of 'winxp' parsers.
        if 'windows xp' in os_version:
          parser_filter_string = 'winxp'
        elif 'windows server 2000' in os_version:
          parser_filter_string = 'winxp'
        elif 'windows server 2003' in os_version:
          parser_filter_string = 'winxp'
        else:
          parser_filter_string = 'win7'

      if getattr(pre_obj, 'guessed_os', None):
        if pre_obj.guessed_os == 'MacOSX':
          parser_filter_string = u'macosx'
        elif pre_obj.guessed_os == 'Linux':
          parser_filter_string = 'linux'

      if parser_filter_string:
        self.config.parsers = parser_filter_string
        logging.info(u'Parser filter expression changed to: {}'.format(
            self.config.parsers))

    # Save some information about the run time into the preprocessing object.
    self._StoreCollectionInformation(pre_obj)

    return pre_obj

  def _StartLocal(self):
    """Start the process, set up all threads and start them up.

    The local implementation uses the muliprocessing library to
    start up new threads or processes.

    Raises:
      errors.BadConfigOption: If the file being parsed does not exist.
    """
    pre_obj = self._StartRuntime()
    collection_queue = queue.MultiThreadedQueue()
    storage_queue = queue.MultiThreadedQueue()

    start_collection_thread = True

    if self.config.output_module:
      storage_writer = storage.BypassStorageWriter(
          storage_queue, self._output, self.config.output_module, pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          storage_queue, self._output, self.config.buffer_size, pre_obj)

    self._collector = self._GetCollector(
        pre_obj, collection_queue, storage_queue)

    logging.info(u'Starting storage thread.')
    self.storage_thread = multiprocessing.Process(
        name='StorageThread', target=storage_writer.WriteEventObjects)
    self.storage_thread.start()

    if start_collection_thread:
      logging.info(u'Starting collection thread.')
      self.collection_thread = multiprocessing.Process(
          name='Collection', target=self._collector.Collect)
      self.collection_thread.start()

    logging.info(u'Starting workers to extract events.')
    self._storage_queue_producer = queue.EventObjectQueueProducer(storage_queue)
    for worker_nr in range(self.config.workers):
      logging.debug(u'Starting worker: {0:d}'.format(worker_nr))
      my_worker = worker.EventExtractionWorker(
          worker_nr, collection_queue, self._storage_queue_producer,
          self.config, pre_obj)
      self.worker_threads.append(multiprocessing.Process(
          name='Worker_{0:d}'.format(worker_nr),
          target=my_worker.Run))
      self.worker_threads[-1].start()

    logging.info(u'Collecting and processing files.')
    if start_collection_thread:
      self.collection_thread.join()
    else:
      self._collector.Collect()

    logging.info(u'Collection is done, waiting for processing to complete.')
    # TODO: Test to see if a process pool can be a better choice.
    for thread_nr, thread in enumerate(self.worker_threads):
      if thread.is_alive():
        thread.join()

      # Note that we explicitly must test against exitcode 0 here since
      # thread.exitcode will be None if there is no exitcode.
      elif thread.exitcode != 0:
        logging.warning((
            u'Worker process: {0:d} already exited with code: {1:d}.').format(
                thread_nr, thread.exitcode))
        thread.terminate()

    logging.info(u'Processing is done, waiting for storage to complete.')

    self._storage_queue_producer.SignalEndOfInput()
    self.storage_thread.join()
    logging.info(u'Storage is done.')

  def _StoreCollectionInformation(self, obj):
    """Store information about collection into an object."""
    obj.collection_information = {}

    obj.collection_information['version'] = plaso.GetVersion()
    obj.collection_information['configured_zone'] = self.config.zone
    obj.collection_information['file_processed'] = self._source
    obj.collection_information['output_file'] = self._output
    obj.collection_information['protobuf_size'] = self.config.buffer_size
    obj.collection_information['parser_selection'] = getattr(
        self.config, 'parsers', '(no list set)')
    obj.collection_information['preferred_encoding'] = getattr(
        self.config, 'preferred_encoding', None)
    obj.collection_information['time_of_run'] = timelib.Timestamp.GetNow()
    filter_query = getattr(self.config, 'parsers', None)
    obj.collection_information['parsers'] = [
        x.parser_name for x in putils.FindAllParsers(
            obj, self.config, filter_query)['all']]

    obj.collection_information['preprocess'] = self._run_preprocess
    obj.collection_information['recursive'] = bool(
        self.config.recursive)
    obj.collection_information['debug'] = bool(self._debug_mode)
    obj.collection_information['vss parsing'] = self._process_vss

    if getattr(self.config, 'filter', None):
      obj.collection_information['filter'] = self.config.filter

    if getattr(self.config, 'file_filter', None):
      if os.path.isfile(self._file_filter):
        filters = []
        with open(self._file_filter, 'rb') as fh:
          for line in fh:
            filters.append(line.rstrip())
        obj.collection_information['file_filter'] = ', '.join(filters)

    obj.collection_information['os_detected'] = getattr(
        self.config, 'os', 'N/A')

    if self._process_image:
      obj.collection_information['method'] = 'imaged processed'
      obj.collection_information['image_offset'] = self._byte_offset
    else:
      obj.collection_information['method'] = 'OS collection'

    if self._single_thread_mode:
      obj.collection_information['runtime'] = 'single threaded'
    else:
      obj.collection_information['runtime'] = 'multi threaded'
      obj.collection_information['workers'] = self.config.workers

  def SetImageInformation(self, byte_offset):
    """Sets the values necessary for collection from an image.

       This function will enable image collection.

    Args:
      byte_offset: Optional byte offset into the image file if this is
                   a disk image. The default is None.

    Raises:
      BadConfigOption: if the byte offset is not defined and cannot be
                       determined from the sector offset and bytes per sector.
    """
    if byte_offset is not None:
      self._byte_offset = byte_offset
    else:
      # If no offset was provided default to 0.
      self._byte_offset = 0

    self._process_image = True
    # If we're dealing with a storage media image always run pre-processing.
    self._run_preprocess = True

  def SetOutput(self, output):
    """Checks if the output file is valid and sets it accordingly.

    Args:
      output: The output file.

    Raises:
      BadConfigOption: if the output is invalid.
    """
    if os.path.exists(output):
      if not os.path.isfile(output):
        raise errors.BadConfigOption(
            u'Output: {0:s} exists but is not a file.'.format(output))
      logging.warning(u'Appending to an already existing output file.')

    dirname = os.path.dirname(output)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the output really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          u'Unable to write to output file: {0:s}'.format(output))

    self._output = output

  def SetSource(self, source, source_path_spec=None):
    """Checks if the source valid and sets it accordingly.

    Args:
      source: The source device, file or directory.
      source_path_spec: Optional source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.

    Raises:
      BadConfigOption: if the source is invalid.
    """
    if not os.path.exists(source):
      raise errors.BadConfigOption(
          u'No such device, file or directory: {0:s}.'.format(source))

    self._source = unicode(source)
    self._source_path_spec = source_path_spec

  def SetVssInformation(self, vss_stores):
    """Sets the Volume Shadow Snapshots (VSS) information.

       This function will enable VSS collection.

    Args:
      vss_stores: List of VSS store index numbers to process.
                  Where 1 represents the first store.
    """
    self._process_vss = True
    self._vss_stores = vss_stores

  # Note that this function is not called by the normal termination.
  def StopThreads(self):
    """Signals the tool to stop running nicely."""
    if self._single_thread_mode and self._debug_mode:
      logging.warning(u'Running in debug mode, set up debugger.')
      pdb.post_mortem()
      return

    logging.warning(u'Stopping collector.')
    self._collector.SignalEndOfInput()

    logging.warning(u'Stopping storage.')
    self._storage_queue_producer.SignalEndOfInput()

    # Kill the collection thread.
    if hasattr(self, 'collection_thread'):
      logging.warning(u'Terminating the collection thread.')
      self.collection_thread.terminate()

    try:
      logging.warning(u'Waiting for workers to complete.')
      for number, worker_thread in enumerate(self.worker_threads):
        pid = worker_thread.pid
        logging.warning(u'Waiting for worker: {0:d} [PID {1:d}]'.format(
            number, pid))
        # Let's kill the process, different methods depending on the platform
        # used.
        if sys.platform.startswith('win'):
          import ctypes
          process_terminate = 1
          handle = ctypes.windll.kernel32.OpenProcess(
              process_terminate, False, pid)
          ctypes.windll.kernel32.TerminateProcess(handle, -1)
          ctypes.windll.kernel32.CloseHandle(handle)
        else:
          try:
            os.kill(pid, signal.SIGKILL)
          except OSError as exception:
            logging.error(u'Unable to kill process {}: {}'.format(
                pid, exception))

        logging.warning(u'Worker: {0:d} CLOSED'.format(pid))

      logging.warning(u'Workers completed.')
      if hasattr(self, 'storage_thread'):
        logging.warning(u'Waiting for storage.')
        self.storage_thread.join()
        logging.warning(u'Storage ended.')

      logging.info(u'Exiting the tool.')
      # Sometimes the main thread will be unresponsive.
      if not sys.platform.startswith('win'):
        os.kill(os.getpid(), signal.SIGKILL)

    except KeyboardInterrupt:
      logging.warning(u'Terminating all processes.')
      for t in self.worker_threads:
        t.terminate()
      logging.warning(u'Workers terminated.')
      if hasattr(self, 'storage_thread'):
        self.storage_thread.terminate()
        logging.warning(u'Storage terminated.')

      # Sometimes the main thread will be unresponsive.
      if not sys.platform.startswith('win'):
        os.kill(os.getpid(), signal.SIGKILL)
