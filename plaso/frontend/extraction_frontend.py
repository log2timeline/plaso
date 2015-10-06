# -*- coding: utf-8 -*-
"""The extraction front-end."""

import logging
import os
import pdb
import traceback

from dfvfs.helpers import source_scanner
from dfvfs.resolver import context

import plaso
from plaso import parsers   # pylint: disable=unused-import
from plaso import hashers   # pylint: disable=unused-import
from plaso.engine import single_process
from plaso.engine import utils as engine_utils
from plaso.frontend import frontend
from plaso.frontend import presets
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import storage
from plaso.lib import timelib
from plaso.multi_processing import multi_process
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager
from plaso.storage import writer as storage_writer

import pytz


class ExtractionFrontend(frontend.Frontend):
  """Class that implements an extraction front-end."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  # Approximately 250 MB of queued items per worker.
  _DEFAULT_QUEUE_SIZE = 125000

  def __init__(self):
    """Initializes the front-end object."""
    super(ExtractionFrontend, self).__init__()
    self._buffer_size = 0
    self._collection_process = None
    self._debug_mode = False
    self._enable_preprocessing = False
    self._enable_profiling = False
    self._engine = None
    self._filter_expression = None
    self._filter_object = None
    self._mount_path = None
    self._operating_system = None
    self._output_module = None
    self._parser_names = None
    self._process_archive_files = False
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._use_old_preprocess = False
    self._use_zeromq = False
    self._queue_size = self._DEFAULT_QUEUE_SIZE
    self._resolver_context = context.Context()
    self._single_process_mode = False
    self._show_worker_memory_information = False
    self._storage_file_path = None
    self._text_prepend = None

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

    if self._engine:
      self._engine.SignalAbort()

  def _GetParserFilterPreset(self, os_guess=u'', os_version=u''):
    """Determines the parser filter preset.

    Args:
      os_guess: optional string containing the operating system guessed by
                the preprocessing. The default is an empty string.
      os_version: optional string containing the operating system version
                  determined by the preprocessing. The default is an empty
                  string.

    Returns:
      The parser filter string or None.
    """
    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.

    parser_filter_string = None

    if not parser_filter_string and os_version:
      os_version = os_version.lower()

      # TODO: Improve this detection, this should be more 'intelligent', since
      # there are quite a lot of versions out there that would benefit from
      # loading up the set of 'winxp' parsers.
      if u'windows xp' in os_version:
        parser_filter_string = u'winxp'
      elif u'windows server 2000' in os_version:
        parser_filter_string = u'winxp'
      elif u'windows server 2003' in os_version:
        parser_filter_string = u'winxp'
      elif u'windows' in os_version:
        # Fallback for other Windows versions.
        parser_filter_string = u'win7'

    if not parser_filter_string and os_guess:
      if os_guess == definitions.OS_LINUX:
        parser_filter_string = u'linux'
      elif os_guess == definitions.OS_MACOSX:
        parser_filter_string = u'macosx'
      elif os_guess == definitions.OS_WINDOWS:
        parser_filter_string = u'win7'

    return parser_filter_string

  def _PreprocessSource(self, source_path_specs, source_type):
    """Preprocesses the source.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      source_type: the dfVFS source type definition.

    Returns:
      The preprocessing object (instance of PreprocessObject).
    """
    pre_obj = None

    if self._use_old_preprocess and os.path.isfile(self._storage_file_path):
      # Check if the storage file contains a preprocessing object.
      try:
        with storage.StorageFile(
            self._storage_file_path, read_only=True) as storage_file:

          storage_information = storage_file.GetStorageInformation()
          if storage_information:
            logging.info(u'Using preprocessing information from a prior run.')
            pre_obj = storage_information[-1]
            self._enable_preprocessing = False

      except IOError:
        logging.warning(u'Storage file does not exist, running preprocess.')

    logging.debug(u'Starting preprocessing.')

    # TODO: move source_scanner.SourceScannerContext.SOURCE_TYPE_
    # to definitions.SOURCE_TYPE_.
    if (self._enable_preprocessing and source_type in [
        source_scanner.SourceScannerContext.SOURCE_TYPE_DIRECTORY,
        source_scanner.SourceScannerContext.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        source_scanner.SourceScannerContext.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]):
      try:
        self._engine.PreprocessSource(
            source_path_specs, self._operating_system,
            resolver_context=self._resolver_context)

      except IOError as exception:
        logging.error(u'Unable to preprocess with error: {0:s}'.format(
            exception))
        return event.PreprocessObject()

    logging.debug(u'Preprocessing done.')

    # TODO: Remove the need for direct access to the pre_obj in favor
    # of the knowledge base.
    pre_obj = getattr(self._engine.knowledge_base, u'_pre_obj', None)

    if not pre_obj:
      pre_obj = event.PreprocessObject()

    return pre_obj

  # TODO: have the frontend fill collection information gradually
  # and set it as the last step of preprocessing?
  # Split in:
  # * extraction preferences (user preferences)
  # * extraction settings (actual settings used)
  # * output/storage settings
  # * processing settings
  # * source settings (support more than one source)
  #   * credentials (encryption)
  #   * mount point

  def _PreprocessSetCollectionInformation(
      self, pre_obj, source_type, unused_engine, command_line_arguments=None,
      filter_file=None, parser_filter_string=None, preferred_encoding=u'utf-8'):
    """Sets the collection information as part of the preprocessing.

    Args:
      pre_obj: the preprocess object (instance of PreprocessObject).
      source_type: the dfVFS source type definition.
      engine: the engine object (instance of BaseEngine).
      command_line_arguments: optional string of the command line arguments or
                              None if not set.
      filter_file: optional path to a file that contains find specifications.
      parser_filter_string: optional parser filter string.
      preferred_encoding: optional preferred encoding.
    """
    collection_information = {}

    # TODO: informational values.
    collection_information[u'version'] = plaso.GetVersion()
    collection_information[u'debug'] = self._debug_mode

    # TODO: extraction preferences:
    if not parser_filter_string:
      parser_filter_string = u'(no list set)'
    collection_information[u'parser_selection'] = parser_filter_string
    collection_information[u'preferred_encoding'] = preferred_encoding

    # TODO: extraction info:
    collection_information[u'configured_zone'] = pre_obj.zone
    collection_information[u'parsers'] = self._parser_names
    collection_information[u'preprocess'] = self._enable_preprocessing

    if self._filter_expression:
      collection_information[u'filter'] = self._filter_expression

    if filter_file and os.path.isfile(filter_file):
      filters = []
      with open(filter_file, 'rb') as file_object:
        for line in file_object.readlines():
          filters.append(line.rstrip())
      collection_information[u'file_filter'] = u', '.join(filters)

    if self._operating_system:
      collection_information[u'os_detected'] = self._operating_system
    else:
      collection_information[u'os_detected'] = u'N/A'

    # TODO: processing settings:
    collection_information[u'protobuf_size'] = self._buffer_size
    collection_information[u'time_of_run'] = timelib.Timestamp.GetNow()

    if self._single_process_mode:
      collection_information[u'runtime'] = u'single process mode'
    else:
      collection_information[u'runtime'] = u'multi process mode'
      # TODO: retrieve this value from the multi-process engine.
      # refactor engine to set number_of_extraction_workers
      # before ProcessSources.
      collection_information[u'workers'] = 0

    # TODO: output/storage settings:
    collection_information[u'output_file'] = self._storage_file_path

    # TODO: source settings:

    # TODO: move source_scanner.SourceScannerContext.SOURCE_TYPE_
    # to definitions.SOURCE_TYPE_.
    if source_type == source_scanner.SourceScannerContext.SOURCE_TYPE_DIRECTORY:
      recursive = True
    else:
      recursive = False

    # TODO: replace by scan node.
    # collection_information[u'file_processed'] = self._source_path
    collection_information[u'recursive'] = recursive
    # TODO: replace by scan node.
    # collection_information[u'vss parsing'] = bool(self.vss_stores)

    # TODO: move source_scanner.SourceScannerContext.SOURCE_TYPE_
    # to definitions.SOURCE_TYPE_.
    if source_type in [
        source_scanner.SourceScannerContext.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        source_scanner.SourceScannerContext.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      collection_information[u'method'] = u'imaged processed'
      # TODO: replace by scan node.
      # collection_information[u'image_offset'] = self.partition_offset
    else:
      collection_information[u'method'] = u'OS collection'

    collection_information[u'cmd_line'] = command_line_arguments

    pre_obj.collection_information = collection_information

  def _PreprocessSetTimezone(self, pre_obj, timezone=pytz.UTC):
    """Sets the timezone as part of the preprocessing.

    Args:
      pre_obj: the previously created preprocessing object (instance of
               PreprocessObject) or None.
      timezone: optional preferred timezone. The default is UTC.
    """
    if not timezone:
      timezone = pytz.UTC

    if hasattr(pre_obj, u'time_zone_str'):
      logging.info(u'Setting timezone to: {0:s}'.format(pre_obj.time_zone_str))

      try:
        pre_obj.zone = pytz.timezone(pre_obj.time_zone_str)

      except pytz.UnknownTimeZoneError:
        if not timezone:
          logging.warning(u'timezone was not properly set, defaulting to UTC')
          timezone = pytz.UTC
        else:
          logging.warning((
              u'Unable to automatically configure timezone falling back '
              u'to preferred timezone value: {0:s}').format(timezone))
        pre_obj.zone = timezone

    else:
      # TODO: shouldn't the user to be able to always override the timezone
      # detection? Or do we need an input sanitization function.
      pre_obj.zone = timezone

    if not getattr(pre_obj, u'zone', None):
      pre_obj.zone = timezone

  def GetHashersInformation(self):
    """Retrieves the hashers information.

    Returns:
      A list of tuples of hasher names and descriptions.
    """
    return hashers_manager.HashersManager.GetHashersInformation()

  def GetParserPluginsInformation(self, parser_filter_string=None):
    """Retrieves the parser plugins information.

    Args:
      parser_filter_string: Optional parser filter string, where None
                            represents all parsers and plugins.

    Returns:
      A list of tuples of parser plugin names and descriptions.
    """
    return parsers_manager.ParsersManager.GetParserPluginsInformation(
        parser_filter_string=parser_filter_string)

  def GetParserPresetsInformation(self):
    """Retrieves the parser presets information.

    Returns:
      A list of tuples of parser preset names and related parsers names.
    """
    parser_presets_information = []
    for preset_name, parser_names in sorted(presets.categories.items()):
      parser_presets_information.append((preset_name, u', '.join(parser_names)))

    return parser_presets_information

  def GetParsersInformation(self):
    """Retrieves the parsers information.

    Returns:
      A list of tuples of parser names and descriptions.
    """
    return parsers_manager.ParsersManager.GetParsersInformation()

  def GetNamesOfParsersWithPlugins(self):
    """Retrieves the names of parser with plugins.

    Returns:
      A list of parser names.
    """
    return parsers_manager.ParsersManager.GetNamesOfParsersWithPlugins()

  def ProcessSources(
      self, source_path_specs, source_type, command_line_arguments=None,
      enable_sigsegv_handler=False, filter_file=None, hasher_names_string=None,
      parser_filter_string=None, preferred_encoding=u'utf-8',
      single_process_mode=False, status_update_callback=None,
      storage_serializer_format=definitions.SERIALIZER_FORMAT_PROTOBUF,
      timezone=pytz.UTC):
    """Processes the sources.

    Args:
      source_path_specs: list of path specifications (instances of
                         dfvfs.PathSpec) to process.
      source_type: the dfVFS source type definition.
      command_line_arguments: optional string of the command line arguments or
                              None if not set.
      enable_sigsegv_handler: optional boolean value to indicate the SIGSEGV
                              handler should be enabled.
      filter_file: optional path to a file that contains find specifications.
      hasher_names_string: optional comma separated string of names of
                           hashers to enable.
      parser_filter_string: optional parser filter string.
      preferred_encoding: optional preferred encoding.
      single_process_mode: optional boolean value to indicate if the front-end
                           should run in single process mode.
      status_update_callback: optional callback function for status updates.
      storage_serializer_format: optional storage serializer format.
      timezone: optional preferred timezone.

    Returns:
      The processing status (instance of ProcessingStatus) or None.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
                          file system.
      UserAbort: if the user initiated an abort.
    """
    # If the source is a directory or a storage media image
    # run pre-processing.
    # TODO: move source_scanner.SourceScannerContext.SOURCE_TYPE_
    # to definitions.SOURCE_TYPE_.
    if source_type in [
        source_scanner.SourceScannerContext.SOURCE_TYPE_DIRECTORY,
        source_scanner.SourceScannerContext.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        source_scanner.SourceScannerContext.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      self.SetEnablePreprocessing(True)
    else:
      self.SetEnablePreprocessing(False)

    self._CheckStorageFile(self._storage_file_path)

    self._single_process_mode = single_process_mode
    # TODO: move source_scanner.SourceScannerContext.SOURCE_TYPE_
    # to definitions.SOURCE_TYPE_.
    if source_type == source_scanner.SourceScannerContext.SOURCE_TYPE_FILE:
      # No need to multi process a single file source.
      self._single_process_mode = True

    if self._single_process_mode:
      self._engine = single_process.SingleProcessEngine(self._queue_size)
    else:
      self._engine = multi_process.MultiProcessEngine(
          maximum_number_of_queued_items=self._queue_size,
          use_zeromq=self._use_zeromq)

    self._engine.SetEnableDebugOutput(self._debug_mode)
    self._engine.SetEnableProfiling(
        self._enable_profiling,
        profiling_sample_rate=self._profiling_sample_rate,
        profiling_type=self._profiling_type)

    pre_obj = self._PreprocessSource(source_path_specs, source_type)

    self._operating_system = getattr(pre_obj, u'guessed_os', None)

    if not parser_filter_string:
      guessed_os = self._operating_system
      os_version = getattr(pre_obj, u'osversion', u'')
      parser_filter_string = self._GetParserFilterPreset(
          os_guess=guessed_os, os_version=os_version)

      if parser_filter_string:
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            parser_filter_string))

    self._parser_names = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers(
        parser_filter_string=parser_filter_string):
      self._parser_names.append(parser_class.NAME)

    if u'filestat' in self._parser_names:
      include_directory_stat = True
    else:
      include_directory_stat = False

    self._hasher_names = []
    hasher_manager = hashers_manager.HashersManager
    for hasher_name in hasher_manager.GetHasherNamesFromString(
        hasher_names_string=hasher_names_string):
      self._hasher_names.append(hasher_name)

    self._PreprocessSetTimezone(pre_obj, timezone=timezone)

    if filter_file:
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(
          filter_file, pre_obj=pre_obj)
    else:
      filter_find_specs = None

    self._PreprocessSetCollectionInformation(
        pre_obj, source_type, self._engine,
        command_line_arguments=command_line_arguments, filter_file=filter_file,
        parser_filter_string=parser_filter_string,
        preferred_encoding=preferred_encoding)

    if self._output_module:
      storage_writer_object = storage_writer.BypassStorageWriter(
          self._engine.event_object_queue, self._storage_file_path,
          output_module_string=self._output_module, pre_obj=pre_obj)
    else:
      storage_writer_object = storage_writer.FileStorageWriter(
          self._engine.event_object_queue, self._storage_file_path,
          buffer_size=self._buffer_size, pre_obj=pre_obj,
          serializer_format=storage_serializer_format)

      storage_writer_object.SetEnableProfiling(
          self._enable_profiling,
          profiling_type=self._profiling_type)

    processing_status = None
    try:
      if self._single_process_mode:
        logging.debug(u'Starting extraction in single process mode.')

        processing_status = self._engine.ProcessSources(
            source_path_specs, storage_writer_object,
            filter_find_specs=filter_find_specs,
            filter_object=self._filter_object,
            hasher_names_string=hasher_names_string,
            include_directory_stat=include_directory_stat,
            mount_path=self._mount_path,
            parser_filter_string=parser_filter_string,
            process_archive_files=self._process_archive_files,
            resolver_context=self._resolver_context,
            status_update_callback=status_update_callback,
            text_prepend=self._text_prepend)

      else:
        logging.debug(u'Starting extraction in multi process mode.')

        # TODO: pass number_of_extraction_workers.
        processing_status = self._engine.ProcessSources(
            source_path_specs, storage_writer_object,
            enable_sigsegv_handler=enable_sigsegv_handler,
            filter_find_specs=filter_find_specs,
            filter_object=self._filter_object,
            hasher_names_string=hasher_names_string,
            include_directory_stat=include_directory_stat,
            mount_path=self._mount_path,
            parser_filter_string=parser_filter_string,
            process_archive_files=self._process_archive_files,
            status_update_callback=status_update_callback,
            show_memory_usage=self._show_worker_memory_information,
            text_prepend=self._text_prepend)

    except KeyboardInterrupt:
      self._CleanUpAfterAbort()
      raise errors.UserAbort

    # TODO: check if this still works and if still needed.
    except Exception as exception:
      if not self._single_process_mode:
        raise

      # The tool should generally not be run in single process mode
      # for other reasons than to debug. Hence the general error
      # catching.
      logging.error(u'An uncaught exception occurred: {0:s}.\n{1:s}'.format(
          exception, traceback.format_exc()))
      if self._debug_mode:
        pdb.post_mortem()

    return processing_status

  def SetDebugMode(self, enable_debug=False):
    """Enables or disables debug mode.

    Args:
      enable_debug: optional boolean value to indicate whether
                    debugging mode should be enabled. The default
                    is False.
    """
    self._debug_mode = enable_debug

  def SetEnablePreprocessing(self, enable_preprocessing):
    """Enables or disables preprocessing.

    Args:
      enable_preprocessing: boolean value to indicate if the preprocessing
                            should be performed.
    """
    self._enable_preprocessing = enable_preprocessing

  def SetEnableProfiling(
      self, enable_profiling, profiling_sample_rate=1000,
      profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if the profiling should
                        be enabled.
      profiling_sample_rate: optional integer indicating the profiling sample
                             rate. The value contains the number of files
                             processed. The default value is 1000.
      profiling_type: optional profiling type. The default is 'all'.
    """
    self._enable_profiling = enable_profiling
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

  def SetUseOldPreprocess(self, use_old_preprocess):
    """Set the use old preprocess flag.

    Args:
      use_old_preprocess: boolean value to indicate if the engine should
                          use the old preprocessing information or run
                          preprocessing again.
    """
    self._use_old_preprocess = use_old_preprocess

  def SetUseZeroMQ(self, use_zeromq=False):
    """Sets whether the tool is using ZeroMQ for queueing or not.

    Args:
      use_zeromq: Optional boolean, when True the tool will use ZeroMQ for
                  queuing.
    """
    self._use_zeromq = use_zeromq

  def SetStorageFile(self, storage_file_path):
    """Sets the storage file path.

    Args:
      storage_file_path: The path of the storage file.
    """
    self._storage_file_path = storage_file_path

  def SetStorageSerializer(self, storage_serializer_format):
    """Sets the storage serializer.

    Args:
      storage_serializer_format: string denoting the type of serializer
                                 to be used in the storage. The values
                                 can be either "proto" or "json".
    """
    if storage_serializer_format not in (
        self._EVENT_SERIALIZER_FORMAT_JSON,
        self._EVENT_SERIALIZER_FORMAT_PROTO):
      return

    self._storage_serializer_format = storage_serializer_format

  def SetShowMemoryInformation(self, show_memory=True):
    """Sets a flag telling the worker monitor to show memory information.

    Args:
      show_memory: a boolean (defaults to True) that indicates whether or not
                   the foreman should include memory information as part of
                   the worker monitoring.
    """
    self._show_worker_memory_information = show_memory

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: free form text that is prepended to each path.
    """
    self._text_prepend = text_prepend
