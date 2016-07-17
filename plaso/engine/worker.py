# -*- coding: utf-8 -*-
"""The event extraction worker."""

import copy
import logging
import re

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import event_sources
from plaso.engine import extractors
from plaso.hashers import manager as hashers_manager
from plaso.lib import definitions
from plaso.lib import errors


class EventExtractionWorker(object):
  """Class that defines the event extraction worker base.

  This class is designed to watch a queue for path specifications of files
  and directories (file entries) and data streams for which events need to
  be extracted.

  The event extraction worker needs to determine if a parser suitable
  for parsing a particular file entry or data stream is available. All
  extracted event objects are pushed on a storage queue for further processing.

  Attributes:
    processing_status (str): human readable status indication e.g. 'Hashing',
        'Extracting'.
  """

  _DEFAULT_HASH_READ_SIZE = 4096

  # TSK metadata files that need special handling.
  _METADATA_FILE_LOCATIONS_TSK = frozenset([
      # NTFS
      u'/$AttrDef',
      u'/$BadClus',
      u'/$Bitmap',
      u'/$Boot',
      u'/$Extend/$ObjId',
      u'/$Extend/$Quota',
      u'/$Extend/$Reparse',
      u'/$Extend/$RmMetadata/$Repair',
      u'/$Extend/$RmMetadata/$TxfLog/$Tops',
      u'/$Extend/$UsnJrnl',
      u'/$LogFile',
      u'/$MFT',
      u'/$MFTMirr',
      u'/$Secure',
      u'/$UpCase',
      u'/$Volume',
      # HFS+/HFSX
      u'/$ExtentsFile',
      u'/$CatalogFile',
      u'/$BadBlockFile',
      u'/$AllocationFile',
      u'/$AttributesFile',
  ])

  # TODO: make this filtering solution more generic. Also see:
  # https://github.com/log2timeline/plaso/issues/467
  _CHROME_CACHE_DATA_FILE_RE = re.compile(r'^[fF]_[0-9a-fA-F]{6}$')
  _FIREFOX_CACHE_DATA_FILE_RE = re.compile(r'^[0-9a-fA-F]{5}[dm][0-9]{2}$')
  _FIREFOX_CACHE2_DATA_FILE_RE = re.compile(r'^[0-9a-fA-F]{40}$')
  _FSEVENTSD_FILE_RE = re.compile(r'^[0-9a-fA-F]{16}$')

  _TYPES_WITH_ROOT_METADATA = frozenset([
      dfvfs_definitions.TYPE_INDICATOR_GZIP])

  def __init__(
      self, resolver_context, parser_filter_expression=None,
      process_archive_files=False):
    """Initializes the event extraction worker object.

    Args:
      resolver_context (dfvfs.Context): resolver context.
      parser_filter_expression (Optional[str]): parser filter expression.
          None represents all parsers and plugins.

          The parser filter expression is a comma separated value string that
          denotes a list of parser names to include and/or exclude. Each entry
          can have the value of:

          * An exact match of a list of parsers, or a preset (see
            plaso/frontend/presets.py for a full list of available presets).
          * A name of a single parser (case insensitive), e.g. msiecf.
          * A glob name for a single parser, e.g. '*msie*' (case insensitive).

      process_archive_files (Optional[bool]): True if the worker should scan
          for file entries inside archive files.
    """
    super(EventExtractionWorker, self).__init__()
    self._abort = False
    self._event_extractor = extractors.EventExtractor(
        resolver_context, parser_filter_expression=parser_filter_expression)
    self._hasher_names = None
    self._process_archive_files = process_archive_files
    self._processing_profiler = None
    self._resolver_context = resolver_context

    self.processing_status = definitions.PROCESSING_STATUS_IDLE

  def _CanSkipContentExtraction(self, file_entry):
    """Determines if content extraction of a file entry can be skipped.

    Args:
      file_entry (dfvfs.FileEntry): file entry of which to determine content
          extraction can be skipped.

    Returns:
      bool: True if content extraction can be skipped.
    """
    # TODO: make this filtering solution more generic. Also see:
    # https://github.com/log2timeline/plaso/issues/467
    location = getattr(file_entry.path_spec, u'location', None)
    if not location:
      return False

    data_stream_name = getattr(file_entry.path_spec, u'data_stream', None)
    if data_stream_name:
      return False

    file_system = file_entry.GetFileSystem()

    path_segments = file_system.SplitPath(location)
    if not path_segments:
      return False

    if self._CHROME_CACHE_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-1]
      location_segments.append(u'index')
      location = file_system.JoinPath(location_segments)
      index_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(index_path_spec):
        # TODO: improve this check if "index" is a Chrome Cache index file.
        return True

    elif self._FIREFOX_CACHE_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-4]
      location_segments.append(u'_CACHE_MAP_')
      location = file_system.JoinPath(location_segments)
      cache_map_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(cache_map_path_spec):
        # TODO: improve this check if "_CACHE_MAP_" is a Firefox Cache
        # version 1 cache map file.
        return True

    elif self._FIREFOX_CACHE2_DATA_FILE_RE.match(path_segments[-1]):
      location_segments = path_segments[:-2]
      location_segments.append(u'index')
      location = file_system.JoinPath(location_segments)
      index_path_spec = path_spec_factory.Factory.NewPathSpec(
          file_entry.type_indicator, location=location,
          parent=file_entry.path_spec.parent)

      if file_system.FileEntryExistsByPathSpec(index_path_spec):
        # TODO: improve this check if "index" is a Firefox Cache version 2
        # index file.
        return True

    elif self._FSEVENTSD_FILE_RE.match(path_segments[-1]):
      if len(path_segments) == 2 and path_segments[0].lower() == u'.fseventsd':
        return True

    elif len(path_segments) == 1 and path_segments[0].lower() in (
        u'hiberfil.sys', u'pagefile.sys', u'swapfile.sys'):
      return True

    return False

  def _ExtractContentFromDataStream(
      self, parser_mediator, file_entry, data_stream_name):
    """Extracts content from a data stream.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to extract its content.
      data_stream_name (str): data stream name to extract its content.
    """
    self.processing_status = definitions.PROCESSING_STATUS_EXTRACTING

    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'extracting')

    self._event_extractor.ParseDataStream(
        parser_mediator, file_entry, data_stream_name=data_stream_name)

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'extracting')

    self.processing_status = definitions.PROCESSING_STATUS_RUNNING

  def _HashDataStream(self, parser_mediator, file_entry, data_stream_name):
    """Hashes the contents of a specific data stream of a file entry.

    The resulting digest hashes are set in the parser mediator as attributes
    that are added to produced event objects. Note that some file systems
    allow directories to have data streams, e.g. NTFS.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to be hashed.
      data_stream_name (str): data stream name to be hashed.

    Raises:
      RuntimeError: if the file-like object is missing.
    """
    if not self._hasher_names:
      return

    self.processing_status = definitions.PROCESSING_STATUS_HASHING

    display_name = parser_mediator.GetDisplayName()
    logging.debug(u'[HashDataStream] hashing file: {0:s}'.format(display_name))

    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'hashing')

    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
    if not file_object:
      raise RuntimeError(
          u'Unable to retrieve file-like object from file entry.')

    # Make sure frame.f_locals does not keep a reference to file_entry.
    file_entry = None

    try:
      digest_hashes = hashers_manager.HashersManager.HashFileObject(
          self._hasher_names, file_object,
          buffer_size=self._DEFAULT_HASH_READ_SIZE)
    finally:
      file_object.close()

    for hash_name, digest_hash_string in iter(digest_hashes.items()):
      attribute_name = u'{0:s}_hash'.format(hash_name)
      parser_mediator.AddEventAttribute(attribute_name, digest_hash_string)

      logging.debug(
          u'[HashDataStream] digest {0:s} calculated for file: {1:s}.'.format(
              digest_hash_string, display_name))

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'hashing')

    logging.debug(
        u'[HashDataStream] completed hashing file: {0:s}'.format(display_name))

    self.processing_status = definitions.PROCESSING_STATUS_RUNNING

  def _ExtractMetadataFromFileEntry(self, parser_mediator, file_entry):
    """Extracts metadata from a file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to extract metadata from.
    """
    self.processing_status = definitions.PROCESSING_STATUS_EXTRACTING

    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'extracting')

    self._event_extractor.ParseFileEntryMetadata(parser_mediator, file_entry)

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'extracting')

    self.processing_status = definitions.PROCESSING_STATUS_RUNNING

  def _GetArchiveTypes(self, parser_mediator, path_spec):
    """Determines if a data stream contains an archive e.g. TAR or ZIP.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification of the data stream.

    Returns:
      list[str]: dfVFS archive type indicators found in the data stream.
    """
    try:
      type_indicators = analyzer.Analyzer.GetArchiveTypeIndicators(
          path_spec, resolver_context=self._resolver_context)
    except IOError as exception:
      type_indicators = []

      error_message = (
          u'analyzer failed to determine archive type indicators '
          u'with error: {0:s}').format(exception)
      parser_mediator.ProduceExtractionError(error_message, path_spec=path_spec)

    return type_indicators

  def _GetCompressedStreamTypes(self, parser_mediator, path_spec):
    """Determines if a data stream contains a compressed stream e.g. gzip.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification of the data stream.

    Returns:
      list[str]: dfVFS compressed stream type indicators found in
          the data stream.
    """
    try:
      type_indicators = analyzer.Analyzer.GetCompressedStreamTypeIndicators(
          path_spec, resolver_context=self._resolver_context)
    except IOError as exception:
      type_indicators = []

      error_message = (
          u'analyzer failed to determine compressed stream type indicators '
          u'with error: {0:s}').format(exception)
      parser_mediator.ProduceExtractionError(error_message, path_spec=path_spec)

    return type_indicators

  def _IsMetadataFile(self, file_entry):
    """Determines if the file entry is a metadata file.

    Args:
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Returns:
      bool: True if the file entry is a metadata file.
    """
    if (file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK and
        file_entry.path_spec.location in self._METADATA_FILE_LOCATIONS_TSK):
      return True

    return False

  def _ProcessArchiveTypes(self, parser_mediator, path_spec, type_indicators):
    """Processes a data stream containing archive types e.g. TAR or ZIP.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
      type_indicators(list[str]): dfVFS archive type indicators found in
          the data stream.
    """
    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return

    self.processing_status = definitions.PROCESSING_STATUS_COLLECTING

    if number_of_type_indicators > 1:
      display_name = parser_mediator.GetDisplayName()
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'archive file: {1:s}').format(type_indicators, display_name))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_TAR:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/',
            parent=path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_ZIP:
        archive_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_ZIP, location=u'/',
            parent=path_spec)

      else:
        archive_path_spec = None

        error_message = (
            u'unsupported archive format type indicator: {0:s}').format(
                type_indicator)
        parser_mediator.ProduceExtractionError(
            error_message, path_spec=path_spec)

      if archive_path_spec:
        try:
          path_spec_extractor = extractors.PathSpecExtractor(
              self._resolver_context)

          for path_spec in path_spec_extractor.ExtractPathSpecs(
              [archive_path_spec]):
            if self._abort:
              break

            event_source = event_sources.FileEntryEventSource(
                path_spec=path_spec)
            event_source.file_entry_type = (
                dfvfs_definitions.FILE_ENTRY_TYPE_FILE)
            parser_mediator.ProduceEventSource(event_source)

        except (IOError, errors.MaximumRecursionDepth) as exception:
          error_message = (
              u'unable to process archive file with error: {0:s}').format(
                  exception)
          parser_mediator.ProduceExtractionError(
              error_message, path_spec=path_spec)

  def _ProcessCompressedStreamTypes(
      self, parser_mediator, path_spec, type_indicators):
    """Processes a data stream containing compressed stream types e.g. bz2.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
      type_indicators(list[str]): dfVFS archive type indicators found in
          the data stream.
    """
    number_of_type_indicators = len(type_indicators)
    if number_of_type_indicators == 0:
      return

    self.processing_status = definitions.PROCESSING_STATUS_COLLECTING

    if number_of_type_indicators > 1:
      display_name = parser_mediator.GetDisplayName()
      logging.debug((
          u'Found multiple format type indicators: {0:s} for '
          u'compressed stream file: {1:s}').format(
              type_indicators, display_name))

    for type_indicator in type_indicators:
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_BZIP2:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
            compression_method=dfvfs_definitions.COMPRESSION_METHOD_BZIP2,
            parent=path_spec)

      elif type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP:
        compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)

      else:
        compressed_stream_path_spec = None

        error_message = (
            u'unsupported compressed stream format type indicators: '
            u'{0:s}').format(type_indicator)
        parser_mediator.ProduceExtractionError(
            error_message, path_spec=path_spec)

      if compressed_stream_path_spec:
        event_source = event_sources.FileEntryEventSource(
            path_spec=compressed_stream_path_spec)
        event_source.file_entry_type = dfvfs_definitions.FILE_ENTRY_TYPE_FILE
        parser_mediator.ProduceEventSource(event_source)

  def _ProcessDirectory(self, parser_mediator, file_entry):
    """Processes a directory file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry of the directory.
    """
    self.processing_status = definitions.PROCESSING_STATUS_COLLECTING

    if self._processing_profiler:
      self._processing_profiler.StartTiming(u'collecting')

    for sub_file_entry in file_entry.sub_file_entries:
      if self._abort:
        break

      try:
        if not sub_file_entry.IsAllocated():
          continue

      except dfvfs_errors.BackEndError as exception:
        error_message = (
            u'unable to process directory entry: {0:s} with error: '
            u'{1:s}').format(sub_file_entry.name, exception)
        parser_mediator.ProduceExtractionError(
            error_message, path_spec=file_entry.path_spec)
        continue

      # For TSK-based file entries only, ignore the virtual /$OrphanFiles
      # directory.
      if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
        if file_entry.IsRoot() and sub_file_entry.name == u'$OrphanFiles':
          continue

      event_source = event_sources.FileEntryEventSource(
          path_spec=sub_file_entry.path_spec)

      # TODO: move this into a dfVFS file entry property.
      stat_object = sub_file_entry.GetStat()
      if stat_object:
        event_source.file_entry_type = stat_object.type

      parser_mediator.ProduceEventSource(event_source)

    if self._processing_profiler:
      self._processing_profiler.StopTiming(u'collecting')

    self.processing_status = definitions.PROCESSING_STATUS_RUNNING

  def _ProcessFileEntry(self, parser_mediator, file_entry):
    """Processes a file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry.
    """
    display_name = parser_mediator.GetDisplayName()
    logging.debug(
        u'[ProcessFileEntry] processing file entry: {0:s}'.format(display_name))

    reference_count = self._resolver_context.GetFileObjectReferenceCount(
        file_entry.path_spec)

    try:
      if self._IsMetadataFile(file_entry):
        self._ProcessMetadataFile(parser_mediator, file_entry)

      else:
        file_entry_processed = False
        for data_stream in file_entry.data_streams:
          if self._abort:
            break

          file_entry_processed = True
          self._ProcessFileEntryDataStream(
              parser_mediator, file_entry, data_stream.name)

        if not file_entry_processed:
          # For when the file entry does not contain a data stream.
          self._ProcessFileEntryDataStream(parser_mediator, file_entry, u'')

    finally:
      if reference_count != self._resolver_context.GetFileObjectReferenceCount(
          file_entry.path_spec):
        # Clean up after parsers that do not call close explicitly.
        if self._resolver_context.ForceRemoveFileObject(file_entry.path_spec):
          logging.warning(
              u'File-object not explicitly closed for file: {0:s}'.format(
                  display_name))

      # Make sure frame.f_locals does not keep a reference to file_entry.
      file_entry = None

    logging.debug(
        u'[ProcessFileEntry] done processing file entry: {0:s}'.format(
            display_name))

  def _ProcessFileEntryDataStream(
      self, parser_mediator, file_entry, data_stream_name):
    """Processes a specific data stream of a file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry containing the data stream.
      data_stream_name (str): data stream name.
    """
    # Not every file entry has a data stream. In such cases we want to
    # extract the metadata only.
    has_data_stream = file_entry.HasDataStream(data_stream_name)
    if has_data_stream:
      self._HashDataStream(parser_mediator, file_entry, data_stream_name)

    # We always want to extract the file entry metadata but we only want
    # to parse it once per file entry, so we only use it if we are
    # processing the default (nameless) data stream.
    if (not data_stream_name and (
        not file_entry.IsRoot() or
        file_entry.type_indicator in self._TYPES_WITH_ROOT_METADATA)):
      self._ExtractMetadataFromFileEntry(parser_mediator, file_entry)

    # Determine if the content of the file entry should not be extracted.
    skip_content_extraction = self._CanSkipContentExtraction(file_entry)
    if skip_content_extraction:
      display_name = parser_mediator.GetDisplayName()
      logging.info(
          u'Skipping content extraction of: {0:s}'.format(display_name))
      self.processing_status = definitions.PROCESSING_STATUS_IDLE
      return

    if (file_entry.IsLink() and not data_stream_name) or not has_data_stream:
      return

    path_spec = copy.deepcopy(file_entry.path_spec)
    if data_stream_name:
      path_spec.data_stream = data_stream_name

    archive_types = []
    compressed_stream_types = []

    compressed_stream_types = self._GetCompressedStreamTypes(
        parser_mediator, path_spec)

    if not compressed_stream_types:
      archive_types = self._GetArchiveTypes(parser_mediator, path_spec)

    if archive_types:
      if self._process_archive_files:
        self._ProcessArchiveTypes(parser_mediator, path_spec, archive_types)

      if dfvfs_definitions.TYPE_INDICATOR_ZIP in archive_types:
        self.processing_status = definitions.PROCESSING_STATUS_EXTRACTING

        # ZIP files are the base of certain file formats like docx.
        self._event_extractor.ParseDataStream(
            parser_mediator, file_entry, data_stream_name)

    elif compressed_stream_types:
      self._ProcessCompressedStreamTypes(
          parser_mediator, path_spec, compressed_stream_types)

    else:
      self.processing_status = definitions.PROCESSING_STATUS_EXTRACTING

      self._event_extractor.ParseDataStream(
          parser_mediator, file_entry, data_stream_name)

  def _ProcessMetadataFile(self, parser_mediator, file_entry):
    """Processes a metadata file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry of the metadata file.
    """
    self.processing_status = definitions.PROCESSING_STATUS_EXTRACTING

    self._event_extractor.ParseFileEntryMetadata(
        parser_mediator, file_entry)

    self._event_extractor.ParseMetadataFile(
        parser_mediator, file_entry, u'')

  def ProcessPathSpec(self, parser_mediator, path_spec):
    """Processes a path specification.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      path_spec (dfvfs.PathSpec): path specification.
    """
    self.processing_status = definitions.PROCESSING_STATUS_RUNNING

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        path_spec, resolver_context=self._resolver_context)

    if file_entry is None:
      display_name = parser_mediator.GetDisplayNameFromPathSpec(path_spec)
      logging.warning(
          u'Unable to open file entry with path spec: {0:s}'.format(
              display_name))
      self.processing_status = definitions.PROCESSING_STATUS_IDLE
      return

    parser_mediator.SetFileEntry(file_entry)

    try:
      if file_entry.IsDirectory():
        self._ProcessDirectory(parser_mediator, file_entry)
      self._ProcessFileEntry(parser_mediator, file_entry)

    finally:
      parser_mediator.ResetFileEntry()

      # Make sure frame.f_locals does not keep a reference to file_entry.
      file_entry = None

      self.processing_status = definitions.PROCESSING_STATUS_IDLE

  def SetHashers(self, hasher_names_string):
    """Sets the hasher names.

    Args:
      hasher_names_string (str): comma separated names of the hashers
          to enable.
    """
    names = hashers_manager.HashersManager.GetHasherNamesFromString(
        hasher_names_string)
    logging.debug(u'[SetHashers] Enabling hashers: {0:s}.'.format(names))
    self._hasher_names = names

  def SetParsersProfiler(self, parsers_profiler):
    """Sets the parsers profiler.

    Args:
      parsers_profiler (ParsersProfiler): parsers profile.
    """
    self._event_extractor.SetParsersProfiler(parsers_profiler)

  def SetProcessingProfiler(self, processing_profiler):
    """Sets the parsers profiler.

    Args:
      processing_profiler (ProcessingProfiler): processing profile.
    """
    self._processing_profiler = processing_profiler

  def SignalAbort(self):
    """Signals the extraction worker to abort."""
    self._abort = True
