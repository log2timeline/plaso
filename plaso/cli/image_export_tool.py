# -*- coding: utf-8 -*-
"""The image export CLI tool."""

import argparse
import codecs
import collections
import io
import json
import os
import textwrap

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.analyzers.hashers import manager as hashers_manager
from plaso.cli import logger
from plaso.cli import storage_media_tool
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import engine
from plaso.engine import extractors
from plaso.engine import path_helper
from plaso.filters import file_entry as file_entry_filters
from plaso.lib import errors
from plaso.lib import loggers
from plaso.lib import specification
from plaso.storage.fake import writer as fake_writer


class ImageExportTool(storage_media_tool.StorageMediaTool):
  """Class that implements the image export CLI tool.

  Attributes:
    has_filters (bool): True if filters have been specified via the options.
    list_signature_identifiers (bool): True if information about the signature
        identifiers should be shown.
  """

  NAME = 'image_export'
  DESCRIPTION = (
      'This is a simple collector designed to export files inside an '
      'image, both within a regular RAW image as well as inside a VSS. '
      'The tool uses a collection filter that uses the same syntax as a '
      'targeted plaso filter.')

  EPILOG = 'And that is how you export files, plaso style.'

  _COPY_BUFFER_SIZE = 32768

  _DIRTY_CHARACTERS = frozenset([
      '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
      '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f',
      '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17',
      '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f',
      os.path.sep, '!', '$', '%', '&', '*', '+', ':', ';', '<', '>',
      '?', '@', '|', '~', '\x7f'])

  _HASHES_FILENAME = 'hashes.json'

  _READ_BUFFER_SIZE = 4096

  # TODO: remove this redirect.
  _SOURCE_OPTION = 'image'

  _SOURCE_TYPES_TO_PREPROCESS = frozenset([
      dfvfs_definitions.SOURCE_TYPE_DIRECTORY,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
      dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE])

  _SPECIFICATION_FILE_ENCODING = 'utf-8'

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(ImageExportTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._abort = False
    self._artifact_definitions_path = None
    self._artifact_filters = None
    self._artifacts_registry = None
    self._custom_artifacts_path = None
    self._destination_path = None
    self._digests = {}
    self._filter_collection = file_entry_filters.FileEntryFilterCollection()
    self._filter_file = None
    self._no_hashes = False
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._process_memory_limit = None
    self._paths_by_hash = collections.defaultdict(list)
    self._resolver_context = context.Context()
    self._skip_duplicates = True

    self.has_filters = False
    self.list_signature_identifiers = False

  def _CalculateDigestHash(self, file_entry, data_stream_name):
    """Calculates a SHA-256 digest of the contents of the file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry whose content will be hashed.
      data_stream_name (str): name of the data stream whose content is to be
          hashed.

    Returns:
      str: hexadecimal representation of the SHA-256 hash or None if the digest
          cannot be determined.
    """
    file_object = file_entry.GetFileObject(data_stream_name=data_stream_name)
    if not file_object:
      return None

    file_object.seek(0, os.SEEK_SET)

    hasher_object = hashers_manager.HashersManager.GetHasher('sha256')

    data = file_object.read(self._READ_BUFFER_SIZE)
    while data:
      hasher_object.Update(data)
      data = file_object.read(self._READ_BUFFER_SIZE)

    return hasher_object.GetStringDigest()

  def _CreateSanitizedDestination(
      self, source_file_entry, file_system_path_spec, source_data_stream_name,
      destination_path):
    """Creates a sanitized path of both destination directory and filename.

    This function replaces non-printable and other characters defined in
     _DIRTY_CHARACTERS with an underscore "_".

    Args:
      source_file_entry (dfvfs.FileEntry): file entry of the source file.
      file_system_path_spec (dfvfs.PathSpec): path specifications of the source
          file system to process.
      source_data_stream_name (str): name of the data stream of the source file
          entry.
      destination_path (str): path of the destination directory.

    Returns:
      tuple[str, str]: sanitized paths of both destination directory and
          filename.
    """
    file_system = source_file_entry.GetFileSystem()
    path = getattr(file_system_path_spec, 'location', None)
    path_segments = file_system.SplitPath(path)

    # Sanitize each path segment.
    for index, path_segment in enumerate(path_segments):
      path_segments[index] = ''.join([
          character if character not in self._DIRTY_CHARACTERS else '_'
          for character in path_segment])

    target_filename = path_segments.pop()

    parent_path_spec = getattr(source_file_entry.path_spec, 'parent', None)

    while parent_path_spec:
      if parent_path_spec.type_indicator in (
          dfvfs_definitions.FILE_SYSTEM_TYPE_INDICATORS):
        path_segments.insert(0, parent_path_spec.location[1:])
        break

      if parent_path_spec.type_indicator == (
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW):
        path_segments.insert(0, parent_path_spec.location[1:])

      parent_path_spec = getattr(parent_path_spec, 'parent', None)

    target_directory = os.path.join(destination_path, *path_segments)

    if source_data_stream_name:
      target_filename = '{0:s}_{1:s}'.format(
          target_filename, source_data_stream_name)

    return target_directory, target_filename

  def _ExtractDataStream(
      self, file_entry, data_stream_name, destination_path,
      skip_duplicates=True):
    """Extracts a data stream.

    Args:
      file_entry (dfvfs.FileEntry): file entry containing the data stream.
      data_stream_name (str): name of the data stream.
      destination_path (str): path where the extracted files should be stored.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.
    """
    if not data_stream_name and not file_entry.IsFile():
      return

    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        file_entry.path_spec)

    try:
      digest = self._CalculateDigestHash(file_entry, data_stream_name)
    except (IOError, dfvfs_errors.BackEndError) as exception:
      logger.error((
          '[skipping] unable to read content of file entry: {0:s} '
          'with error: {1!s}').format(display_name, exception))
      return

    if not digest:
      logger.error(
          '[skipping] unable to read content of file entry: {0:s}'.format(
              display_name))
      return

    target_directory, target_filename = self._CreateSanitizedDestination(
        file_entry, file_entry.path_spec, data_stream_name, destination_path)

    # If does not exist, append path separator to have consistent behaviour.
    if not destination_path.endswith(os.path.sep):
      destination_path = destination_path + os.path.sep

    target_path = os.path.join(target_directory, target_filename)
    if target_path.startswith(destination_path):
      path = target_path[len(destination_path):]

    self._paths_by_hash[digest].append(path)

    if skip_duplicates:
      duplicate_display_name = self._digests.get(digest, None)
      if duplicate_display_name:
        logger.warning((
            '[skipping] file entry: {0:s} is a duplicate of: {1:s} with '
            'digest: {2:s}').format(
                display_name, duplicate_display_name, digest))
        return

      self._digests[digest] = display_name

    if not os.path.isdir(target_directory):
      os.makedirs(target_directory)

    if os.path.exists(target_path):
      logger.warning((
          '[skipping] unable to export contents of file entry: {0:s} '
          'because exported file: {1:s} already exists.').format(
              display_name, target_path))
      return

    try:
      self._WriteFileEntry(file_entry, data_stream_name, target_path)
    except (IOError, dfvfs_errors.BackEndError) as exception:
      logger.error((
          '[skipping] unable to export contents of file entry: {0:s} '
          'with error: {1!s}').format(display_name, exception))

      try:
        os.remove(target_path)
      except (IOError, OSError):
        pass

  def _ExtractFileEntry(
      self, file_entry, destination_path, skip_duplicates=True):
    """Extracts a file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry whose content is to be written.
      destination_path (str): path where the extracted files should be stored.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.
    """
    if not self._filter_collection.Matches(file_entry):
      return

    file_entry_processed = False
    for data_stream in file_entry.data_streams:
      if self._abort:
        break
      self._ExtractDataStream(
          file_entry, data_stream.name, destination_path,
          skip_duplicates=skip_duplicates)

      file_entry_processed = True

    if not file_entry_processed:
      self._ExtractDataStream(
          file_entry, '', destination_path, skip_duplicates=skip_duplicates)

  # TODO: merge with collector and/or engine.
  def _Extract(
      self, file_system_path_specs, destination_path, output_writer,
      artifact_filters, filter_file, artifact_definitions_path,
      custom_artifacts_path, skip_duplicates=True):
    """Extracts files.

    This method runs the file extraction process on the image and
    potentially on every VSS if that is wanted.

    Args:
      file_system_path_specs (list[dfvfs.PathSpec]): path specifications of
          the source file systems to process.
      destination_path (str): path where the extracted files should be stored.
      output_writer (CLIOutputWriter): output writer.
      artifact_definitions_path (str): path to artifact definitions file.
      custom_artifacts_path (str): path to custom artifact definitions file.
      artifact_filters (list[str]): names of artifact definitions that are
          used for filtering file system and Windows Registry key paths.
      filter_file (str): path of the file that contains the filter file path
          filters.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.

    Raises:
      BadConfigOption: if an invalid collection filter was specified.
    """
    extraction_engine = engine.BaseEngine()

    extraction_engine.BuildArtifactsRegistry(
        artifact_definitions_path, custom_artifacts_path)

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    # If the source is a directory or a storage media image run pre-processing.

    system_configurations = []
    if self._source_type in self._SOURCE_TYPES_TO_PREPROCESS:
      try:
        logger.debug('Starting preprocessing.')

        # Setting storage writer to None here since we do not want to store
        # preprocessing information.
        system_configurations = extraction_engine.PreprocessSource(
            self._file_system_path_specs, storage_writer,
            resolver_context=self._resolver_context)

        logger.debug('Preprocessing done.')

      except IOError as exception:
        logger.error('Unable to preprocess with error: {0!s}'.format(exception))

    # TODO: use system_configurations instead of knowledge base
    _ = system_configurations

    environment_variables = (
        extraction_engine.knowledge_base.GetEnvironmentVariables())
    user_accounts = list(storage_writer.GetAttributeContainers('user_account'))

    try:
      extraction_engine.BuildCollectionFilters(
          environment_variables, user_accounts,
          artifact_filter_names=artifact_filters,
          filter_file_path=filter_file)
    except errors.InvalidFilter as exception:
      raise errors.BadConfigOption(
          'Unable to build collection filters with error: {0!s}'.format(
              exception))

    excluded_find_specs = extraction_engine.GetCollectionExcludedFindSpecs()
    included_find_specs = extraction_engine.GetCollectionIncludedFindSpecs()

    output_writer.Write('Extracting file entries.\n')

    for file_system_path_spec in file_system_path_specs:
      path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
          file_system_path_spec, find_specs=included_find_specs,
          resolver_context=self._resolver_context)

      for path_spec in path_spec_generator:
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(
            path_spec, resolver_context=self._resolver_context)

        if not file_entry:
          path_spec_string = self._GetPathSpecificationString(path_spec)
          logger.warning(
              'Unable to open file entry for path specfication: {0:s}'.format(
                  path_spec_string))
          continue

        skip_file_entry = False
        for find_spec in excluded_find_specs or []:
          skip_file_entry = find_spec.CompareLocation(file_entry)
          if skip_file_entry:
            break

        if skip_file_entry:
          logger.info('Skipped: {0:s} because of exclusion filter.'.format(
              file_entry.path_spec.location))
          continue

        self._ExtractFileEntry(
            file_entry, destination_path, skip_duplicates=skip_duplicates)

  def _ParseExtensionsString(self, extensions_string):
    """Parses the extensions string.

    Args:
      extensions_string (str): comma separated extensions to filter.
    """
    if not extensions_string:
      return

    extensions_string = extensions_string.lower()
    extensions = [
        extension.strip() for extension in extensions_string.split(',')]
    file_entry_filter = file_entry_filters.ExtensionsFileEntryFilter(extensions)
    self._filter_collection.AddFilter(file_entry_filter)

  def _ParseNamesString(self, names_string):
    """Parses the name string.

    Args:
      names_string (str): comma separated filenames to filter.
    """
    if not names_string:
      return

    names_string = names_string.lower()
    names = [name.strip() for name in names_string.split(',')]
    file_entry_filter = file_entry_filters.NamesFileEntryFilter(names)
    self._filter_collection.AddFilter(file_entry_filter)

  def _ParseFilterOptions(self, options):
    """Parses the filter options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    names = ['artifact_filters', 'date_filters', 'filter_file']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=names)

    extensions_string = self.ParseStringOption(options, 'extensions_string')
    self._ParseExtensionsString(extensions_string)

    names_string = getattr(options, 'names_string', None)
    self._ParseNamesString(names_string)

    signature_identifiers = getattr(options, 'signature_identifiers', None)
    try:
      self._ParseSignatureIdentifiers(
          self._data_location, signature_identifiers)
    except (IOError, ValueError) as exception:
      raise errors.BadConfigOption(exception)

    if self._artifact_filters or self._filter_file:
      self.has_filters = True
    else:
      self.has_filters = self._filter_collection.HasFilters()

  def _ParseSignatureIdentifiers(self, data_location, signature_identifiers):
    """Parses the signature identifiers.

    Args:
      data_location (str): location of the format specification file, for
          example, "signatures.conf".
      signature_identifiers (str): comma separated signature identifiers.

    Raises:
      IOError: if the format specification file could not be read from
          the specified data location.
      OSError: if the format specification file could not be read from
          the specified data location.
      ValueError: if no data location was specified.
    """
    if not signature_identifiers:
      return

    if not data_location:
      raise ValueError('Missing data location.')

    path = os.path.join(data_location, 'signatures.conf')
    if not os.path.exists(path):
      raise IOError(
          'No such format specification file: {0:s}'.format(path))

    try:
      specification_store = self._ReadSpecificationFile(path)
    except IOError as exception:
      raise IOError((
          'Unable to read format specification file: {0:s} with error: '
          '{1!s}').format(path, exception))

    signature_identifiers = signature_identifiers.lower()
    signature_identifiers = [
        identifier.strip() for identifier in signature_identifiers.split(',')]
    file_entry_filter = file_entry_filters.SignaturesFileEntryFilter(
        specification_store, signature_identifiers)
    self._filter_collection.AddFilter(file_entry_filter)

  def _ReadSpecificationFile(self, path):
    """Reads the format specification file.

    Args:
      path (str): path of the format specification file.

    Returns:
      FormatSpecificationStore: format specification store.
    """
    specification_store = specification.FormatSpecificationStore()

    with io.open(
        path, 'rt', encoding=self._SPECIFICATION_FILE_ENCODING) as file_object:
      for line in file_object.readlines():
        line = line.strip()
        if not line or line.startswith('#'):
          continue

        try:
          identifier, offset, pattern = line.split()
        except ValueError:
          logger.error('[skipping] invalid line: {0:s}'.format(line))
          continue

        try:
          offset = int(offset, 10)
        except ValueError:
          logger.error('[skipping] invalid offset in line: {0:s}'.format(line))
          continue

        try:
          # TODO: find another way to do this that doesn't use an undocumented
          # API.
          pattern = codecs.escape_decode(pattern)[0]
        # ValueError is raised when the patterns contains invalid escaped
        # characters, such as "\xg1".
        except ValueError:
          logger.error(
              '[skipping] invalid pattern in line: {0:s}'.format(line))
          continue

        format_specification = specification.FormatSpecification(identifier)
        format_specification.AddNewSignature(pattern, offset=offset)
        specification_store.AddSpecification(format_specification)

    return specification_store

  def _WriteFileEntry(self, file_entry, data_stream_name, destination_file):
    """Writes the contents of the source file entry to a destination file.

    Note that this function will overwrite an existing file.

    Args:
      file_entry (dfvfs.FileEntry): file entry whose content is to be written.
      data_stream_name (str): name of the data stream whose content is to be
          written.
      destination_file (str): path of the destination file.
    """
    source_file_object = file_entry.GetFileObject(
        data_stream_name=data_stream_name)
    if not source_file_object:
      return

    with open(destination_file, 'wb') as destination_file_object:
      source_file_object.seek(0, os.SEEK_SET)

      data = source_file_object.read(self._COPY_BUFFER_SIZE)
      while data:
        destination_file_object.write(data)
        data = source_file_object.read(self._COPY_BUFFER_SIZE)

  def AddFilterOptions(self, argument_group):
    """Adds the filter options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    names = ['artifact_filters', 'date_filters', 'filter_file']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=names)

    argument_group.add_argument(
        '-x', '--extensions', dest='extensions_string', action='store',
        type=str, metavar='EXTENSIONS', help=(
            'Filter on file name extensions. This option accepts multiple '
            'multiple comma separated values e.g. "csv,docx,pst".'))

    argument_group.add_argument(
        '--names', dest='names_string', action='store',
        type=str, metavar='NAMES', help=(
            'Filter on file names.  This option accepts a comma separated '
            'string denoting all file names, e.g. -x '
            '"NTUSER.DAT,UsrClass.dat".'))

    argument_group.add_argument(
        '--signatures', dest='signature_identifiers', action='store',
        type=str, metavar='IDENTIFIERS', help=(
            'Filter on file format signature identifiers. This option '
            'accepts multiple comma separated values e.g. "esedb,lnk". '
            'Use "list" to show an overview of the supported file format '
            'signatures.'))

  def ListSignatureIdentifiers(self):
    """Lists the signature identifier.

    Raises:
      BadConfigOption: if the data location is invalid.
    """
    if not self._data_location:
      raise errors.BadConfigOption('Missing data location.')

    path = os.path.join(self._data_location, 'signatures.conf')
    if not os.path.exists(path):
      raise errors.BadConfigOption(
          'No such format specification file: {0:s}'.format(path))

    try:
      specification_store = self._ReadSpecificationFile(path)
    except IOError as exception:
      raise errors.BadConfigOption((
          'Unable to read format specification file: {0:s} with error: '
          '{1!s}').format(path, exception))

    identifiers = []
    for format_specification in specification_store.specifications:
      identifiers.append(format_specification.identifier)

    self._output_writer.Write('Available signature identifiers:\n')
    self._output_writer.Write(
        '\n'.join(textwrap.wrap(', '.join(sorted(identifiers)), 79)))
    self._output_writer.Write('\n\n')

  def ParseArguments(self, arguments):
    """Parses the command line arguments.

    Args:
      arguments (list[str]): command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    loggers.ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddInformationalOptions(argument_parser)

    argument_helper_names = [
        'artifact_definitions', 'data_location', 'vfs_backend']
    if self._CanEnforceProcessMemoryLimit():
      argument_helper_names.append('process_resources')
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_parser, names=argument_helper_names)

    self.AddLogFileOptions(argument_parser)

    self.AddStorageMediaImageOptions(argument_parser)
    self.AddVSSProcessingOptions(argument_parser)
    self.AddCredentialOptions(argument_parser)

    self.AddFilterOptions(argument_parser)

    argument_parser.add_argument(
        '-w', '--write', action='store', dest='path', type=str,
        metavar='PATH', default='export', help=(
            'The directory in which extracted files should be stored.'))

    argument_parser.add_argument(
        '--include_duplicates', '--include-duplicates',
        dest='include_duplicates', action='store_true', default=False, help=(
            'By default a digest hash (SHA-256) is calculated for each file '
            '(data stream). These hashes are compared to the previously '
            'exported files and duplicates are skipped. Use this option to '
            'include duplicate files in the export.'))

    argument_parser.add_argument(
        '--no_hashes', '--no-hashes', dest='no_hashes', action='store_true',
        default=False, help=(
            'Do not generate the {0:s} file'.format(self._HASHES_FILENAME)))

    argument_parser.add_argument(
        self._SOURCE_OPTION, nargs='?', action='store', metavar='IMAGE',
        default=None, type=str, help=(
            'The full path to the image file that we are about to extract '
            'files from, it should be a raw image or another image that '
            'Plaso supports.'))

    try:
      options = argument_parser.parse_args(arguments)
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write('')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write('')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    self._WaitUserWarning()

    loggers.ConfigureLogging(
        debug_output=self._debug_mode, filename=self._log_file,
        quiet_mode=self._quiet_mode)

    return True

  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # The data location is required to list signatures.
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['data_location'])

    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)

    # Check the list options first otherwise required options will raise.
    signature_identifiers = self.ParseStringOption(
        options, 'signature_identifiers')
    if signature_identifiers == 'list':
      self.list_signature_identifiers = True

    if self.list_signature_identifiers or self.show_troubleshooting:
      return

    self._ParseInformationalOptions(options)
    self._ParseLogFileOptions(options)

    self._ParseStorageMediaOptions(options)

    self._destination_path = self.ParseStringOption(
        options, 'path', default_value='export')

    if not self._data_location:
      logger.warning('Unable to automatically determine data location.')

    argument_helper_names = [
        'artifact_definitions', 'process_resources', 'vfs_backend']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=argument_helper_names)

    if self._vfs_back_end == 'fsext':
      dfvfs_definitions.PREFERRED_EXT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_EXT)

    elif self._vfs_back_end == 'fsfat':
      dfvfs_definitions.PREFERRED_FAT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_FAT)

    elif self._vfs_back_end == 'fshfs':
      dfvfs_definitions.PREFERRED_HFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_HFS)

    elif self._vfs_back_end == 'fsntfs':
      dfvfs_definitions.PREFERRED_NTFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_NTFS)

    elif self._vfs_back_end == 'tsk':
      dfvfs_definitions.PREFERRED_EXT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)
      dfvfs_definitions.PREFERRED_FAT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)
      dfvfs_definitions.PREFERRED_GPT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION)
      dfvfs_definitions.PREFERRED_HFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)
      dfvfs_definitions.PREFERRED_NTFS_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_TSK)

    elif self._vfs_back_end == 'vsgpt':
      dfvfs_definitions.PREFERRED_GPT_BACK_END = (
          dfvfs_definitions.TYPE_INDICATOR_GPT)

    self._ParseFilterOptions(options)

    include_duplicates = getattr(options, 'include_duplicates', False)
    self._skip_duplicates = not include_duplicates

    self._no_hashes = getattr(options, 'no_hashes', False)

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

  def PrintFilterCollection(self):
    """Prints the filter collection."""
    self._filter_collection.Print(self._output_writer)

  def ProcessSource(self):
    """Processes the source.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    try:
      self.ScanSource(self._source_path)
    except dfvfs_errors.UserAbort as exception:
      raise errors.UserAbort(exception)

    self._output_writer.Write('Export started.\n')

    if not os.path.isdir(self._destination_path):
      os.makedirs(self._destination_path)

    self._Extract(
        self._file_system_path_specs, self._destination_path,
        self._output_writer, self._artifact_filters, self._filter_file,
        self._artifact_definitions_path, self._custom_artifacts_path,
        skip_duplicates=self._skip_duplicates)

    json_data = []

    if not self._no_hashes:
      hashes_file_path = os.path.join(
          self._destination_path, self._HASHES_FILENAME)
      with open(hashes_file_path, 'w', encoding='utf-8') as file_object:
        for sha256, paths in self._paths_by_hash.items():
          json_data.append({'sha256': sha256, 'paths': paths})
        json.dump(json_data, file_object)

    self._output_writer.Write('Export completed.\n')
    self._output_writer.Write('\n')
