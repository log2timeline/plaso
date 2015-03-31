# -*- coding: utf-8 -*-
"""The extraction front-end functionality."""

import logging
import os
import pdb
import traceback

from dfvfs.resolver import context

import plaso
from plaso import parsers   # pylint: disable=unused-import
from plaso import hashers   # pylint: disable=unused-import
from plaso.engine import single_process
from plaso.engine import utils as engine_utils
from plaso.engine import worker
from plaso.frontend import frontend
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import storage
from plaso.lib import timelib
from plaso.multi_processing import multi_process
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager

import pytz


class ExtractionFrontend(frontend.StorageMediaFrontend):
  """Class that implements an extraction front-end."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  _EVENT_SERIALIZER_FORMAT_PROTO = u'proto'
  _EVENT_SERIALIZER_FORMAT_JSON = u'json'

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self, input_reader, output_writer):
    """Initializes the front-end object.

    Args:
      input_reader: the input reader (instance of FrontendInputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of FrontendOutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(ExtractionFrontend, self).__init__(input_reader, output_writer)
    self._buffer_size = 0
    self._collection_process = None
    self._collector = None
    self._debug_mode = False
    self._enable_profiling = False
    self._engine = None
    self._filter_expression = None
    self._filter_object = None
    self._mount_path = None
    self._number_of_worker_processes = 0
    self._old_preprocess = False
    self._operating_system = None
    self._output_module = None
    self._parser_names = None
    self._preprocess = False
    self._process_archive_files = False
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._run_foreman = True
    self._single_process_mode = False
    self._show_worker_memory_information = False
    self._storage_file_path = None
    self._storage_serializer_format = self._EVENT_SERIALIZER_FORMAT_PROTO
    self._timezone = pytz.utc

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

  # Note that this function is not called by the normal termination.
  def _CleanUpAfterAbort(self):
    """Signals the tool to stop running nicely after an abort."""
    if self._single_process_mode and self._debug_mode:
      logging.warning(u'Running in debug mode, set up debugger.')
      pdb.post_mortem()
      return

    if self._collector:
      logging.warning(u'Stopping collector.')
      self._collector.SignalEndOfInput()

    if self._engine:
      self._engine.SignalAbort()

  def _DebugPrintCollector(self, options):
    """Prints debug information about the collector.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    filter_file = getattr(options, 'file_filter', None)
    if self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      if filter_file:
        logging.debug(u'Starting a collection on image with filter.')
      else:
        logging.debug(u'Starting a collection on image.')

    elif self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_DIRECTORY]:
      if filter_file:
        logging.debug(u'Starting a collection on directory with filter.')
      else:
        logging.debug(u'Starting a collection on directory.')

    elif self._scan_context.source_type == self._scan_context.SOURCE_TYPE_FILE:
      logging.debug(u'Starting a collection on a single file.')

    else:
      logging.warning(u'Unsupported source type.')

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
    collection_information['configured_zone'] = self._timezone
    collection_information['file_processed'] = self._source_path
    collection_information['output_file'] = self._storage_file_path
    collection_information['protobuf_size'] = self._buffer_size
    collection_information['parser_selection'] = getattr(
        options, 'parsers', '(no list set)')
    collection_information['preferred_encoding'] = self.preferred_encoding
    collection_information['time_of_run'] = timelib.Timestamp.GetNow()

    collection_information['parsers'] = self._parser_names
    collection_information['preprocess'] = self._preprocess

    if self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_DIRECTORY]:
      recursive = True
    else:
      recursive = False
    collection_information['recursive'] = recursive
    collection_information['debug'] = self._debug_mode
    collection_information['vss parsing'] = bool(self._vss_stores)

    if self._filter_expression:
      collection_information['filter'] = self._filter_expression

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      if os.path.isfile(filter_file):
        filters = []
        with open(filter_file, 'rb') as fh:
          for line in fh:
            filters.append(line.rstrip())
        collection_information['file_filter'] = ', '.join(filters)

    if self._operating_system:
      collection_information['os_detected'] = self._operating_system
    else:
      collection_information['os_detected'] = 'N/A'

    if self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      collection_information['method'] = 'imaged processed'
      collection_information['image_offset'] = self._partition_offset
    else:
      collection_information['method'] = 'OS collection'

    if self._single_process_mode:
      collection_information['runtime'] = 'single process mode'
    else:
      collection_information['runtime'] = 'multi process mode'
      collection_information['workers'] = self._number_of_worker_processes

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

    # TODO: refactor putting the filter into the options object.
    # See if it can be passed in another way.
    if not getattr(options, 'filter', None):
      options.filter = u''

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
              u'to the user supplied one: {0:s}').format(self._timezone))
          pre_obj.zone = self._timezone
        else:
          logging.warning(u'timezone was not properly set, defaulting to UTC')
          pre_obj.zone = pytz.utc
    else:
      # TODO: shouldn't the user to be able to always override the timezone
      # detection? Or do we need an input sanitization function.
      pre_obj.zone = self._timezone

    if not getattr(pre_obj, 'zone', None):
      pre_obj.zone = self._timezone

  def _ProcessSourceMultiProcessMode(self, options):
    """Processes the source in a multiple process.

    Multiprocessing is used to start up separate processes.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    # TODO: replace by an option.
    start_collection_process = True

    self._number_of_worker_processes = getattr(options, 'workers', 0)

    logging.info(u'Starting extraction in multi process mode.')

    self._engine = multi_process.MultiProcessEngine(
        maximum_number_of_queued_items=self._queue_size)

    self._engine.SetEnableDebugOutput(self._debug_mode)
    self._engine.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate)
    self._engine.SetProcessArchiveFiles(self._process_archive_files)

    if self._filter_object:
      self._engine.SetFilterObject(self._filter_object)

    if self._mount_path:
      self._engine.SetMountPath(self._mount_path)

    if self._text_prepend:
      self._engine.SetTextPrepend(self._text_prepend)
    # TODO: add support to handle multiple partitions.
    self._engine.SetSource(
        self.GetSourcePathSpec(), resolver_context=self._resolver_context)

    logging.debug(u'Starting preprocessing.')
    pre_obj = self.PreprocessSource(options)
    logging.debug(u'Preprocessing done.')

    # TODO: make sure parsers option is not set by preprocessing.
    parser_filter_string = getattr(options, 'parsers', '')

    self._parser_names = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers(
        parser_filter_string=parser_filter_string):
      self._parser_names.append(parser_class.NAME)

    hasher_names_string = getattr(options, u'hashers', u'')

    self._hasher_names = []
    hasher_manager = hashers_manager.HashersManager
    for hasher_name in hasher_manager.GetHasherNamesFromString(
        hasher_names_string=hasher_names_string):
      self._hasher_names.append(hasher_name)

    self._PreprocessSetCollectionInformation(options, pre_obj)

    if 'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(
          filter_file, pre_obj=pre_obj)
    else:
      filter_find_specs = None

    if start_collection_process:
      resolver_context = context.Context()
    else:
      resolver_context = self._resolver_context

    # TODO: create multi process collector.
    self._collector = self._engine.CreateCollector(
        include_directory_stat, vss_stores=self._vss_stores,
        filter_find_specs=filter_find_specs, resolver_context=resolver_context)

    self._DebugPrintCollector(options)

    if self._output_module:
      storage_writer = storage.BypassStorageWriter(
          self._engine.storage_queue, self._storage_file_path,
          output_module_string=self._output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          self._engine.storage_queue, self._storage_file_path,
          buffer_size=self._buffer_size, pre_obj=pre_obj,
          serializer_format=self._storage_serializer_format)

    try:
      self._engine.ProcessSource(
          self._collector, storage_writer,
          parser_filter_string=parser_filter_string,
          hasher_names_string=hasher_names_string,
          number_of_extraction_workers=self._number_of_worker_processes,
          have_collection_process=start_collection_process,
          have_foreman_process=self._run_foreman,
          show_memory_usage=self._show_worker_memory_information)

    except KeyboardInterrupt:
      self._CleanUpAfterAbort()
      raise errors.UserAbort(u'Process source aborted.')

  def _ProcessSourceSingleProcessMode(self, options):
    """Processes the source in a single process.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    logging.info(u'Starting extraction in single process mode.')

    try:
      self._StartSingleThread(options)
    except Exception as exception:
      # The tool should generally not be run in single process mode
      # for other reasons than to debug. Hence the general error
      # catching.
      logging.error(u'An uncaught exception occurred: {0:s}.\n{1:s}'.format(
          exception, traceback.format_exc()))
      if self._debug_mode:
        pdb.post_mortem()

  def _StartSingleThread(self, options):
    """Starts everything up in a single process.

    This should not normally be used, since running the tool in a single
    process buffers up everything into memory until the storage is called.

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
    self._engine = single_process.SingleProcessEngine(self._queue_size)
    self._engine.SetEnableDebugOutput(self._debug_mode)
    self._engine.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate)
    self._engine.SetProcessArchiveFiles(self._process_archive_files)

    if self._filter_object:
      self._engine.SetFilterObject(self._filter_object)

    if self._mount_path:
      self._engine.SetMountPath(self._mount_path)

    if self._text_prepend:
      self._engine.SetTextPrepend(self._text_prepend)

    # TODO: add support to handle multiple partitions.
    self._engine.SetSource(
        self.GetSourcePathSpec(), resolver_context=self._resolver_context)

    logging.debug(u'Starting preprocessing.')
    pre_obj = self.PreprocessSource(options)

    logging.debug(u'Preprocessing done.')

    # TODO: make sure parsers option is not set by preprocessing.
    parser_filter_string = getattr(options, 'parsers', '')

    self._parser_names = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers(
        parser_filter_string=parser_filter_string):
      self._parser_names.append(parser_class.NAME)

    self._PreprocessSetCollectionInformation(options, pre_obj)

    if 'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(
          filter_file, pre_obj=pre_obj)
    else:
      filter_find_specs = None

    self._collector = self._engine.CreateCollector(
        include_directory_stat, vss_stores=self._vss_stores,
        filter_find_specs=filter_find_specs,
        resolver_context=self._resolver_context)

    self._DebugPrintCollector(options)

    if self._output_module:
      storage_writer = storage.BypassStorageWriter(
          self._engine.storage_queue, self._storage_file_path,
          output_module_string=self._output_module, pre_obj=pre_obj)
    else:
      storage_writer = storage.StorageFileWriter(
          self._engine.storage_queue, self._storage_file_path,
          buffer_size=self._buffer_size, pre_obj=pre_obj,
          serializer_format=self._storage_serializer_format)

    hasher_names_string = getattr(options, u'hashers', u'')

    try:
      self._engine.ProcessSource(
          self._collector, storage_writer,
          parser_filter_string=parser_filter_string,
          hasher_names_string=hasher_names_string)

    except KeyboardInterrupt:
      self._CleanUpAfterAbort()
      raise errors.UserAbort(u'Process source aborted.')

    finally:
      self._resolver_context.Empty()

  def AddExtractionOptions(self, argument_group):
    """Adds the extraction options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '--use_old_preprocess', '--use-old-preprocess', dest='old_preprocess',
        action='store_true', default=False, help=(
            u'Only used in conjunction when appending to a previous storage '
            u'file. When this option is used then a new preprocessing object '
            u'is not calculated and instead the last one that got added to '
            u'the storage file is used. This can be handy when parsing an '
            u'image that contains more than a single partition.'))

  def AddInformationalOptions(self, argument_group):
    """Adds the informational options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '-d', '--debug', dest='debug', action='store_true', default=False,
        help=(
            u'Enable debug mode. Intended for troubleshooting parsing '
            u'issues.'))

  def AddPerformanceOptions(self, argument_group):
    """Adds the performance options to the argument group.

    Args:
      argument_group: The argparse argument group (instance of
                      argparse._ArgumentGroup).
    """
    argument_group.add_argument(
        '--buffer_size', '--buffer-size', '--bs', dest='buffer_size',
        action='store', default=0,
        help=u'The buffer size for the output (defaults to 196MiB).')

    argument_group.add_argument(
        '--queue_size', '--queue-size', dest='queue_size', action='store',
        default=0, help=(
            u'The maximum number of queued items per worker '
            u'(defaults to {0:d})').format(self._DEFAULT_QUEUE_SIZE))

    if worker.BaseEventExtractionWorker.SupportsProfiling():
      argument_group.add_argument(
          '--profile', dest='enable_profiling', action='store_true',
          default=False, help=(
              u'Enable profiling of memory usage. Intended for '
              u'troubleshooting memory issues.'))

      argument_group.add_argument(
          '--profile_sample_rate', '--profile-sample-rate',
          dest='profile_sample_rate', action='store', default=0, help=(
              u'The profile sample rate (defaults to a sample every {0:d} '
              u'files).').format(self._DEFAULT_PROFILING_SAMPLE_RATE))

  def GetSourceFileSystemSearcher(self):
    """Retrieves the file system searcher of the source.

    Returns:
      The file system searcher object (instance of dfvfs.FileSystemSearcher).
    """
    return self._engine.GetSourceFileSystemSearcher(
        resolver_context=self._resolver_context)

  def ParseOptions(self, options, source_option='source'):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: optional name of the source option. The default is source.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ExtractionFrontend, self).ParseOptions(
        options, source_option=source_option)

    self._buffer_size = getattr(options, 'buffer_size', 0)
    if self._buffer_size:
      # TODO: turn this into a generic function that supports more size
      # suffixes both MB and MiB and also that does not allow m as a valid
      # indicator for MiB since m represents milli not Mega.
      try:
        if self._buffer_size[-1].lower() == 'm':
          self._buffer_size = int(self._buffer_size[:-1], 10)
          self._buffer_size *= self._BYTES_IN_A_MIB
        else:
          self._buffer_size = int(self._buffer_size, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid buffer size: {0:s}.'.format(self._buffer_size))

    queue_size = getattr(options, 'queue_size', None)
    if queue_size:
      try:
        self._queue_size = int(queue_size, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid queue size: {0:s}.'.format(queue_size))

    self._enable_profiling = getattr(options, 'enable_profiling', False)

    profile_sample_rate = getattr(options, 'profile_sample_rate', None)
    if profile_sample_rate:
      try:
        self._profiling_sample_rate = int(profile_sample_rate, 10)
      except ValueError:
        raise errors.BadConfigOption(
            u'Invalid profile sample rate: {0:s}.'.format(profile_sample_rate))

    serializer_format = getattr(
        options, 'serializer_format', self._EVENT_SERIALIZER_FORMAT_PROTO)
    if serializer_format:
      self.SetStorageSerializer(serializer_format)

    self._filter_expression = getattr(options, 'filter', None)
    if self._filter_expression:
      self._filter_object = pfilter.GetMatcher(self._filter_expression)
      if not self._filter_object:
        raise errors.BadConfigOption(
            u'Invalid filter expression: {0:s}'.format(self._filter_expression))

    filter_file = getattr(options, 'file_filter', None)
    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'No such collection filter file: {0:s}.'.format(filter_file))

    self._debug_mode = getattr(options, 'debug', False)

    self._old_preprocess = getattr(options, 'old_preprocess', False)

    timezone_string = getattr(options, 'timezone', None)
    if timezone_string:
      self._timezone = pytz.timezone(timezone_string)

    self._single_process_mode = getattr(
        options, 'single_process', False)

    self._output_module = getattr(options, 'output_module', None)

    self._operating_system = getattr(options, 'os', None)
    self._process_archive_files = getattr(options, 'scan_archives', False)
    self._text_prepend = getattr(options, 'text_prepend', None)

    if self._operating_system:
      self._mount_path = getattr(options, 'filename', None)

  def PreprocessSource(self, options):
    """Preprocesses the source.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Returns:
      The preprocessing object (instance of PreprocessObject).
    """
    pre_obj = None

    if self._old_preprocess and os.path.isfile(self._storage_file_path):
      # Check if the storage file contains a preprocessing object.
      try:
        with storage.StorageFile(
            self._storage_file_path, read_only=True) as store:
          storage_information = store.GetStorageInformation()
          if storage_information:
            logging.info(u'Using preprocessing information from a prior run.')
            pre_obj = storage_information[-1]
            self._preprocess = False
      except IOError:
        logging.warning(u'Storage file does not exist, running preprocess.')

    if self._preprocess and self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_DIRECTORY,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      try:
        self._engine.PreprocessSource(
            self._operating_system, resolver_context=self._resolver_context)
      except IOError as exception:
        logging.error(u'Unable to preprocess with error: {0:s}'.format(
            exception))
        return

    # TODO: Remove the need for direct access to the pre_obj in favor
    # of the knowledge base.
    pre_obj = getattr(self._engine.knowledge_base, '_pre_obj', None)

    if not pre_obj:
      pre_obj = event.PreprocessObject()

    self._PreprocessSetTimezone(options, pre_obj)
    self._PreprocessSetParserFilter(options, pre_obj)

    return pre_obj

  def PrintOptions(self, options, source_path):
    """Prints the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_path: the source path.
    """
    self._output_writer.Write(u'\n')
    self._output_writer.Write(
        u'Source path\t\t\t\t: {0:s}\n'.format(source_path))

    if self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      is_image = True
    else:
      is_image = False

    self._output_writer.Write(
        u'Is storage media image or device\t: {0!s}\n'.format(is_image))

    if is_image:
      image_offset_bytes = self._partition_offset
      if isinstance(image_offset_bytes, basestring):
        try:
          image_offset_bytes = int(image_offset_bytes, 10)
        except ValueError:
          image_offset_bytes = 0
      elif image_offset_bytes is None:
        image_offset_bytes = 0

      self._output_writer.Write(
          u'Partition offset\t\t\t: {0:d} (0x{0:08x})\n'.format(
              image_offset_bytes))

      if self._process_vss and self._vss_stores:
        self._output_writer.Write(
            u'VSS stores\t\t\t\t: {0!s}\n'.format(self._vss_stores))

    filter_file = getattr(options, 'file_filter', None)
    if filter_file:
      self._output_writer.Write(u'Filter file\t\t\t\t: {0:s}\n'.format(
          filter_file))

    self._output_writer.Write(u'\n')

  def ProcessSource(self, options):
    """Processes the source.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      SourceScannerError: if the source scanner could not find a supported
                          file system.
      UserAbort: if the user initiated an abort.
    """
    self.ScanSource(options)

    self.PrintOptions(options, self._source_path)

    if self._partition_offset is None:
      self._preprocess = False

    else:
      # If we're dealing with a storage media image always run pre-processing.
      self._preprocess = True

    self._CheckStorageFile(self._storage_file_path)

    # No need to multi process when we're only processing a single file.
    if self._scan_context.source_type == self._scan_context.SOURCE_TYPE_FILE:
      # If we are only processing a single file we don't need more than a
      # single worker.
      # TODO: Refactor this use of using the options object.
      options.workers = 1
      self._single_process_mode = True

    if self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_DIRECTORY]:
      # If we are dealing with a directory we would like to attempt
      # pre-processing.
      self._preprocess = True

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

  def SetStorageSerializer(self, storage_serializer_format):
    """Sets the storage serializer.

    Args:
      storage_serializer_format: String denoting the type of serializer
                                 to be used in the storage. The values
                                 can be either "proto" or "json".
    """
    if storage_serializer_format not in (
        self._EVENT_SERIALIZER_FORMAT_JSON,
        self._EVENT_SERIALIZER_FORMAT_PROTO):
      return
    self._storage_serializer_format = storage_serializer_format

  def SetRunForeman(self, run_foreman=True):
    """Sets a flag indicating whether the frontend should monitor workers.

    Args:
      run_foreman: A boolean (defaults to true) that indicates whether or not
                   the frontend should start a foreman that monitors workers.
    """
    self._run_foreman = run_foreman

  def SetShowMemoryInformation(self, show_memory=True):
    """Sets a flag telling the worker monitor to show memory information.

    Args:
      show_memory: A boolean (defaults to True) that indicates whether or not
                   the foreman should include memory information as part of
                   the worker monitoring.
    """
    self._show_worker_memory_information = show_memory
