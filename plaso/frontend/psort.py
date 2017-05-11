# -*- coding: utf-8 -*-
"""The psort front-end."""

from __future__ import print_function
import os

from plaso import formatters   # pylint: disable=unused-import
from plaso import output   # pylint: disable=unused-import

from plaso.analysis import manager as analysis_manager
from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import analysis_frontend
from plaso.lib import errors
from plaso.multi_processing import psort
from plaso.output import manager as output_manager
from plaso.output import mediator as output_mediator
from plaso.storage import zip_file as storage_zip_file


class PsortFrontend(analysis_frontend.AnalysisFrontend):
  """Class that implements the psort front-end."""

  _DEFAULT_PROFILING_SAMPLE_RATE = 1000

  def __init__(self):
    """Initializes the front-end object."""
    super(PsortFrontend, self).__init__()
    self._abort = False
    self._debug_mode = False
    # Instance of EventObjectFilter.
    self._event_filter = None
    self._event_filter_expression = None
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._preferred_language = u'en-US'
    self._profiling_directory = None
    self._profiling_sample_rate = self._DEFAULT_PROFILING_SAMPLE_RATE
    self._profiling_type = u'all'
    self._quiet_mode = False
    self._use_zeromq = True

  def _CheckStorageFile(self, storage_file_path):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path (str): path of the storage file.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if not os.path.isfile(storage_file_path):
      raise errors.BadConfigOption(
          u'Storage file: {0:s} is not a file.'.format(storage_file_path))

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = u'.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          u'Unable to write to storage file: {0:s}'.format(storage_file_path))

  def _CreateEngine(self):
    """Creates an engine based on the front end settings.

    Returns:
      BaseEngine: engine.
    """
    # TODO: add single processing support.
    return psort.PsortMultiProcessEngine(use_zeromq=self._use_zeromq)

  def AnalyzeEvents(
      self, storage_writer, analysis_plugins, processing_configuration,
      status_update_callback=None):
    """Analyzes events in a plaso storage.

    Args:
      storage_writer (StorageWriter): storage writer.
      analysis_plugins (list[AnalysisPlugin]): analysis plugins that should
          be run.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      status_update_callback (Optional[function]): callback function for status
          updates.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    engine = self._CreateEngine()

    # TODO: add single processing support.
    # TODO: pass configuration object.
    _ = processing_configuration

    engine.AnalyzeEvents(
        self._knowledge_base, storage_writer, self._data_location,
        analysis_plugins, event_filter=self._event_filter,
        event_filter_expression=self._event_filter_expression,
        status_update_callback=status_update_callback)

  def CreateOutputModule(
      self, output_format, preferred_encoding=u'utf-8', timezone=u'UTC'):
    """Create an output module.

    Args:
      output_format (str): output format.
      preferred_encoding (Optional[str]): preferred encoding to output.
      timezone (Optional[str]): timezone to use for timestamps in output.

    Returns:
      OutputModule: output module.

    Raises:
      RuntimeError: if a non-recoverable situation is encountered.
    """
    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._data_location)

    try:
      formatter_mediator.SetPreferredLanguageIdentifier(
          self._preferred_language)
    except (KeyError, TypeError) as exception:
      raise RuntimeError(exception)

    output_mediator_object = output_mediator.OutputMediator(
        self._knowledge_base, formatter_mediator,
        preferred_encoding=preferred_encoding)
    output_mediator_object.SetTimezone(timezone)

    try:
      output_module = output_manager.OutputManager.NewOutputModule(
          output_format, output_mediator_object)

    except IOError as exception:
      raise RuntimeError(
          u'Unable to create output module with error: {0:s}'.format(
              exception))

    if not output_module:
      raise RuntimeError(u'Missing output module.')

    return output_module

  def CreateSession(
      self, command_line_arguments=None, preferred_encoding=u'utf-8'):
    """Creates the session start information.

    Args:
      command_line_arguments (Optional[str]): the command line arguments.
      preferred_encoding (Optional[str]): preferred encoding.

    Returns:
      Session: session attribute container.
    """
    session = sessions.Session()

    session.command_line_arguments = command_line_arguments
    session.preferred_encoding = preferred_encoding

    return session

  def CreateStorageReader(self, storage_file_path):
    """Creates a storage reader.

    Args:
      storage_file_path (str): path of the storage file.

    Returns:
      StorageReader: storage reader.
    """
    return storage_zip_file.ZIPStorageFileReader(storage_file_path)

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

  def ExportEvents(
      self, storage_reader, output_module, processing_configuration,
      deduplicate_events=True, status_update_callback=None, time_slice=None,
      use_time_slicer=False):
    """Exports events using an output module.

    Args:
      storage_reader (StorageReader): storage reader.
      output_module (OutputModule): output module.
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      deduplicate_events (Optional[bool]): True if events should be
          deduplicated.
      status_update_callback (Optional[function]): callback function for status
          updates.
      time_slice (Optional[TimeSlice]): slice of time to output.
      use_time_slicer (Optional[bool]): True if the 'time slicer' should be
          used. The 'time slicer' will provide a context of events around
          an event of interest.

    Returns:
      collections.Counter: counter that tracks the number of events extracted
          from storage and the analysis plugin results.
    """
    engine = self._CreateEngine()

    # TODO: pass configuration object.
    _ = processing_configuration

    return engine.ExportEvents(
        self._knowledge_base, storage_reader, output_module,
        deduplicate_events=deduplicate_events, event_filter=self._event_filter,
        status_update_callback=status_update_callback, time_slice=time_slice,
        use_time_slicer=use_time_slicer)

  def GetAnalysisPluginInfo(self):
    """Retrieves information about the registered analysis plugins.

    Returns:
      list[tuple]: contains:

        str: name of analysis plugin.
        str: docstring of analysis plugin.
        type: type of analysis plugin.
    """
    return analysis_manager.AnalysisPluginManager.GetAllPluginInformation()

  def GetAnalysisPlugins(self, analysis_plugins_string):
    """Retrieves analysis plugins.

    Args:
      analysis_plugins_string (str): comma separated names of analysis plugins
          to enable.

    Returns:
      list[AnalysisPlugin]: analysis plugins.
    """
    if not analysis_plugins_string:
      return []

    analysis_plugins_list = [
        name.strip() for name in analysis_plugins_string.split(u',')]

    analysis_plugins = analysis_manager.AnalysisPluginManager.GetPluginObjects(
        analysis_plugins_list)
    return analysis_plugins.values()

  def GetDisabledOutputClasses(self):
    """Retrieves the disabled output classes.

    Returns:
      generator(tuple): contains:

        str: output class names
        type: output class types.
    """
    return output_manager.OutputManager.GetDisabledOutputClasses()

  def GetOutputClasses(self):
    """Retrieves the available output classes.

    Returns:
      generator(tuple): contains:

        str: output class names
        type: output class types.
    """
    return output_manager.OutputManager.GetOutputClasses()

  def HasOutputClass(self, name):
    """Determines if a specific output class is registered with the manager.

    Args:
      name (str): name of the output module.

    Returns:
      bool: True if the output class is registered.
    """
    return output_manager.OutputManager.HasOutputClass(name)

  def SetEventFilter(self, event_filter, event_filter_expression):
    """Sets the event filter information.

    Args:
      event_filter (FilterObject): event filter.
      event_filter_expression (str): event filter expression.
    """
    self._event_filter = event_filter
    self._event_filter_expression = event_filter_expression

  def SetPreferredLanguageIdentifier(self, language_identifier):
    """Sets the preferred language identifier.

    Args:
      language_identifier (str): language identifier string, for example
          'en-US' for US English or 'is-IS' for Icelandic.
    """
    self._preferred_language = language_identifier

  def SetQuietMode(self, quiet_mode=False):
    """Sets whether quiet mode should be enabled or not.

    Args:
      quiet_mode (Optional[bool]): True when quiet mode should be enabled.
    """
    self._quiet_mode = quiet_mode

  def SetUseZeroMQ(self, use_zeromq=True):
    """Sets whether ZeroMQ should be used for queueing or not.

    Args:
      use_zeromq (Optional[bool]): True if ZeroMQ should be used for queuing
          instead of Python's multiprocessing queue.
    """
    self._use_zeromq = use_zeromq
