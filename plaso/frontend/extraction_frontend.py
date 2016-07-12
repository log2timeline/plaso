# -*- coding: utf-8 -*-
"""The extraction front-end."""

import logging
import os

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context

from plaso import hashers   # pylint: disable=unused-import
from plaso import parsers   # pylint: disable=unused-import
from plaso.containers import sessions
from plaso.engine import single_process
from plaso.engine import utils as engine_utils
from plaso.frontend import frontend
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import event
from plaso.multi_processing import engine as multi_process_engine
from plaso.hashers import manager as hashers_manager
from plaso.parsers import manager as parsers_manager
from plaso.parsers import presets as parsers_presets
from plaso.storage import zip_file as storage_zip_file

import pytz  # pylint: disable=wrong-import-order


class ExtractionFrontend(frontend.Frontend):
  """Class that implements an extraction front-end."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  def __init__(self):
    """Initializes the front-end object."""
    super(ExtractionFrontend, self).__init__()
    self._collection_process = None
    self._debug_mode = False
    self._enable_preprocessing = False
    self._enable_profiling = False
    self._engine = None
    self._filter_expression = None
    self._filter_object = None
    self._hasher_names = []
    self._mount_path = None
    self._operating_system = None
    self._parser_names = None
    self._profiling_directory = None
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._use_old_preprocess = False
    self._use_zeromq = True
    self._resolver_context = context.Context()
    self._show_worker_memory_information = False
    self._storage_file_path = None
    self._text_prepend = None

  def _CheckStorageFile(self, storage_file_path):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path (str): path of the storage file.

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
      dirname = u'.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          u'Unable to write to storage file: {0:s}'.format(storage_file_path))

  def _CreateEngine(self, single_process_mode):
    """Creates an engine based on the front end settings.

    Args:
      single_process_mode (bool): True if the front-end should run in single
          process mode.

    Returns:
      BaseEngine: engine.
    """
    if single_process_mode:
      engine = single_process.SingleProcessEngine(
          enable_profiling=self._enable_profiling,
          profiling_directory=self._profiling_directory,
          profiling_sample_rate=self._profiling_sample_rate,
          profiling_type=self._profiling_type)
    else:
      engine = multi_process_engine.MultiProcessEngine(
          enable_profiling=self._enable_profiling,
          profiling_directory=self._profiling_directory,
          profiling_sample_rate=self._profiling_sample_rate,
          profiling_type=self._profiling_type, use_zeromq=self._use_zeromq)

    engine.SetEnableDebugOutput(self._debug_mode)

    return engine

  def _CreateSession(
      self, command_line_arguments=None, filter_file=None,
      parser_filter_expression=None, preferred_encoding=u'utf-8',
      preferred_year=None):
    """Creates the session start information.

    Args:
      command_line_arguments (Optional[str]): the command line arguments.
      filter_file (Optional[str]): path to a file with find specifications.
      parser_filter_expression (Optional[str]): parser filter expression.
      preferred_encoding (Optional[str]): preferred encoding.
      preferred_year (Optional[int]): preferred year.

    Returns:
      Session: session attribute container.
    """
    session = sessions.Session()

    session.command_line_arguments = command_line_arguments
    session.filter_expression = self._filter_expression
    session.filter_file = filter_file
    session.debug_mode = self._debug_mode
    session.parser_filter_expression = parser_filter_expression
    session.preferred_encoding = preferred_encoding
    session.preferred_year = preferred_year

    return session

  def _GetParserFilterPreset(self, os_guess=u'', os_version=u''):
    """Determines the parser filter preset.

    Args:
      os_guess: optional string containing the operating system guessed by
                the preprocessing.
      os_version: optional string containing the operating system version
                  determined by the preprocessing.

    Returns:
      A string containing the parser filter preset, where None represents
      all parsers and plugins.
    """
    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.

    parser_filter_preset = None

    if not parser_filter_preset and os_version:
      os_version = os_version.lower()

      # TODO: Improve this detection, this should be more 'intelligent', since
      # there are quite a lot of versions out there that would benefit from
      # loading up the set of 'winxp' parsers.
      if u'windows xp' in os_version:
        parser_filter_preset = u'winxp'
      elif u'windows server 2000' in os_version:
        parser_filter_preset = u'winxp'
      elif u'windows server 2003' in os_version:
        parser_filter_preset = u'winxp'
      elif u'windows' in os_version:
        # Fallback for other Windows versions.
        parser_filter_preset = u'win7'

    if not parser_filter_preset and os_guess:
      if os_guess == definitions.OS_LINUX:
        parser_filter_preset = u'linux'
      elif os_guess == definitions.OS_MACOSX:
        parser_filter_preset = u'macosx'
      elif os_guess == definitions.OS_WINDOWS:
        parser_filter_preset = u'win7'

    return parser_filter_preset

  def _PreprocessSources(self, source_path_specs, source_type):
    """Preprocesses the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      source_type (str): the dfVFS source type definition.

    Returns:
      The preprocessing object (instance of PreprocessObject).
    """
    preprocess_object = None

    if self._use_old_preprocess and os.path.isfile(self._storage_file_path):
      # Check if the storage file contains a preprocessing object.
      storage_file = None
      try:
        # TODO: refactor to use storage reader interface.
        storage_file = storage_zip_file.StorageFile(
            self._storage_file_path, read_only=True)
        storage_information = storage_file.GetStorageInformation()
        if storage_information:
          logging.info(u'Using preprocessing information from a prior run.')
          preprocess_object = storage_information[-1]
          self._enable_preprocessing = False

      except IOError:
        logging.warning(
            u'Unable to retrieve preprocessing information from storage file.')

      finally:
        if storage_file:
          storage_file.Close()

    logging.debug(u'Starting preprocessing.')

    if (self._enable_preprocessing and source_type in [
        dfvfs_definitions.SOURCE_TYPE_DIRECTORY,
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]):
      try:
        self._engine.PreprocessSources(
            source_path_specs, resolver_context=self._resolver_context)

      except IOError as exception:
        logging.error(u'Unable to preprocess with error: {0:s}'.format(
            exception))
        return event.PreprocessObject()

    logging.debug(u'Preprocessing done.')

    # TODO: Remove the need for direct access to the preprocess_object in favor
    # of the knowledge base.
    preprocess_object = getattr(self._engine.knowledge_base, u'_pre_obj', None)

    if not preprocess_object:
      preprocess_object = event.PreprocessObject()

    return preprocess_object

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

  def _PreprocessSetCollectionInformation(self, preprocess_object):
    """Sets the collection information as part of the preprocessing.

    Args:
      preprocess_object: a preprocess object (instance of PreprocessObject).
      engine: the engine object (instance of BaseEngine).
    """
    collection_information = {}

    # TODO: extraction info:
    collection_information[u'configured_zone'] = preprocess_object.zone
    collection_information[u'parsers'] = self._parser_names
    collection_information[u'preprocess'] = self._enable_preprocessing

    if self._operating_system:
      collection_information[u'os_detected'] = self._operating_system
    else:
      collection_information[u'os_detected'] = u'N/A'

    preprocess_object.collection_information = collection_information

  def _PreprocessSetTimezone(self, preprocess_object, timezone=pytz.UTC):
    """Sets the timezone as part of the preprocessing.

    Args:
      preprocess_object: a preprocess object (instance of PreprocessObject).
      timezone: optional preferred timezone.
    """
    if not timezone:
      timezone = pytz.UTC

    if hasattr(preprocess_object, u'time_zone_str'):
      logging.info(u'Setting timezone to: {0:s}'.format(
          preprocess_object.time_zone_str))

      try:
        preprocess_object.zone = pytz.timezone(preprocess_object.time_zone_str)

      except pytz.UnknownTimeZoneError:
        if not timezone:
          logging.warning(u'timezone was not properly set, defaulting to UTC')
          timezone = pytz.UTC
        else:
          logging.warning((
              u'Unable to automatically configure timezone falling back '
              u'to preferred timezone value: {0:s}').format(timezone))
        preprocess_object.zone = timezone

    else:
      # TODO: shouldn't the user to be able to always override the timezone
      # detection? Or do we need an input sanitization function.
      preprocess_object.zone = timezone

    if not getattr(preprocess_object, u'zone', None):
      preprocess_object.zone = timezone

  def DisableProfiling(self):
    """Disabled profiling."""
    self._enable_profiling = False

  def EnableProfiling(
      self, profiling_directory=None, profiling_sample_rate=1000,
      profiling_type=u'all'):
    """Enables profiling.

    Args:
      profiling_directory (Optional[str]): path to the directory where
          the profiling sample files should be stored.
      profiling_sample_rate (Optional[int]): the profiling sample rate.
          Contains the number of event sources processed.
      profiling_type (Optional[str]): type of profiling.
          Supported types are:

          * 'memory' to profile memory usage;
          * 'parsers' to profile CPU time consumed by individual parsers;
          * 'processing' to profile CPU time consumed by different parts of
            the processing;
          * 'serializers' to profile CPU time consumed by individual
            serializers.
    """
    self._enable_profiling = True
    self._profiling_directory = profiling_directory
    self._profiling_sample_rate = profiling_sample_rate
    self._profiling_type = profiling_type

  def GetHashersInformation(self):
    """Retrieves the hashers information.

    Returns:
      A list of tuples of hasher names and descriptions.
    """
    return hashers_manager.HashersManager.GetHashersInformation()

  def GetParserPluginsInformation(self, parser_filter_expression=None):
    """Retrieves the parser plugins information.

    Args:
      parser_filter_expression: optional string containing the parser filter
                                expression, where None represents all parsers
                                and plugins.

    Returns:
      A list of tuples of parser plugin names and descriptions.
    """
    return parsers_manager.ParsersManager.GetParserPluginsInformation(
        parser_filter_expression=parser_filter_expression)

  def GetParserPresetsInformation(self):
    """Retrieves the parser presets information.

    Returns:
      A list of tuples of parser preset names and related parsers names.
    """
    parser_presets_information = []
    for preset_name, parser_names in sorted(parsers_presets.CATEGORIES.items()):
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
      enable_sigsegv_handler=False, filter_file=None,
      force_preprocessing=False, hasher_names_string=None,
      number_of_extraction_workers=0, parser_filter_expression=None,
      preferred_encoding=u'utf-8', preferred_year=None,
      process_archive_files=False, single_process_mode=False,
      status_update_callback=None, temporary_directory=None, timezone=pytz.UTC):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      source_type (str): the dfVFS source type definition.
      command_line_arguments (Optional[str]): the command line arguments.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      filter_file (Optional[str]): path to a file that contains find
          specifications.
      force_preprocessing (Optional[bool]): True if preprocessing should be
          forced.
      hasher_names_string (Optional[str]): comma separated string of names
          of hashers to use during processing.
      number_of_extraction_workers (Optional[int]): number of extraction
          workers to run. If 0, the number will be selected automatically.
      parser_filter_expression (Optional[str]): parser filter expression.
      preferred_encoding (Optional[str]): preferred encoding.
      preferred_year (Optional[int]): preferred year.
      process_archive_files (Optional[bool]): True if archive files should be
          scanned for file entries.
      single_process_mode (Optional[bool]): True if the front-end should
          run in single process mode.
      status_update_callback (Optional[function]): callback function for status
          updates.
      temporary_directory (Optional[str]): path of the directory for temporary
          files.
      timezone (Optional[datetime.tzinfo]): timezone.

    Returns:
      The processing status (instance of ProcessingStatus) or None.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
                          file system.
      UserAbort: if the user initiated an abort.
    """
    # If the source is a directory or a storage media image
    # run pre-processing.
    if force_preprocessing or source_type in [
        dfvfs_definitions.SOURCE_TYPE_DIRECTORY,
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      self.SetEnablePreprocessing(True)
    else:
      self.SetEnablePreprocessing(False)

    self._CheckStorageFile(self._storage_file_path)

    if source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      # No need to multi process a single file source.
      single_process_mode = True

    self._engine = self._CreateEngine(single_process_mode)

    preprocess_object = self._PreprocessSources(source_path_specs, source_type)

    self._operating_system = getattr(preprocess_object, u'guessed_os', None)

    if not parser_filter_expression:
      guessed_os = self._operating_system
      os_version = getattr(preprocess_object, u'osversion', u'')
      parser_filter_expression = self._GetParserFilterPreset(
          os_guess=guessed_os, os_version=os_version)

      if parser_filter_expression:
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            parser_filter_expression))

    self._parser_names = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers(
        parser_filter_expression=parser_filter_expression):
      self._parser_names.append(parser_class.NAME)

    self._hasher_names = []
    hasher_manager = hashers_manager.HashersManager
    for hasher_name in hasher_manager.GetHasherNamesFromString(
        hasher_names_string=hasher_names_string):
      self._hasher_names.append(hasher_name)

    self._PreprocessSetTimezone(preprocess_object, timezone=timezone)

    if filter_file:
      path_attributes = self._engine.knowledge_base.GetPathAttributes()
      filter_find_specs = engine_utils.BuildFindSpecsFromFile(
          filter_file, path_attributes=path_attributes)
    else:
      filter_find_specs = None

    # TODO: deprecate the need for this function.
    self._PreprocessSetCollectionInformation(preprocess_object)

    session = self._CreateSession(
        command_line_arguments=command_line_arguments, filter_file=filter_file,
        parser_filter_expression=parser_filter_expression,
        preferred_encoding=preferred_encoding, preferred_year=preferred_year)

    # TODO: we are directly invoking ZIP file storage here. In storage rewrite
    # come up with a more generic solution.
    storage_writer = storage_zip_file.ZIPStorageFileWriter(
        session, self._storage_file_path)

    processing_status = None
    if single_process_mode:
      logging.debug(u'Starting extraction in single process mode.')

      processing_status = self._engine.ProcessSources(
          source_path_specs, preprocess_object, storage_writer,
          self._resolver_context, filter_find_specs=filter_find_specs,
          filter_object=self._filter_object,
          hasher_names_string=hasher_names_string,
          mount_path=self._mount_path,
          parser_filter_expression=parser_filter_expression,
          preferred_year=preferred_year,
          process_archive_files=process_archive_files,
          status_update_callback=status_update_callback,
          temporary_directory=temporary_directory,
          text_prepend=self._text_prepend)

    else:
      logging.debug(u'Starting extraction in multi process mode.')

      processing_status = self._engine.ProcessSources(
          session.identifier, source_path_specs, preprocess_object,
          storage_writer, enable_sigsegv_handler=enable_sigsegv_handler,
          filter_find_specs=filter_find_specs,
          filter_object=self._filter_object,
          hasher_names_string=hasher_names_string,
          mount_path=self._mount_path,
          number_of_worker_processes=number_of_extraction_workers,
          parser_filter_expression=parser_filter_expression,
          preferred_year=preferred_year,
          process_archive_files=process_archive_files,
          status_update_callback=status_update_callback,
          show_memory_usage=self._show_worker_memory_information,
          temporary_directory=temporary_directory,
          text_prepend=self._text_prepend)

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

  def SetShowMemoryInformation(self, show_memory=True):
    """Sets a flag telling the worker monitor to show memory information.

    Args:
      show_memory: a boolean (defaults to True) that indicates whether or not
                   the foreman should include memory information as part of
                   the worker monitoring.
    """
    self._show_worker_memory_information = show_memory

  def SetStorageFile(self, storage_file_path):
    """Sets the storage file path.

    Args:
      storage_file_path: The path of the storage file.
    """
    self._storage_file_path = storage_file_path

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: free form text that is prepended to each path.
    """
    self._text_prepend = text_prepend

  def SetUseOldPreprocess(self, use_old_preprocess):
    """Set the use old preprocess flag.

    Args:
      use_old_preprocess: boolean value to indicate if the engine should
                          use the old preprocessing information or run
                          preprocessing again.
    """
    self._use_old_preprocess = use_old_preprocess

  def SetUseZeroMQ(self, use_zeromq=True):
    """Sets whether the frontend is using ZeroMQ for queueing or not.

    Args:
      use_zeromq: optional boolean value to indicate if ZeroMQ should be used
                  for queuing.
    """
    self._use_zeromq = use_zeromq
