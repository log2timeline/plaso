# -*- coding: utf-8 -*-
"""The extraction front-end."""

import logging

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context

from plaso import parsers   # pylint: disable=unused-import

from plaso.containers import sessions
from plaso.engine import single_process
from plaso.frontend import frontend
from plaso.frontend import utils
from plaso.multi_processing import task_engine as multi_process_engine
from plaso.parsers import manager as parsers_manager


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
    # TODO: remove after testing.
    self._experimental = False
    self._filter_expression = None
    self._filter_object = None
    self._mount_path = None
    self._profiling_directory = None
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._resolver_context = context.Context()
    self._text_prepend = None

  def _CreateEngine(self, single_process_mode, use_zeromq=True):
    """Creates an engine based on the front end settings.

    Args:
      single_process_mode (bool): True if the front-end should run in single
          process mode.
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing.

    Returns:
      BaseEngine: engine.
    """
    if single_process_mode:
      engine = single_process.SingleProcessEngine()
    else:
      engine = multi_process_engine.TaskMultiProcessEngine(
          use_zeromq=use_zeromq)

    return engine

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

  def ProcessSources(
      self, session, storage_writer, source_path_specs, source_type,
      processing_configuration, enable_sigsegv_handler=False,
      force_preprocessing=False, number_of_extraction_workers=0,
      single_process_mode=False, status_update_callback=None,
      use_zeromq=True, worker_memory_limit=None):
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
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing.
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

    engine = self._CreateEngine(single_process_mode, use_zeromq=use_zeromq)

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
      parser_filter_expression = (
          parsers_manager.ParsersManager.GetPresetForOperatingSystem(
              operating_system, operating_system_product,
              operating_system_version))

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
