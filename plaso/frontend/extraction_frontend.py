# -*- coding: utf-8 -*-
"""The extraction front-end."""

import logging
import os

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context

from plaso import parsers   # pylint: disable=unused-import
from plaso.analyzers.hashers import manager as hashers_manager
from plaso.containers import sessions
from plaso.engine import single_process
from plaso.frontend import frontend
from plaso.frontend import utils
from plaso.lib import definitions
from plaso.lib import errors
from plaso.multi_processing import task_engine as multi_process_engine
from plaso.parsers import manager as parsers_manager
from plaso.parsers import presets as parsers_presets
from plaso.storage import zip_file as storage_zip_file


class ExtractionFrontend(frontend.Frontend):
  """Class that implements an extraction front-end."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  _SOURCE_TYPES_TO_PREPROCESS = frozenset([
      dfvfs_definitions.SOURCE_TYPE_DIRECTORY,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE])

  def __init__(self):
    """Initializes the front-end object."""
    super(ExtractionFrontend, self).__init__()
    self._collection_process = None
    self._debug_mode = False
    self._filter_expression = None
    self._filter_object = None
    self._mount_path = None
    self._profiling_directory = None
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._use_zeromq = True
    self._resolver_context = context.Context()
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
      engine = single_process.SingleProcessEngine()
    else:
      engine = multi_process_engine.TaskMultiProcessEngine(
          use_zeromq=self._use_zeromq)

    return engine

  def _GetParserFilterPreset(
      self, operating_system, operating_system_product,
      operating_system_version):
    """Determines the parser filter preset.

    Args:
      operating_system (str): operating system for example "Windows". This
          should be one of the values in definitions.OPERATING_SYSTEMS.
      operating_system_product (str): operating system product for
          example "Windows XP" as determined by preprocessing.
      operating_system_version (str): operating system version for
          example "5.1" as determined by preprocessing.

    Returns:
      str: parser filter preset, where None represents all parsers and plugins.
    """
    # TODO: Make this more sane. Currently we are only checking against
    # one possible version of Windows, and then making the assumption if
    # that is not correct we default to Windows 7. Same thing with other
    # OS's, no assumption or checks are really made there.
    # Also this is done by default, and no way for the user to turn off
    # this behavior, need to add a parameter to the frontend that takes
    # care of overwriting this behavior.

    if operating_system == definitions.OPERATING_SYSTEM_LINUX:
      return u'linux'

    if operating_system == definitions.OPERATING_SYSTEM_MACOSX:
      return u'macosx'

    if operating_system_product:
      operating_system_product = operating_system_product.lower()
    else:
      operating_system_product = u''

    if operating_system_version:
      operating_system_version = operating_system_version.split(u'.')
    else:
      operating_system_version = [u'0', u'0']

    # Windows NT 5 (2000, XP and 2003).
    if (u'windows' in operating_system_product and
        operating_system_version[0] == u'5'):
      return u'winxp'

    # TODO: Improve this detection, this should be more 'intelligent', since
    # there are quite a lot of versions out there that would benefit from
    # loading up the set of 'winxp' parsers.
    if (u'windows xp' in operating_system_product or
        u'windows server 2000' in operating_system_product or
        u'windows server 2003' in operating_system_product):
      return u'winxp'

    # Fallback for other Windows versions.
    if u'windows' in operating_system_product:
      return u'win7'

    if operating_system == definitions.OPERATING_SYSTEM_WINDOWS:
      return u'win7'

    return

  def _PreprocessSources(self, engine, source_path_specs):
    """Preprocesses the sources.

    Args:
      engine (BaseEngine): engine to preprocess the sources.
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
    """
    logging.debug(u'Starting preprocessing.')

    try:
      engine.PreprocessSources(
          source_path_specs, resolver_context=self._resolver_context)

    except IOError as exception:
      logging.error(u'Unable to preprocess with error: {0:s}'.format(
          exception))
      return

    logging.debug(u'Preprocessing done.')

  def CreateSession(
      self, command_line_arguments=None, filter_file=None,
      preferred_encoding=u'utf-8', preferred_time_zone=None,
      preferred_year=None):
    """Creates a session attribute containiner.

    Args:
      command_line_arguments (Optional[str]): the command line arguments.
      filter_file (Optional[str]): path to a file with find specifications.
      preferred_encoding (Optional[str]): preferred encoding.
      preferred_time_zone (Optional[str]): preferred time zone.
      preferred_year (Optional[int]): preferred year.

    Returns:
      Session: session attribute container.
    """
    session = sessions.Session()

    session.command_line_arguments = command_line_arguments
    session.filter_expression = self._filter_expression
    session.filter_file = filter_file
    session.debug_mode = self._debug_mode
    session.preferred_encoding = preferred_encoding
    session.preferred_time_zone = preferred_time_zone
    session.preferred_year = preferred_year

    return session

  def CreateStorageWriter(self, session, storage_file_path):
    """Creates a storage writer.

    Args:
      session (Session): session the storage changes are part of.
      storage_file_path (str): path of the storage file.

    Returns:
      StorageWriter: storage writer.
    """
    self._CheckStorageFile(storage_file_path)

    return storage_zip_file.ZIPStorageFileWriter(session, storage_file_path)

  def GetHashersInformation(self):
    """Retrieves the hashers information.

    Returns:
      list[tuple]: contains:

        str: hasher name
        str: hahser description
    """
    return hashers_manager.HashersManager.GetHashersInformation()

  def GetParserPluginsInformation(self, parser_filter_expression=None):
    """Retrieves the parser plugins information.

    Args:
      parser_filter_expression (str): parser filter expression, where None
          represents all parsers and plugins.

    Returns:
      list[tuple]: contains:

        str: parser plugin name
        str: parser plugin description
    """
    return parsers_manager.ParsersManager.GetParserPluginsInformation(
        parser_filter_expression=parser_filter_expression)

  def GetParserPresetsInformation(self):
    """Retrieves the parser presets information.

    Returns:
      list[tuple]: contains:

        str: parser preset name
        str: parsers names corresponding to the preset
    """
    parser_presets_information = []
    for preset_name, parser_names in sorted(parsers_presets.CATEGORIES.items()):
      parser_presets_information.append((preset_name, u', '.join(parser_names)))

    return parser_presets_information

  def GetParsersInformation(self):
    """Retrieves the parsers information.

    Returns:
      list[tuple]: contains:

        str: parser name
        str: parser description
    """
    return parsers_manager.ParsersManager.GetParsersInformation()

  def GetNamesOfParsersWithPlugins(self):
    """Retrieves the names of parser with plugins.

    Returns:
      list[str]: parser names.
    """
    return parsers_manager.ParsersManager.GetNamesOfParsersWithPlugins()

  def ProcessSources(
      self, session, storage_writer, source_path_specs, source_type,
      processing_configuration, enable_sigsegv_handler=False,
      force_preprocessing=False, number_of_extraction_workers=0,
      single_process_mode=False, status_update_callback=None,
      worker_memory_limit=None):
    """Processes the sources.

    Args:
      session (Session): session the storage changes are part of.
      storage_writer (StorageWriter): storage writer.
      source_path_specs (list[dfvfs.PathSpec]): path specifications of
          the sources to process.
      source_type (str): the dfVFS source type definition.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      force_preprocessing (Optional[bool]): True if preprocessing should be
          forced.
      number_of_extraction_workers (Optional[int]): number of extraction
          workers to run. If 0, the number will be selected automatically.
      single_process_mode (Optional[bool]): True if the front-end should
          run in single process mode.
      status_update_callback (Optional[function]): callback function for status
          updates.
      worker_memory_limit (Optional[int]): maximum amount of memory a worker is
          allowed to consume, where None represents 2 GiB.

    Returns:
      ProcessingStatus: processing status or None.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    if source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      # No need to multi process a single file source.
      single_process_mode = True

    engine = self._CreateEngine(single_process_mode)

    # If the source is a directory or a storage media image
    # run pre-processing.
    if force_preprocessing or source_type in self._SOURCE_TYPES_TO_PREPROCESS:
      self._PreprocessSources(engine, source_path_specs)

    if not processing_configuration.parser_filter_expression:
      operating_system = engine.knowledge_base.GetValue(
          u'operating_system')
      operating_system_product = engine.knowledge_base.GetValue(
          u'operating_system_product')
      operating_system_version = engine.knowledge_base.GetValue(
          u'operating_system_version')
      parser_filter_expression = self._GetParserFilterPreset(
          operating_system, operating_system_product, operating_system_version)

      if parser_filter_expression:
        logging.info(u'Parser filter expression changed to: {0:s}'.format(
            parser_filter_expression))

      processing_configuration.parser_filter_expression = (
          parser_filter_expression)
      session.enabled_parser_names = list(
          parsers_manager.ParsersManager.GetParserAndPluginNames(
              parser_filter_expression=(
                  processing_configuration.parser_filter_expression)))
      session.parser_filter_expression = (
          processing_configuration.parser_filter_expression)

    if session.preferred_time_zone:
      try:
        engine.knowledge_base.SetTimeZone(session.preferred_time_zone)
      except ValueError:
        logging.warning(
            u'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
                session.preferred_time_zone,
                engine.knowledge_base.time_zone.zone))

    filter_find_specs = None
    if processing_configuration.filter_file:
      environment_variables = engine.knowledge_base.GetEnvironmentVariables()
      filter_find_specs = utils.BuildFindSpecsFromFile(
          processing_configuration.filter_file,
          environment_variables=environment_variables)

    processing_status = None
    if single_process_mode:
      logging.debug(u'Starting extraction in single process mode.')

      processing_status = engine.ProcessSources(
          source_path_specs, storage_writer, self._resolver_context,
          processing_configuration, filter_find_specs=filter_find_specs,
          status_update_callback=status_update_callback)

    else:
      logging.debug(u'Starting extraction in multi process mode.')

      processing_status = engine.ProcessSources(
          session.identifier, source_path_specs, storage_writer,
          processing_configuration,
          enable_sigsegv_handler=enable_sigsegv_handler,
          filter_find_specs=filter_find_specs,
          number_of_worker_processes=number_of_extraction_workers,
          status_update_callback=status_update_callback,
          worker_memory_limit=worker_memory_limit)

    return processing_status

  def SetUseZeroMQ(self, use_zeromq=True):
    """Sets whether the frontend is using ZeroMQ for queueing or not.

    Args:
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing.
    """
    self._use_zeromq = use_zeromq
