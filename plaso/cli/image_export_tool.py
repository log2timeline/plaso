# -*- coding: utf-8 -*-
"""The image export CLI tool."""

import argparse
import logging
import os
import textwrap

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.analyzers.hashers import manager as hashers_manager
from plaso.cli import storage_media_tool
from plaso.cli.helpers import manager as helpers_manager
from plaso.engine import extractors
from plaso.engine import knowledge_base
from plaso.engine import path_helper
from plaso.filters import file_entry as file_entry_filters
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import specification
from plaso.preprocessors import manager as preprocess_manager


class ImageExportTool(storage_media_tool.StorageMediaTool):
  """Class that implements the image export CLI tool.

  Attributes:
    has_filters (bool): True if filters have been specified via the options.
    list_signature_identifiers (bool): True if information about the signature
        identifiers should be shown.
  """

  NAME = u'image_export'
  DESCRIPTION = (
      u'This is a simple collector designed to export files inside an '
      u'image, both within a regular RAW image as well as inside a VSS. '
      u'The tool uses a collection filter that uses the same syntax as a '
      u'targeted plaso filter.')

  EPILOG = u'And that is how you export files, plaso style.'

  _DIRTY_CHARACTERS = frozenset([
      u'\x00', u'\x01', u'\x02', u'\x03', u'\x04', u'\x05', u'\x06', u'\x07',
      u'\x08', u'\x09', u'\x0a', u'\x0b', u'\x0c', u'\x0d', u'\x0e', u'\x0f',
      u'\x10', u'\x11', u'\x12', u'\x13', u'\x14', u'\x15', u'\x16', u'\x17',
      u'\x18', u'\x19', u'\x1a', u'\x1b', u'\x1c', u'\x1d', u'\x1e', u'\x1f',
      os.path.sep, u'!', u'$', u'%', u'&', u'*', u'+', u':', u';', u'<', u'>',
      u'?', u'@', u'|', u'~', u'\x7f'])

  _COPY_BUFFER_SIZE = 32768

  _READ_BUFFER_SIZE = 4096

  # TODO: remove this redirect.
  _SOURCE_OPTION = u'image'

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
    self._artifacts_registry = None
    self._destination_path = None
    self._digests = {}
    self._filter_collection = file_entry_filters.FileEntryFilterCollection()
    self._filter_file = None
    self._knowledge_base = knowledge_base.KnowledgeBase()
    self._path_spec_extractor = extractors.PathSpecExtractor()
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
      return

    try:
      file_object.seek(0, os.SEEK_SET)

      hasher_object = hashers_manager.HashersManager.GetHasher(u'sha256')

      data = file_object.read(self._READ_BUFFER_SIZE)
      while data:
        hasher_object.Update(data)
        data = file_object.read(self._READ_BUFFER_SIZE)

    finally:
      file_object.close()

    return hasher_object.GetStringDigest()

  def _CreateSanitizedDestination(
      self, source_file_entry, source_path_spec, destination_path):
    """Creates a sanitized path of both destination directory and filename.

    This function replaces non-printable and other characters defined in
     _DIRTY_CHARACTERS with an underscore "_".

    Args:
      source_file_entry (dfvfs.FileEntry): file entry of the source file.
      source_path_spec (dfvfs.PathSpec): path specification of the source file.
      destination_path (str): path of the destination directory.

    Returns:
      tuple[str, str]: sanitized paths of both destination directory and
          filename.
    """
    file_system = source_file_entry.GetFileSystem()
    path = getattr(source_path_spec, u'location', None)
    path_segments = file_system.SplitPath(path)

    # Sanitize each path segment.
    for index, path_segment in enumerate(path_segments):
      path_segments[index] = u''.join([
          character if character not in self._DIRTY_CHARACTERS else u'_'
          for character in path_segment])

    return (
        os.path.join(destination_path, *path_segments[:-1]), path_segments[-1])

  # TODO: merge with collector and/or engine.
  def _Extract(
      self, source_path_specs, destination_path, output_writer,
      skip_duplicates=True):
    """Extracts files.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications to extract.
      destination_path (str): path where the extracted files should be stored.
      output_writer (CLIOutputWriter): output writer.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.
    """
    output_writer.Write(u'Extracting file entries.\n')
    path_spec_generator = self._path_spec_extractor.ExtractPathSpecs(
        source_path_specs, resolver_context=self._resolver_context)

    for path_spec in path_spec_generator:
      self._ExtractFileEntry(
          path_spec, destination_path, output_writer,
          skip_duplicates=skip_duplicates)

  def _ExtractDataStream(
      self, file_entry, data_stream_name, destination_path, output_writer,
      skip_duplicates=True):
    """Extracts a data stream.

    Args:
      file_entry (dfvfs.FileEntry): file entry containing the data stream.
      data_stream_name (str): name of the data stream.
      destination_path (str): path where the extracted files should be stored.
      output_writer (CLIOutputWriter): output writer.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.
    """
    if not data_stream_name and not file_entry.IsFile():
      return

    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        file_entry.path_spec)

    if skip_duplicates:
      try:
        digest = self._CalculateDigestHash(file_entry, data_stream_name)
      except (IOError, dfvfs_errors.BackEndError) as exception:
        output_writer.Write((
            u'[skipping] unable to read content of file entry: {0:s} '
            u'with error: {1:s}\n').format(display_name, exception))
        return

      if not digest:
        output_writer.Write(
            u'[skipping] unable to read content of file entry: {0:s}\n'.format(
                display_name))
        return

      duplicate_display_name = self._digests.get(digest, None)
      if duplicate_display_name:
        output_writer.Write((
            u'[skipping] file entry: {0:s} is a duplicate of: {1:s} with '
            u'digest: {2:s}\n').format(
                display_name, duplicate_display_name, digest))
        return

      self._digests[digest] = display_name

    target_directory, target_filename = self._CreateSanitizedDestination(
        file_entry, file_entry.path_spec, destination_path)

    parent_path_spec = getattr(file_entry.path_spec, u'parent', None)
    if parent_path_spec:
      vss_store_number = getattr(parent_path_spec, u'store_index', None)
      if vss_store_number is not None:
        target_filename = u'vss{0:d}_{1:s}'.format(
            vss_store_number + 1, target_filename)

    if data_stream_name:
      target_filename = u'{0:s}_{1:s}'.format(target_filename, data_stream_name)

    if not target_directory:
      target_directory = destination_path

    elif not os.path.isdir(target_directory):
      os.makedirs(target_directory)

    target_path = os.path.join(target_directory, target_filename)

    if os.path.exists(target_path):
      output_writer.Write((
          u'[skipping] unable to export contents of file entry: {0:s} '
          u'because exported file: {1:s} already exists.\n').format(
              display_name, target_path))
      return

    try:
      self._WriteFileEntry(file_entry, data_stream_name, target_path)
    except (IOError, dfvfs_errors.BackEndError) as exception:
      output_writer.Write((
          u'[skipping] unable to export contents of file entry: {0:s} '
          u'with error: {1:s}\n').format(display_name, exception))

      try:
        os.remove(target_path)
      except (IOError, OSError):
        pass

  def _ExtractFileEntry(
      self, path_spec, destination_path, output_writer, skip_duplicates=True):
    """Extracts a file entry.

    Args:
      path_spec (dfvfs.PathSpec): path specification of the source file.
      destination_path (str): path where the extracted files should be stored.
      output_writer (CLIOutputWriter): output writer.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.
    """
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    if not self._filter_collection.Matches(file_entry):
      return

    file_entry_processed = False
    for data_stream in file_entry.data_streams:
      if self._abort:
        break

      self._ExtractDataStream(
          file_entry, data_stream.name, destination_path, output_writer,
          skip_duplicates=skip_duplicates)

      file_entry_processed = True

    if not file_entry_processed:
      self._ExtractDataStream(
          file_entry, u'', destination_path, output_writer,
          skip_duplicates=skip_duplicates)

  # TODO: merge with collector and/or engine.
  def _ExtractWithFilter(
      self, source_path_specs, destination_path, output_writer,
      filter_file_path, skip_duplicates=True):
    """Extracts files using a filter expression.

    This method runs the file extraction process on the image and
    potentially on every VSS if that is wanted.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications to extract.
      destination_path (str): path where the extracted files should be stored.
      output_writer (CLIOutputWriter): output writer.
      filter_file_path (str): path of the file that contains the filter
          expressions.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.
    """
    for source_path_spec in source_path_specs:
      file_system, mount_point = self._GetSourceFileSystem(
          source_path_spec, resolver_context=self._resolver_context)

      if self._knowledge_base is None:
        self._Preprocess(file_system, mount_point)

      display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
          source_path_spec)
      output_writer.Write(
          u'Extracting file entries from: {0:s}\n'.format(display_name))

      environment_variables = self._knowledge_base.GetEnvironmentVariables()
      find_specs = frontend_utils.BuildFindSpecsFromFile(
          filter_file_path, environment_variables=environment_variables)

      searcher = file_system_searcher.FileSystemSearcher(
          file_system, mount_point)
      for path_spec in searcher.Find(find_specs=find_specs):
        self._ExtractFileEntry(
            path_spec, destination_path, output_writer,
            skip_duplicates=skip_duplicates)

      file_system.Close()

  # TODO: refactor, this is a duplicate of the function in engine.
  def _GetSourceFileSystem(self, source_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    Args:
      source_path_spec (dfvfs.PathSpec): source path specification of the file
          system.
      resolver_context (dfvfs.Context): resolver context.

    Returns:
      tuple: contains:

        dfvfs.FileSystem: file system.
        dfvfs.PathSpec: mount point path specification that refers
            to the base location of the file system.

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not source_path_spec:
      raise RuntimeError(u'Missing source.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        source_path_spec, resolver_context=resolver_context)

    type_indicator = source_path_spec.type_indicator
    if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
      mount_point = source_path_spec
    else:
      mount_point = source_path_spec.parent

    return file_system, mount_point

  def _ParseExtensionsString(self, extensions_string):
    """Parses the extensions string.

    Args:
      extensions_string (str): comma separated extensions to filter.
    """
    if not extensions_string:
      return

    extensions_string = extensions_string.lower()
    extensions = [
        extension.strip() for extension in extensions_string.split(u',')]
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
    names = [name.strip() for name in names_string.split(u',')]
    file_entry_filter = file_entry_filters.NamesFileEntryFilter(names)
    self._filter_collection.AddFilter(file_entry_filter)

  def _ParseFilterOptions(self, options):
    """Parses the filter options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    names = [u'date_filters', u'filter_file']
    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=names)

    extensions_string = self.ParseStringOption(options, u'extensions_string')
    self._ParseExtensionsString(extensions_string)

    names_string = getattr(options, u'names_string', None)
    self._ParseNamesString(names_string)

    signature_identifiers = getattr(options, u'signature_identifiers', None)
    try:
      self._ParseSignatureIdentifiers(
          self._data_location, signature_identifiers)
    except (IOError, ValueError) as exception:
      raise errors.BadConfigOption(exception)

    if self._filter_file:
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
      ValueError: if no data location was specified.
    """
    if not signature_identifiers:
      return

    if not data_location:
      raise ValueError(u'Missing data location.')

    path = os.path.join(data_location, u'signatures.conf')
    if not os.path.exists(path):
      raise IOError(
          u'No such format specification file: {0:s}'.format(path))

    try:
      specification_store = self._ReadSpecificationFile(path)
    except IOError as exception:
      raise IOError((
          u'Unable to read format specification file: {0:s} with error: '
          u'{1:s}').format(path, exception))

    signature_identifiers = signature_identifiers.lower()
    signature_identifiers = [
        identifier.strip() for identifier in signature_identifiers.split(u',')]
    file_entry_filter = file_entry_filters.SignaturesFileEntryFilter(
        specification_store, signature_identifiers)
    self._filter_collection.AddFilter(file_entry_filter)

  def _Preprocess(self, file_system, mount_point):
    """Preprocesses the image.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
    """
    logging.debug(u'Starting preprocessing.')

    try:
      preprocess_manager.PreprocessPluginsManager.RunPlugins(
          self._artifacts_registry, file_system, mount_point,
          self._knowledge_base)

    except IOError as exception:
      logging.error(u'Unable to preprocess with error: {0:s}'.format(exception))

    logging.debug(u'Preprocessing done.')

  def _ReadSpecificationFile(self, path):
    """Reads the format specification file.

    Args:
      path (str): path of the format specification file.

    Returns:
      FormatSpecificationStore: format specification store.
    """
    specification_store = specification.FormatSpecificationStore()

    with open(path, 'rb') as file_object:
      for line in file_object.readlines():
        line = line.strip()
        if not line or line.startswith(b'#'):
          continue

        try:
          identifier, offset, pattern = line.split()
        except ValueError:
          logging.error(u'[skipping] invalid line: {0:s}'.format(
              line.decode(u'utf-8')))
          continue

        try:
          offset = int(offset, 10)
        except ValueError:
          logging.error(u'[skipping] invalid offset in line: {0:s}'.format(
              line.decode(u'utf-8')))
          continue

        try:
          pattern = pattern.decode(u'string_escape')
        # ValueError is raised e.g. when the patterns contains "\xg1".
        except ValueError:
          logging.error(
              u'[skipping] invalid pattern in line: {0:s}'.format(
                  line.decode(u'utf-8')))
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

    try:
      with open(destination_file, 'wb') as destination_file_object:
        source_file_object.seek(0, os.SEEK_SET)

        data = source_file_object.read(self._COPY_BUFFER_SIZE)
        while data:
          destination_file_object.write(data)
          data = source_file_object.read(self._COPY_BUFFER_SIZE)

    finally:
      source_file_object.close()

  def AddFilterOptions(self, argument_group):
    """Adds the filter options to the argument group.

    Args:
      argument_group (argparse._ArgumentGroup): argparse argument group.
    """
    names = [u'date_filters', u'filter_file']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_group, names=names)

    argument_group.add_argument(
        u'-x', u'--extensions', dest=u'extensions_string', action=u'store',
        type=str, metavar=u'EXTENSIONS', help=(
            u'Filter on file name extensions. This option accepts multiple '
            u'multiple comma separated values e.g. "csv,docx,pst".'))

    argument_group.add_argument(
        u'--names', dest=u'names_string', action=u'store',
        type=str, metavar=u'NAMES', help=(
            u'Filter on file names.  This option accepts a comma separated '
            u'string denoting all file names, e.g. -x '
            u'"NTUSER.DAT,UsrClass.dat".'))

    argument_group.add_argument(
        u'--signatures', dest=u'signature_identifiers', action=u'store',
        type=str, metavar=u'IDENTIFIERS', help=(
            u'Filter on file format signature identifiers. This option '
            u'accepts multiple comma separated values e.g. "esedb,lnk". '
            u'Use "list" to show an overview of the supported file format '
            u'signatures.'))

  def ListSignatureIdentifiers(self):
    """Lists the signature identifier.

    Raises:
      BadConfigOption: if the data location is invalid.
    """
    if not self._data_location:
      raise errors.BadConfigOption(u'Missing data location.')

    path = os.path.join(self._data_location, u'signatures.conf')
    if not os.path.exists(path):
      raise errors.BadConfigOption(
          u'No such format specification file: {0:s}'.format(path))

    try:
      specification_store = self._ReadSpecificationFile(path)
    except IOError as exception:
      raise errors.BadConfigOption((
          u'Unable to read format specification file: {0:s} with error: '
          u'{1:s}').format(path, exception))

    identifiers = []
    for format_specification in specification_store.specifications:
      identifiers.append(format_specification.identifier)

    self._output_writer.Write(u'Available signature identifiers:\n')
    self._output_writer.Write(
        u'\n'.join(textwrap.wrap(u', '.join(sorted(identifiers)), 79)))
    self._output_writer.Write(u'\n\n')

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddInformationalOptions(argument_parser)

    names = [u'artifact_definitions', u'data_location']
    helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
        argument_parser, names=names)

    self.AddLogFileOptions(argument_parser)

    self.AddStorageMediaImageOptions(argument_parser)
    self.AddVSSProcessingOptions(argument_parser)

    self.AddFilterOptions(argument_parser)

    argument_parser.add_argument(
        u'-w', u'--write', action=u'store', dest=u'path', type=str,
        metavar=u'PATH', default=u'export', help=(
            u'The directory in which extracted files should be stored.'))

    argument_parser.add_argument(
        u'--include_duplicates', dest=u'include_duplicates',
        action=u'store_true', default=False, help=(
            u'If extraction from VSS is enabled, by default a digest hash '
            u'is calculated for each file. These hashes are compared to the '
            u'previously exported files and duplicates are skipped. Use '
            u'this option to include duplicate files in the export.'))

    argument_parser.add_argument(
        self._SOURCE_OPTION, nargs='?', action=u'store', metavar=u'IMAGE',
        default=None, type=str, help=(
            u'The full path to the image file that we are about to extract '
            u'files from, it should be a raw image or another image that '
            u'plaso supports.'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write(u'ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write(u'')
      self._output_writer.Write(argument_parser.format_usage())
      return False

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
        options, self, names=[u'data_location'])

    # Check the list options first otherwise required options will raise.
    signature_identifiers = self.ParseStringOption(
        options, u'signature_identifiers')
    if signature_identifiers == u'list':
      self.list_signature_identifiers = True

    if self.list_signature_identifiers:
      return

    self._ParseInformationalOptions(options)
    self._ParseLogFileOptions(options)

    self._ParseStorageMediaOptions(options)

    format_string = (
        u'%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
        u'<%(module)s> %(message)s')

    if self._debug_mode:
      logging_level = logging.DEBUG
    elif self._quiet_mode:
      logging_level = logging.WARNING
    else:
      logging_level = logging.INFO

    self._ConfigureLogging(
        filename=self._log_file, format_string=format_string,
        log_level=logging_level)

    self._destination_path = self.ParseStringOption(
        options, u'path', default_value=u'export')

    if not self._data_location:
      logging.warning(u'Unable to automatically determine data location.')

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=[u'artifact_definitions'])

    self._ParseFilterOptions(options)

    if (getattr(options, u'no_vss', False) or
        getattr(options, u'include_duplicates', False)):
      self._skip_duplicates = False

  def PrintFilterCollection(self):
    """Prints the filter collection."""
    self._filter_collection.Print(self._output_writer)

  def ProcessSources(self):
    """Processes the sources.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    self.ScanSource()

    self._output_writer.Write(u'Export started.\n')

    if not os.path.isdir(self._destination_path):
      os.makedirs(self._destination_path)

    if self._filter_file:
      self._ExtractWithFilter(
          self._source_path_specs, self._destination_path, self._output_writer,
          self._filter_file, skip_duplicates=self._skip_duplicates)
    else:
      self._Extract(
          self._source_path_specs, self._destination_path, self._output_writer,
          skip_duplicates=self._skip_duplicates)

    self._output_writer.Write(u'Export completed.\n')
    self._output_writer.Write(u'\n')
