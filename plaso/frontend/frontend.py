#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""The common front-end functionality."""

import logging
import multiprocessing
import os
import pdb
import signal
import sys
import traceback

from dfvfs.resolver import context

import plaso
from plaso import parsers   # pylint: disable=unused-import
from plaso.collector import scanner
from plaso.collector import utils as engine_utils
from plaso.lib import engine
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import putils
from plaso.lib import queue
from plaso.lib import storage
from plaso.lib import timelib

import pytz


class Frontend(object):
  """Class that implements a front-end."""

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of EngineInputReader).
                    The default is None which indicates to use the stdin
                    input reader.
      output_writer: the output writer (instance of EngineOutputWriter).
                     The default is None which indicates to use the stdout
                     output writer.
    """
    super(Frontend, self).__init__()
    self._input_reader = input_reader
    self._output_writer = output_writer

  def AddImageOptions(self, argument_group):
    """Adds the storage media image options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '-o', '--offset', dest='image_offset', action='store', default=None,
        type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of sectors. A sector is 512 bytes in size by default '
            u'this can be overwritten with the --sector_size option.'))

    argument_group.add_argument(
        '--sector_size', '--sector-size', dest='bytes_per_sector',
        action='store', type=int, default=512, help=(
            u'The number of bytes per sector, which is 512 by default.'))

    argument_group.add_argument(
        '--ob', '--offset_bytes', '--offset_bytes', dest='image_offset_bytes',
        action='store', default=None, type=int, help=(
            u'The offset of the volume within the storage media image in '
            u'number of bytes.'))

  def AddVssProcessingOptions(self, argument_group):
    """Adds the VSS processing options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '--vss_stores', '--vss-stores', dest='vss_stores', action='store',
        type=str, default=None, help=(
            u'Define Volume Shadow Snapshots (VSS) (or stores that need to be '
            u'processed. A range of stores can be defined as: \'3..5\'. '
            u'Multiple stores can be defined as: \'1,3,5\' (a list of comma '
            u'separated values). Ranges and lists can also be combined as: '
            u'\'1,3..5\'. The first store is 1.'))

  def PrintOptions(self, options, source_path):
    """Prints the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_path: the source path.
    """
    self._output_writer.Write(u'\n')
    self._output_writer.Write(
        u'Source path\t\t: {0:s}\n'.format(source_path))
    self._output_writer.Write(
        u'Is storage media image\t: {0!s}\n'.format(options.image))

    if options.image:
      self._output_writer.Write(
          u'Partition offset\t: 0x{0:08x}\n'.format(options.image_offset_bytes))

      if options.vss_stores:
        self._output_writer.Write(
            u'VSS stores\t\t: {0!s}\n'.format(options.vss_stores))

    if options.file_filter:
      self._output_writer.Write(
          u'Filter file\t\t: {0:s}\n'.format(options.file_filter))

    self._output_writer.Write(u'\n')

  def ScanSource(self, options, source_path):
    """Scans the source path for volume and file systems.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_path: the source path.

    Returns:
      The base path specification (instance of dfvfs.PathSpec).
    """
    if not source_path:
      return

    file_system_scanner = scanner.FileSystemScanner(
        self._input_reader, self._output_writer)

    if hasattr(options, 'image_offset_bytes'):
      file_system_scanner.SetPartitionOffset(options.image_offset_bytes)
    elif hasattr(options, 'image_offset'):
      bytes_per_sector = getattr(options, 'bytes_per_sector', 512)
      file_system_scanner.SetPartitionOffset(
          options.image_offset * bytes_per_sector)

    if getattr(options, 'partition_number', None) is not None:
      file_system_scanner.SetPartitionNumber(options.partition_number)

    if hasattr(options, 'vss_stores'):
      file_system_scanner.SetVssStores(options.vss_stores)

    path_spec = file_system_scanner.Scan(source_path)

    options.image = file_system_scanner.is_storage_media_image
    options.image_offset_bytes = file_system_scanner.partition_offset
    options.vss_stores = file_system_scanner.vss_stores

    return path_spec


class ExtractionFrontend(Frontend):
  """Class that implements an extraction front-end."""

  # The minimum number of processes.
  MINIMUM_WORKERS = 3
  # The maximum number of processes.
  MAXIMUM_WORKERS = 15

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of EngineInputReader).
                    The default is None which indicates to use the stdin
                    input reader.
      output_writer: the output writer (instance of EngineOutputWriter).
                     The default is None which indicates to use the stdout
                     output writer.
    """
    super(ExtractionFrontend, self).__init__(input_reader, output_writer)
    self._collection_thread = None
    self._collector = None
    self._debug_mode = False
    self._engine = None
    self._parsers = None
    self._resolver_context = context.Context()
    self._single_process_mode = False
    self._source_path = None
    self._source_path_spec = None
    self._storage_file_path = None
    self._storage_thread = None

    # TODO: turn into a thread pool.
    self._worker_threads = []

  def _CheckStorageFile(self, storage_file_path):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path: The path of the storage file.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            u'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))
      logging.warning(u'Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          u'Unable to write to storage file: {0:s}'.format(storage_file_path))

  def _CreateExtractionWorker(self, worker_number, options, pre_obj):
    """Creates an extraction worker object.

    Args:
      worker_number: number that identifies the worker.
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: The preprocessing object (instance of PreprocessObject).

    Returns:
      An extraction worker (instance of worker.ExtractionWorker).
    """
    extraction_worker = self._engine.CreateExtractionWorker(
        worker_number, pre_obj, self._parsers)

    extraction_worker.SetDebugMode(self._debug_mode)
    extraction_worker.SetSingleProcessMode(self._single_process_mode)

    open_files = getattr(options, 'open_files', None)
    extraction_worker.SetOpenFiles(open_files)

    if getattr(options, 'os', None):
      mount_path = getattr(options, 'filename', None)
      extraction_worker.SetMountPath(mount_path)

    filter_query = getattr(options, 'filter', None)
    if filter_query:
      filter_object = pfilter.GetMatcher(filter_query)
      extraction_worker.SetFilterObject(filter_object)

    text_prepend = getattr(options, 'text_prepend', None)
    extraction_worker.SetTextPrepend(text_prepend)

    return extraction_worker

  def _DebugPrintCollector(self, options):
    """Prints debug information about the collector.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    if self._engine.SourceIsStorageMediaImage():
      if options.file_filter:
        logging.debug(u'Starting a collection on image with filter.')
      else:
        logging.debug(u'Starting a collection on image.')

    elif self._engine.SourceIsDirectory():
      if options.file_filter:
        logging.debug(u'Starting a collection on directory with filter.')
      elif options.recursive:
        logging.debug(u'Starting a collection on directory.')

    elif self._engine.SourceIsFile():
      logging.debug(u'Starting a collection on a single file.')

    else:
      logging.warning(u'Unknown collection mode.')

  # TODO: have the frontend fill collecton information gradually
  # and set it as the last step of preprocessing?
  def _PreprocessSetCollectionInformation(self, options, pre_obj):
    """Sets the collection information as part of the preprocessing.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: the preprocess object (instance of PreprocessObject).
    """
    collection_information = {}

    collection_information['version'] = plaso.GetVersion()
    collection_information['configured_zone'] = options.zone
    collection_information['file_processed'] = self._source_path
    collection_information['output_file'] = options.output
    collection_information['protobuf_size'] = options.buffer_size
    collection_information['parser_selection'] = getattr(
        options, 'parsers', '(no list set)')
    collection_information['preferred_encoding'] = getattr(
        options, 'preferred_encoding', None)
    collection_information['time_of_run'] = timelib.Timestamp.GetNow()

    collection_information['parsers'] = self._parser_names
    collection_information['preprocess'] = options.preprocess
    collection_information['recursive'] = bool(options.recursive)
    collection_information['debug'] = bool(options.debug)
    collection_information['vss parsing'] = bool(options.vss_stores)

    if getattr(options, 'filter', None):
      collection_information['filter'] = options.filter

    if getattr(options, 'file_filter', None):
      if os.path.isfile(options.file_filter):
        filters = []
        with open(options.file_filter, 'rb') as fh:
          for line in fh:
            filters.append(line.rstrip())
        collection_information['file_filter'] = ', '.join(filters)

    collection_information['os_detected'] = getattr(options, 'os', 'N/A')

    if options.process_image:
      collection_information['method'] = 'imaged processed'
      collection_information['image_offset'] = options.image_offset_bytes
    else:
      collection_information['method'] = 'OS collection'

    if self._single_process_mode:
      collection_information['runtime'] = 'single threaded'
    else:
      collection_information['runtime'] = 'multi threaded'
      collection_information['workers'] = options.workers

    pre_obj.collection_information = collection_information

  def _PreprocessSetParserFilter(self, options, pre_obj):
    """Sets the parser filter as part of the preprocessing.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: The previously created preprocessing object (instance of
               PreprocessObject) or None.
    """
    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.

    if not getattr(options, 'filter', None):
      options.filter = u''

    # TODO: why this check?
    if not options.filter:
      options.filter = u''

    parser_filter_string = u''

    # If no parser filter is set, let's use our best guess of the OS
    # to build that list.
    if not getattr(options, 'parsers', ''):
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
        options.parsers = parser_filter_string
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            options.parsers))

  def _PreprocessSetTimezone(self, options, pre_obj):
    """Sets the timezone as part of the preprocessing.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      pre_obj: The previously created preprocessing object (instance of
               PreprocessObject) or None.
    """
    if hasattr(pre_obj, 'time_zone_str'):
      logging.info(u'Setting timezone to: {0:s}'.format(pre_obj.time_zone_str))
      try:
        pre_obj.zone = pytz.timezone(pre_obj.time_zone_str)
      except pytz.UnknownTimeZoneError:
        if hasattr(options, 'zone'):
          logging.warning((
              u'Unable to automatically configure timezone, falling back '
              u'to the user supplied one: {0:s}').format(options.zone))
          pre_obj.zone = options.zone
        else:
          logging.warning(u'TimeZone was not properly set, defaulting to UTC')
          pre_obj.zone = pytz.utc
    else:
      # TODO: shouldn't the user to be able to always override the timezone
      # detection? Or do we need an input sanitation function.
      pre_obj.zone = options.zone

    if not getattr(pre_obj, 'zone', None):
      pre_obj.zone = options.zone

  def _ProcessSourceMultiProcessMode(self, options):
    """Processes the source in a multiple process.

    Muliprocessing is used to start up separate processes.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    # TODO: replace by an option.
    start_collection_thread = True

    if options.workers < 1:
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

      options.workers = cpus

    logging.info(u'Starting extraction in multi process mode.')

    collection_queue = queue.MultiThreadedQueue()
    storage_queue = queue.MultiThreadedQueue()
    self._engine = engine.Engine(
        collection_queue, storage_queue,
        resolver_context=self._resolver_context)

    self._engine.SetSource(self._source_path_spec)

    logging.debug(u'Starting preprocessing.')
    pre_obj = self.PreprocessSource(options)

    # TODO: move FindAllParsers to engine as a class method?
    filter_query = getattr(options, 'parsers', '')
    self._parsers = putils.FindAllParsers(
        pre_obj=pre_obj, config=options, parser_filter_string=filter_query)
    self._parser_names = [parser.parser_name for parser in self._parsers['all']]

    self._PreprocessSetCollectionInformation(options, pre_obj)

    if options.output_module:
      storage_writer = storage.BypassStorageWriter(
          storage_queue, self._storage_file_path, options.output_module,
          pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          storage_queue, self._storage_file_path, options.buffer_size, pre_obj)

    logging.debug(u'Preprocessing done.')

    if 'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    file_filter = getattr(options, 'file_filter', None)
    if file_filter:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(file_filter)
    else:
      filter_find_specs = None

    self._collector = self._engine.CreateCollector(
        include_directory_stat, options.vss_stores, filter_find_specs)

    self._DebugPrintCollector(options)

    logging.info(u'Starting storage thread.')
    self._storage_thread = multiprocessing.Process(
        name='StorageThread', target=storage_writer.WriteEventObjects)
    self._storage_thread.start()

    if start_collection_thread:
      logging.info(u'Starting collection thread.')
      self._collection_thread = multiprocessing.Process(
          name='Collection', target=self._collector.Collect)
      self._collection_thread.start()

    logging.info(u'Starting workers to extract events.')
    for worker_nr in range(options.workers):
      extraction_worker = self._CreateExtractionWorker(
          worker_nr, options, pre_obj)

      logging.debug(u'Starting worker: {0:d}'.format(worker_nr))
      self._worker_threads.append(multiprocessing.Process(
          name='Worker_{0:d}'.format(worker_nr), target=extraction_worker.Run))

      self._worker_threads[-1].start()

    logging.info(u'Collecting and processing files.')
    if self._collection_thread:
      self._collection_thread.join()
    else:
      self._collector.Collect()

    logging.info(u'Collection is done, waiting for processing to complete.')
    # TODO: Test to see if a process pool can be a better choice.
    for thread_nr, thread in enumerate(self._worker_threads):
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

    self._engine.SignalEndOfInputStorageQueue()
    self._storage_thread.join()
    logging.info(u'Storage is done.')

  def _ProcessSourceSingleProcessMode(self, options):
    """Processes the source in a single process.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    logging.info(u'Starting extraction in single process mode.')

    try:
      self._StartSingleThread(options)
    except Exception as exception:
      # The tool should generally not be run in single threaded mode
      # for other reasons than to debug. Hence the general error
      # catching.
      logging.error(u'An uncaught exception occured: {0:s}.\n{1:s}'.format(
          exception, traceback.format_exc()))
      if self._debug_mode:
        pdb.post_mortem()

  def _StartSingleThread(self, options):
    """Starts everything up in a single thread.

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

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    collection_queue = queue.SingleThreadedQueue()
    storage_queue = queue.SingleThreadedQueue()
    self._engine = engine.Engine(
        collection_queue, storage_queue,
        resolver_context=self._resolver_context)

    self._engine.SetSource(self._source_path_spec)

    logging.debug(u'Starting preprocessing.')
    pre_obj = self.PreprocessSource(options)

    # TODO: move FindAllParsers to engine as a class method?
    filter_query = getattr(options, 'parsers', '')
    self._parsers = putils.FindAllParsers(
        pre_obj=pre_obj, config=options, parser_filter_string=filter_query)
    self._parser_names = [parser.parser_name for parser in self._parsers['all']]

    self._PreprocessSetCollectionInformation(options, pre_obj)

    logging.debug(u'Preprocessing done.')

    if 'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    file_filter = getattr(options, 'file_filter', None)
    if file_filter:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(file_filter)
    else:
      filter_find_specs = None

    self._collector = self._engine.CreateCollector(
        include_directory_stat, options.vss_stores, filter_find_specs)

    self._DebugPrintCollector(options)

    logging.debug(u'Starting collection.')
    self._collector.Collect()
    logging.debug(u'Collection done.')

    extraction_worker = self._CreateExtractionWorker(0, options, pre_obj)

    logging.debug(u'Starting extraction worker.')
    extraction_worker.Run()
    logging.debug(u'Extraction worker done.')

    self._engine.SignalEndOfInputStorageQueue()

    if options.output_module:
      storage_writer = storage.BypassStorageWriter(
          storage_queue, self._storage_file_path,
          output_module_string=options.output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          storage_queue, self._storage_file_path,
          buffer_size=options.buffer_size, pre_obj=pre_obj)

    logging.debug(u'Starting storage.')
    storage_writer.WriteEventObjects()
    logging.debug(u'Storage done.')

    self._resolver_context.Empty()

  # Note that this function is not called by the normal termination.
  def CleanUpAfterAbort(self):
    """Signals the tool to stop running nicely after an abort."""
    if self._single_process_mode and self._debug_mode:
      logging.warning(u'Running in debug mode, set up debugger.')
      pdb.post_mortem()
      return

    logging.warning(u'Stopping collector.')
    self._collector.SignalEndOfInput()

    logging.warning(u'Stopping storage.')
    self._engine.SignalEndOfInputStorageQueue()

    # Kill the collection thread.
    if self._collection_thread:
      logging.warning(u'Terminating the collection thread.')
      self._collection_thread.terminate()

    try:
      logging.warning(u'Waiting for workers to complete.')
      for number, worker_thread in enumerate(self._worker_threads):
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
            logging.error(
                u'Unable to kill process {0:d} with error: {1:s}'.format(
                    pid, exception))

        logging.warning(u'Worker: {0:d} CLOSED'.format(pid))

      logging.warning(u'Workers completed.')
      if hasattr(self, 'storage_thread'):
        logging.warning(u'Waiting for storage.')
        self._storage_thread.join()
        logging.warning(u'Storage ended.')

      logging.info(u'Exiting the tool.')
      # Sometimes the main thread will be unresponsive.
      if not sys.platform.startswith('win'):
        os.kill(os.getpid(), signal.SIGKILL)

    except KeyboardInterrupt:
      logging.warning(u'Terminating all processes.')
      for t in self._worker_threads:
        t.terminate()
      logging.warning(u'Workers terminated.')
      if hasattr(self, 'storage_thread'):
        self._storage_thread.terminate()
        logging.warning(u'Storage terminated.')

      # Sometimes the main thread will be unresponsive.
      if not sys.platform.startswith('win'):
        os.kill(os.getpid(), signal.SIGKILL)

  def GetSourceFileSystemSearcher(self):
    """Retrieves the file system searcher of the source.

    Returns:
      The file system searcher object (instance of dfvfs.FileSystemSearcher).
    """
    return self._engine.GetSourceFileSystemSearcher()

  def ParseOptions(self, options, source_option):
    """Parses the options and initializes the processing engine.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: the name of the source option.

    Raises:
      BadConfigOption: if the option are invalid.
    """
    if not options:
      raise errors.BadConfigOption(u'Missing options.')

    if options.buffer_size:
      # TODO: turn this into a generic function that supports
      # more size suffixes both MB and MiB and also that does not
      # allow m as a valid indicator for MiB since m represents
      # milli not Mega.
      try:
        if options.buffer_size[-1].lower() == 'm':
          options.buffer_size = int(options.buffer_size[:-1], 10)
          options.buffer_size *= self._BYTES_IN_A_MIB
        else:
          options.buffer_size = int(options.buffer_size, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid buffer size: {0:s}.'.format(options.buffer_size))

    if options.file_filter and not os.path.isfile(options.file_filter):
      raise errors.BadConfigOption(
          u'No such collection filter file: {0:s}.'.format(options.file_filter))

    self._source_path = getattr(options, source_option, None)
    if not self._source_path:
      raise errors.BadConfigOption(u'Missing source path.')

    try:
      self._source_path = unicode(self._source_path)
    except UnicodeDecodeError as exception:
      raise errors.BadConfigOption(
          u'Unable to convert source path to Unicode with error: {0:s}.'.format(
              exception))

    self._debug_mode = options.debug
    options.zone = pytz.timezone(options.tzone)

    if options.single_thread:
      self._single_process_mode = True
    else:
      self._single_process_mode = False

  def PreprocessSource(self, options):
    """Preprocesses the source.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Returns:
      The preprocessing object (instance of PreprocessObject).
    """
    pre_obj = None

    if options.old_preprocess and os.path.isfile(self._storage_file_path):
      # Check if the storage file contains a preprocessing object.
      try:
        with storage.StorageFile(
            self._storage_file_path, read_only=True) as store:
          storage_information = store.GetStorageInformation()
          if storage_information:
            logging.info(u'Using preprocessing information from a prior run.')
            pre_obj = storage_information[-1]
            options.preprocess = False
      except IOError:
        logging.warning(u'Storage file does not exist, running preprocess.')

    if not pre_obj:
      pre_obj = event.PreprocessObject()

    if options.preprocess and (options.process_image or options.recursive):
      platform = getattr(options, 'os', None)
      try:
        self._engine.PreprocessSource(pre_obj, platform)
      except IOError as exception:
        logging.error(u'Unable to preprocess with error: {0:s}'.format(
            exception))
        return

    self._PreprocessSetTimezone(options, pre_obj)
    self._PreprocessSetParserFilter(options, pre_obj)

    return pre_obj

  def ProcessSource(self, options):
    """Processes the source.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are incorrect or not supported.
    """
    try:
      # TODO: move scanner into engine.
      self._source_path_spec = self.ScanSource(options, self._source_path)
    except errors.FileSystemScannerError as exception:
      # TODO: make this a processing error.
      raise errors.BadConfigOption((
          u'Unable to scan for a supported filesystem with error: {0:s}.\n'
          u'Most likely the image format is not supported by the '
          u'tool.').format(exception))

    self.PrintOptions(options, self._source_path)

    if not options.image:
      options.recursive = os.path.isdir(self._source_path)
    else:
      options.recursive = False

    if options.image_offset_bytes is None:
      options.process_image = False

    else:
      options.process_image = True
      # If we're dealing with a storage media image always run pre-processing.
      options.preprocess = True

    self._CheckStorageFile(self._storage_file_path)

    if self._single_process_mode:
      self._ProcessSourceSingleProcessMode(options)
    else:
      self._ProcessSourceMultiProcessMode(options)

  def SetStorageFile(self, storage_file_path):
    """Sets the storage file path.

    Args:
      storage_file_path: The path of the storage file.
    """
    self._storage_file_path = storage_file_path
