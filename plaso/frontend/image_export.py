# -*- coding: utf-8 -*-
"""The image export front-end."""

import abc
import collections
import logging
import os

import pysigscan

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.analyzers.hashers import manager as hashers_manager
from plaso.engine import extractors
from plaso.engine import knowledge_base
from plaso.engine import path_helper
from plaso.frontend import frontend
from plaso.frontend import utils
from plaso.lib import py2to3
from plaso.lib import specification
from plaso.lib import timelib
from plaso.preprocessors import manager as preprocess_manager


class FileEntryFilter(object):
  """Class that implements the file entry filter interface."""

  @abc.abstractmethod
  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """

  @abc.abstractmethod
  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """


class DateTimeFileEntryFilter(FileEntryFilter):
  """Class that implements date time-based file entry filter."""

  _DATE_TIME_RANGE_TUPLE = collections.namedtuple(
      u'date_time_range_tuple', u'time_value start_timestamp end_timestamp')

  _SUPPORTED_TIME_VALUES = frozenset([
      u'atime', u'bkup', u'ctime', u'crtime', u'dtime', u'mtime'])

  def __init__(self):
    """Initializes the date time-based file entry filter."""
    super(DateTimeFileEntryFilter, self).__init__()
    self._date_time_ranges = []

  def AddDateTimeRange(
      self, time_value, start_time_string=None, end_time_string=None):
    """Adds a date time filter range.

    The time strings are formatted as:
    YYYY-MM-DD hh:mm:ss.######[+-]##:##
    Where # are numeric digits ranging from 0 to 9 and the seconds
    fraction can be either 3 or 6 digits. The time of day, seconds fraction
    and timezone offset are optional. The default timezone is UTC.

    Args:
      time_value (str): time value, such as, atime, ctime, crtime, dtime, bkup
          and mtime.
      start_time_string (str): start date and time value string.
      end_time_string (str): end date and time value string.

    Raises:
      ValueError: If the filter is badly formed.
    """
    if not isinstance(time_value, py2to3.STRING_TYPES):
      raise ValueError(u'Filter type must be a string.')

    if start_time_string is None and end_time_string is None:
      raise ValueError(
          u'Filter must have either a start or an end date time value.')

    time_value_lower = time_value.lower()
    if time_value_lower not in self._SUPPORTED_TIME_VALUES:
      raise ValueError(
          u'Unsupported time value: {0:s}.'.format(time_value))

    if start_time_string:
      start_timestamp = timelib.Timestamp.CopyFromString(start_time_string)
    else:
      start_timestamp = None

    if end_time_string:
      end_timestamp = timelib.Timestamp.CopyFromString(end_time_string)
    else:
      end_timestamp = None

    # Make sure that the end timestamp occurs after the beginning.
    # If not then we need to reverse the time range.
    if (None not in [start_timestamp, end_timestamp] and
        start_timestamp > end_timestamp):
      raise ValueError(
          u'Invalid date time value start must be earlier than end.')

    self._date_time_ranges.append(self._DATE_TIME_RANGE_TUPLE(
        time_value_lower, start_timestamp, end_timestamp))

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """
    if not self._date_time_ranges:
      return

    stat_object = file_entry.GetStat()
    for date_time_range in self._date_time_ranges:
      time_value = date_time_range.time_value
      timestamp = getattr(stat_object, time_value, None)
      if timestamp is None:
        continue

      nano_time_value = u'{0:s}_nano'.format(time_value)
      nano_time_value = getattr(stat_object, nano_time_value, None)

      timestamp = timelib.Timestamp.FromPosixTime(timestamp)
      if nano_time_value is not None:
        # Note that the _nano values are in intervals of 100th nano seconds.
        nano_time_value, _ = divmod(nano_time_value, 10)
        timestamp += nano_time_value

      if (date_time_range.start_timestamp is not None and
          timestamp < date_time_range.start_timestamp):
        return False

      if (date_time_range.end_timestamp is not None and
          timestamp > date_time_range.end_timestamp):
        return False

    return True

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._date_time_ranges:
      for date_time_range in self._date_time_ranges:
        if date_time_range.start_timestamp is None:
          end_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.end_timestamp)
          output_writer.Write(u'\t{0:s} after {1:s}\n'.format(
              date_time_range.time_value, end_time_string))

        elif date_time_range.end_timestamp is None:
          start_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.start_timestamp)
          output_writer.Write(u'\t{0:s} before {1:s}\n'.format(
              date_time_range.time_value, start_time_string))

        else:
          start_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.start_timestamp)
          end_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.end_timestamp)
          output_writer.Write(u'\t{0:s} between {1:s} and {2:s}\n'.format(
              date_time_range.time_value, start_time_string,
              end_time_string))


class ExtensionsFileEntryFilter(FileEntryFilter):
  """Class that implements extensions-based file entry filter."""

  def __init__(self, extensions):
    """Initializes the extensions-based file entry filter.

    An extension is defined as "pdf" as in "document.pdf".

    Args:
      extensions (list[str]): a list of extension strings.
    """
    super(ExtensionsFileEntryFilter, self).__init__()
    self._extensions = extensions

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """
    location = getattr(file_entry.path_spec, u'location', None)
    if not location:
      return

    if u'.' not in location:
      return False

    _, _, extension = location.rpartition(u'.')
    return extension.lower() in self._extensions

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._extensions:
      output_writer.Write(u'\textensions: {0:s}\n'.format(
          u', '.join(self._extensions)))


class NamesFileEntryFilter(FileEntryFilter):
  """Class that implements names-based file entry filter."""

  def __init__(self, names):
    """Initializes the names-based file entry filter.

    Args:
      names (list[str]): names.
    """
    super(NamesFileEntryFilter, self).__init__()
    self._names = names

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter.
    """
    if not self._names or not file_entry.IsFile():
      return

    return file_entry.name.lower() in self._names

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._names:
      output_writer.Write(u'\tnames: {0:s}\n'.format(
          u', '.join(self._names)))


class SignaturesFileEntryFilter(FileEntryFilter):
  """Class that implements signature-based file entry filter."""

  def __init__(self, specification_store, signature_identifiers):
    """Initializes the signature-based file entry filter.

    Args:
      specification_store (FormatSpecificationStore): a specification store.
      signature_identifiers (list[str]): signature identifiers.
    """
    super(SignaturesFileEntryFilter, self).__init__()
    self._file_scanner = None
    self._signature_identifiers = []

    self._file_scanner = self._GetScanner(
        specification_store, signature_identifiers)

  def _GetScanner(self, specification_store, signature_identifiers):
    """Initializes the scanner object form the specification store.

    Args:
      specification_store (FormatSpecificationStore): a specification store.
      signature_identifiers (list[str]): signature identifiers.

    Returns:
      pysigscan.scanner: signature scanner or None.
    """
    if not specification_store:
      return

    scanner_object = pysigscan.scanner()

    for format_specification in specification_store.specifications:
      if format_specification.identifier not in signature_identifiers:
        continue

      for signature in format_specification.signatures:
        pattern_offset = signature.offset
        if pattern_offset is None:
          signature_flags = pysigscan.signature_flags.NO_OFFSET
        elif pattern_offset < 0:
          pattern_offset *= -1
          signature_flags = pysigscan.signature_flags.RELATIVE_FROM_END
        else:
          signature_flags = pysigscan.signature_flags.RELATIVE_FROM_START

        scanner_object.add_signature(
            signature.identifier, pattern_offset, signature.pattern,
            signature_flags)

      self._signature_identifiers.append(format_specification.identifier)

    return scanner_object

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches the filter, False if not or
          None if the filter does not apply.
    """
    if not self._file_scanner or not file_entry.IsFile():
      return

    file_object = file_entry.GetFileObject()
    if not file_object:
      return False

    try:
      scan_state = pysigscan.scan_state()
      self._file_scanner.scan_file_object(scan_state, file_object)

    except IOError as exception:
      # TODO: replace location by display name.
      location = getattr(file_entry.path_spec, u'location', u'')
      logging.error((
          u'[skipping] unable to scan file: {0:s} for signatures '
          u'with error: {1:s}').format(location, exception))
      return False

    finally:
      file_object.close()

    return scan_state.number_of_scan_results > 0

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._file_scanner:
      output_writer.Write(u'\tsignature identifiers: {0:s}\n'.format(
          u', '.join(self._signature_identifiers)))


class FileEntryFilterCollection(object):
  """Class that implements a collection of file entry filters."""

  def __init__(self):
    """Initializes the file entry filter collection object."""
    super(FileEntryFilterCollection, self).__init__()
    self._filters = []

  def AddFilter(self, file_entry_filter):
    """Adds a file entry filter to the collection.

    Args:
      file_entry_filter (FileEntryFilter): file entry filter.
    """
    self._filters.append(file_entry_filter)

  def HasFilters(self):
    """Determines if filters are defined.

    Returns:
      bool: True if filters are defined.
    """
    return bool(self._filters)

  def Matches(self, file_entry):
    """Compares the file entry against the filter collection.

    Args:
      file_entry (dfvfs.FileEntry): file entry to compare.

    Returns:
      bool: True if the file entry matches one of the filters. If no filters
          are provided or applicable the result will be True.
    """
    if not self._filters:
      return True

    results = []
    for file_entry_filter in self._filters:
      result = file_entry_filter.Matches(file_entry)
      results.append(result)

    return True in results or False not in results

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    if self._filters:
      output_writer.Write(u'Filters:\n')
      for file_entry_filter in self._filters:
        file_entry_filter.Print(output_writer)


class ImageExportFrontend(frontend.Frontend):
  """Class that implements the image export front-end."""

  _DIRTY_CHARACTERS = frozenset([
      u'\x00', u'\x01', u'\x02', u'\x03', u'\x04', u'\x05', u'\x06', u'\x07',
      u'\x08', u'\x09', u'\x0a', u'\x0b', u'\x0c', u'\x0d', u'\x0e', u'\x0f',
      u'\x10', u'\x11', u'\x12', u'\x13', u'\x14', u'\x15', u'\x16', u'\x17',
      u'\x18', u'\x19', u'\x1a', u'\x1b', u'\x1c', u'\x1d', u'\x1e', u'\x1f',
      os.path.sep, u'!', u'$', u'%', u'&', u'*', u'+', u':', u';', u'<', u'>',
      u'?', u'@', u'|', u'~', u'\x7f'])

  _COPY_BUFFER_SIZE = 32768
  _READ_BUFFER_SIZE = 4096

  def __init__(self):
    """Initializes the front-end object."""
    super(ImageExportFrontend, self).__init__()
    self._abort = False
    self._digests = {}
    self._filter_collection = FileEntryFilterCollection()
    self._knowledge_base = None
    self._path_spec_extractor = extractors.PathSpecExtractor()
    self._resolver_context = context.Context()

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
      find_specs = utils.BuildFindSpecsFromFile(
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

  def _Preprocess(self, file_system, mount_point):
    """Preprocesses the image.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
    """
    if self._knowledge_base is not None:
      return

    self._knowledge_base = knowledge_base.KnowledgeBase()

    logging.debug(u'Preprocessing.')

    preprocess_manager.PreprocessPluginsManager.RunPlugins(
        file_system, mount_point, self._knowledge_base)

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

  def HasFilters(self):
    """Determines if filters are defined.

    Returns:
      bool: True if filters are defined.
    """
    return self._filter_collection.HasFilters()

  def ParseDateFilters(self, date_filters):
    """Parses the date filters.

    A date filter string is formatted as 3 comma separated values:
    time value, start date and time (string) and end date and time (string)

    The time value and either a start or end date and time is required.

    The date and time strings are formatted as:
    YYYY-MM-DD hh:mm:ss.######[+-]##:##
    Where # are numeric digits ranging from 0 to 9 and the seconds
    fraction can be either 3 or 6 digits. The time of day, seconds fraction
    and timezone offset are optional. The default timezone is UTC.

    Args:
      date_filters (list[str]): date filter definitions.

    Raises:
      ValueError: if the date filter definitions are invalid.
    """
    if not date_filters:
      return

    file_entry_filter = DateTimeFileEntryFilter()

    for date_filter in date_filters:
      date_filter_pieces = date_filter.split(u',')
      if len(date_filter_pieces) != 3:
        raise ValueError(
            u'Badly formed date filter: {0:s}'.format(date_filter))

      time_value, start_time_string, end_time_string = date_filter_pieces
      time_value = time_value.strip()
      start_time_string = start_time_string.strip()
      end_time_string = end_time_string.strip()

      try:
        file_entry_filter.AddDateTimeRange(
            time_value, start_time_string=start_time_string,
            end_time_string=end_time_string)
      except ValueError:
        raise ValueError(
            u'Badly formed date filter: {0:s}'.format(date_filter))

    self._filter_collection.AddFilter(file_entry_filter)

  def ParseExtensionsString(self, extensions_string):
    """Parses the extensions string.

    Args:
      extensions_string (str): comma separated extensions to filter.
    """
    if not extensions_string:
      return

    extensions_string = extensions_string.lower()
    extensions = [
        extension.strip() for extension in extensions_string.split(u',')]
    file_entry_filter = ExtensionsFileEntryFilter(extensions)
    self._filter_collection.AddFilter(file_entry_filter)

  def ParseNamesString(self, names_string):
    """Parses the name string.

    Args:
      names_string (str): comma separated filenames to filter.
    """
    if not names_string:
      return

    names_string = names_string.lower()
    names = [name.strip() for name in names_string.split(u',')]
    file_entry_filter = NamesFileEntryFilter(names)
    self._filter_collection.AddFilter(file_entry_filter)

  def ParseSignatureIdentifiers(self, data_location, signature_identifiers):
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
      specification_store = self.ReadSpecificationFile(path)
    except IOError as exception:
      raise IOError((
          u'Unable to read format specification file: {0:s} with error: '
          u'{1:s}').format(path, exception))

    signature_identifiers = signature_identifiers.lower()
    signature_identifiers = [
        identifier.strip() for identifier in signature_identifiers.split(u',')]
    file_entry_filter = SignaturesFileEntryFilter(
        specification_store, signature_identifiers)
    self._filter_collection.AddFilter(file_entry_filter)

  def PrintFilterCollection(self, output_writer):
    """Prints the filter collection.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    self._filter_collection.Print(output_writer)

  def ProcessSources(
      self, source_path_specs, destination_path, output_writer,
      filter_file=None, skip_duplicates=True):
    """Processes the sources.

    Args:
      source_path_specs (list[dfvfs.PathSpec]): path specifications to extract.
      destination_path (str): path where the extracted files should be stored.
      output_writer (CLIOutputWriter): output writer.
      filter_file (Optional[str]): name of of the filter file.
      skip_duplicates (Optional[bool]): True if files with duplicate content
          should be skipped.
    """
    if not os.path.isdir(destination_path):
      os.makedirs(destination_path)

    if filter_file:
      self._ExtractWithFilter(
          source_path_specs, destination_path, output_writer, filter_file,
          skip_duplicates=skip_duplicates)
    else:
      self._Extract(
          source_path_specs, destination_path, output_writer,
          skip_duplicates=skip_duplicates)

  def ReadSpecificationFile(self, path):
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
