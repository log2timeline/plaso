# -*- coding: utf-8 -*-
"""The event extraction worker."""

import logging
import os

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

try:
  from guppy import hpy
except ImportError:
  hpy = None

from plaso.engine import collector
from plaso.engine import queue
from plaso.lib import errors
from plaso.parsers import manager as parsers_manager


class BaseEventExtractionWorker(queue.ItemQueueConsumer):
  """Class that defines the event extraction worker base.

  This class is designed to watch a queue for path specifications of files
  and directories (file entries) for which events need to be extracted.

  The event extraction worker needs to determine if a parser suitable
  for parsing a particular file is available. All extracted event objects
  are pushed on a storage queue for further processing.
  """

  def __init__(
      self, identifier, process_queue, event_queue_producer,
      parse_error_queue_producer, parser_mediator, resolver_context=None):
    """Initializes the event extraction worker object.

    Args:
      identifier: The identifier, usually an incrementing integer.
      process_queue: The process queue (instance of Queue). This queue contains
                     the file entries that need to be processed.
      event_queue_producer: The event object queue producer (instance of
                            ItemQueueProducer).
      parse_error_queue_producer: The parse error queue producer (instance of
                                  ItemQueueProducer).
      parser_mediator: A parser mediator object (instance of ParserMediator).
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None.
    """
    super(BaseEventExtractionWorker, self).__init__(process_queue)
    self._enable_debug_output = False
    self._identifier = identifier
    self._open_files = False
    self._parser_mediator = parser_mediator
    self._filestat_parser_object = None
    self._parser_objects = None
    self._process_archive_files = False
    self._resolver_context = resolver_context

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

  def _ConsumeItem(self, path_spec):
    """Consumes an item callback for ConsumeItems.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).
    """
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

  def _DebugParseFileEntry(self):
    """Callback for debugging file entry parsing failures."""
    return

  def _ParseFileEntryWithParser(self, parser_object, file_entry):
    """Parses a file entry with a specific parser.

    Args:
      parser_object: A parser object (instance of BaseParser).
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Raises:
      QueueFull: If a queue is full.
    """
    # We need to reset the parser chain before each file, in case there's a
    # stale entry there due a bug in a parser.
    self._parser_mediator.ClearParserChain()
    self._parser_mediator.SetFileEntry(file_entry)
    try:
      parser_object.UpdateChainAndParse(self._parser_mediator)

    except errors.UnableToParseFile as exception:
      logging.debug(u'Not a {0:s} file ({1:s}) - {2:s}'.format(
          parser_object.NAME, file_entry.name, exception))

    except errors.QueueFull:
      raise

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

    finally:
      self._parser_mediator.SetFileEntry(None)

      if self._enable_debug_output:
        self._DebugParseFileEntry()

  def _ProcessArchiveFile(self, file_entry):
    """Processes an archive file (file that contains file entries).

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file is an archive file.
    """
    type_indicators = analyzer.Analyzer.GetArchiveTypeIndicators(
        file_entry.path_spec, resolver_context=self._resolver_context)

    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return False

    if number_of_type_indicators > 1:
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'archive file: {1:s}').format(
              type_indicators, file_entry.path_spec.comparable))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_TAR:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/',
            parent=file_entry.path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_ZIP:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_ZIP, location=u'/',
            parent=file_entry.path_spec)

      else:
        logging.debug((
            u'Unsupported archive format type indicator: {0:s} for '
            u'archive file: {1:s}').format(
                type_indicator, archive_path_spec.comparable))

        archive_path_spec = None

      if archive_path_spec and self._process_archive_files:
        try:
          file_system = path_spec_resolver.Resolver.OpenFileSystem(
              archive_path_spec, resolver_context=self._resolver_context)

          # TODO: change this to pass the archive file path spec to
          # the collector process and have the collector implement a maximum
          # path spec "depth" to prevent ZIP bombs and equiv.
          file_system_collector = collector.FileSystemCollector(self._queue)
          file_system_collector.Collect(file_system, archive_path_spec)

        except IOError:
          logging.warning(u'Unable to process archive file:\n{0:s}'.format(
              archive_path_spec.comparable))

    return True

  def _ProcessCompressedStreamFile(self, file_entry):
    """Processes an compressed stream file (file that contains file entries).

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file is a compressed stream file.
    """
    type_indicators = analyzer.Analyzer.GetCompressedStreamTypeIndicators(
        file_entry.path_spec, resolver_context=self._resolver_context)

    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return False

    if number_of_type_indicators > 1:
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'compressed stream file: {1:s}').format(
              type_indicators, file_entry.path_spec.comparable))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_BZIP2:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=dfvfs_definitions.COMPRESSION_METHOD_BZIP2,
            parent=file_entry.path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=file_entry.path_spec)

      else:
        logging.debug((
            u'Unsupported compressed stream format type indicators: {0:s} for '
            u'compressed stream file: {1:s}').format(
                type_indicator, compressed_stream_path_spec.comparable))

        compressed_stream_path_spec = None

      if compressed_stream_path_spec:
        self._queue.PushItem(compressed_stream_path_spec)

    return True

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
    """Returns a status dictionary."""
    return {
        'is_running': self._is_running,
        'identifier': u'Worker_{0:d}'.format(self._identifier),
        'current_file': self._current_working_file,
        'counter': self._parser_mediator.number_of_events}

  def InitializeParserObjects(self, parser_filter_string=None):
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

  def ParseFileEntry(self, file_entry):
    """Parses a file entry.

    Args:
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    logging.debug(u'[ParseFileEntry] Parsing: {0:s}'.format(
        file_entry.path_spec.comparable))

    self._current_working_file = getattr(
        file_entry.path_spec, u'location', file_entry.name)

    is_archive = False
    is_compressed_stream = False
    is_file = file_entry.IsFile()

    if is_file:
      is_compressed_stream = self._ProcessCompressedStreamFile(file_entry)
      if not is_compressed_stream:
        is_archive = self._ProcessArchiveFile(file_entry)

    if is_file and not is_archive and not is_compressed_stream:
      # TODO: Not go through all parsers, just the ones
      # that the classifier classifies the file as.
      for parser_object in self._parser_objects:
        logging.debug(u'Trying to parse: {0:s} with parser: {1:s}'.format(
            file_entry.name, parser_object.NAME))

        self._ParseFileEntryWithParser(parser_object, file_entry)

    elif self._filestat_parser_object:
      # TODO: for archive and compressed stream files is the desired behavior
      # to only apply the filestat parser?
      self._ParseFileEntryWithParser(self._filestat_parser_object, file_entry)

    logging.debug(u'[ParseFileEntry] Done parsing: {0:s}'.format(
        file_entry.path_spec.comparable))

    if self._enable_profiling:
      self._ProfilingUpdate()

  def Run(self):
    """Extracts event objects from file entries."""
    self._parser_mediator.ResetCounters()

    if self._enable_profiling:
      self._ProfilingStart()

    self._is_running = True

    logging.info(
        u'Worker {0:d} (PID: {1:d}) started monitoring process queue.'.format(
            self._identifier, os.getpid()))

    self.ConsumeItems()

    logging.info(
        u'Worker {0:d} (PID: {1:d}) stopped monitoring process queue.'.format(
            self._identifier, os.getpid()))

    self._current_working_file = u''

    self._is_running = False

    if self._enable_profiling:
      self._ProfilingStop()

    if self._resolver_context:
      self._resolver_context.Empty()

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
    self._parser_mediator.SetFilterObject(filter_object)

  def SetMountPath(self, mount_path):
    """Sets the mount path.

    Args:
      mount_path: string containing the mount path.
    """
    self._parser_mediator.SetMountPath(mount_path)

  def SetProcessArchiveFiles(self, process_archive_files):
    """Sets the process archive files mode.

    Args:
      process_archive_files: boolean value to indicate if the worker should
                             scan for file entries inside files.
    """
    self._process_archive_files = process_archive_files

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: string that contains the text to prepend to every
                    event object.
    """
    self._parser_mediator.SetTextPrepend(text_prepend)

  def SignalAbort(self):
    """Signals the worker to abort."""
    super(BaseEventExtractionWorker, self).SignalAbort()
    self._parser_mediator.SignalAbort()

  @classmethod
  def SupportsProfiling(cls):
    """Returns a boolean value to indicate if profiling is supported."""
    return hpy is not None
