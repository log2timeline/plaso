# -*- coding: utf-8 -*-
"""The image export front-end."""

import abc
import collections
import hashlib
import logging
import os
import textwrap

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

import pysigscan

from plaso.artifacts import knowledge_base
from plaso.engine import collector
from plaso.engine import utils as engine_utils
from plaso.engine import queue
from plaso.engine import single_process
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import specification
from plaso.lib import timelib
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager


class FileEntryFilter(object):
  """Class that implements the file entry filter interface."""

  @abc.abstractmethod
  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry: The file entry (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file entry matches the filter or
      None if the filter does not apply
    """

  @abc.abstractmethod
  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer: the output writer object (instance of
                     StdoutFrontendOutputWriter).
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
    """Add a date time filter range.

    The time strings are formatted as:
    YYYY-MM-DD hh:mm:ss.######[+-]##:##
    Where # are numeric digits ranging from 0 to 9 and the seconds
    fraction can be either 3 or 6 digits. The time of day, seconds fraction
    and timezone offset are optional. The default timezone is UTC.

    Args:
      time_value: the time value strting e.g. atime, ctime, crtime, dtime,
                  bkup and mtime.
      start_time_string: the start date and time value string.
      end_time_string: the end date and time value string.

    Raises:
      ValueError: If the filter is badly formed.
    """
    if not isinstance(time_value, basestring):
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
      file_entry: The file entry (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file entry matches the filter or
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
      output_writer: the output writer object (instance of
                     StdoutFrontendOutputWriter).
    """
    if self._date_time_ranges:
      for date_time_range in self._date_time_ranges:
        if date_time_range.start_timestamp is None:
          start_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.start_timestamp)
          output_writer.Write(u'\t{0:s} before {1:s}\n'.format(
              date_time_range.time_value, start_time_string))

        elif date_time_range.end_timestamp is None:
          end_time_string = timelib.Timestamp.CopyToIsoFormat(
              date_time_range.end_timestamp)
          output_writer.Write(u'\t{0:s} after {1:s}\n'.format(
              date_time_range.time_value, end_time_string))

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
      extensions: a list of extension strings.
    """
    super(ExtensionsFileEntryFilter, self).__init__()
    self._extensions = extensions

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry: The file entry (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file entry matches the filter or
      None if the filter does not apply
    """
    location = getattr(file_entry.path_spec, u'location', None)
    if not location:
      return

    _, _, extension = location.rpartition(u'.')
    if not extension:
      return False

    return extension.lower() in self._extensions

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer: the output writer object (instance of
                     StdoutFrontendOutputWriter).
    """
    if self._extensions:
      output_writer.Write(u'\textensions: {0:s}\n'.format(
          u', '.join(self._extensions)))


class NamesFileEntryFilter(FileEntryFilter):
  """Class that implements names-based file entry filter."""

  def __init__(self, names):
    """Initializes the names-based file entry filter.

    Args:
      names: a list of name strings.
    """
    super(NamesFileEntryFilter, self).__init__()
    self._names = names

  def Matches(self, file_entry):
    """Compares the file entry against the filter.

    Args:
      file_entry: The file entry (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file entry matches the filter.
    """
    if not self._names or not file_entry.IsFile():
      return

    return file_entry.name.lower() in self._names

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer: the output writer object (instance of
                     StdoutFrontendOutputWriter).
    """
    if self._names:
      output_writer.Write(u'\tnames: {0:s}\n'.format(
          u', '.join(self._names)))


class SignaturesFileEntryFilter(FileEntryFilter):
  """Class that implements signature-based file entry filter."""

  def __init__(self, specification_store, signature_identifiers):
    """Initializes the signature-based file entry filter.

    Args:
      specification_store: a specification store (instance of
                           FormatSpecificationStore).
      signature_identifiers: a list of signature identifiers.
    """
    super(SignaturesFileEntryFilter, self).__init__()
    self._signature_identifiers = []

    if specification_store:
      self._file_scanner = self._GetScanner(
          specification_store, signature_identifiers)
    else:
      self._file_scanner = None

  def _GetScanner(self, specification_store, signature_identifiers):
    """Initializes the scanner object form the specification store.

    Args:
      specification_store: a specification store (instance of
                           FormatSpecificationStore).
      signature_identifiers: a list of signature identifiers.

    Returns:
      A scanner object (instance of pysigscan.scanner).
    """
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
      file_entry: The file entry (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file entry matches the filter or
      None if the filter does not apply
    """
    if not self._file_scanner or not file_entry.IsFile():
      return

    file_object = file_entry.GetFileObject()
    scan_state = pysigscan.scan_state()

    try:
      self._file_scanner.scan_file_object(scan_state, file_object)
    finally:
      file_object.close()

    return scan_state.number_of_scan_results > 0

  def Print(self, output_writer):
    """Prints a human readable version of the filter.

    Args:
      output_writer: the output writer object (instance of
                     StdoutFrontendOutputWriter).
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
      file_entry_filter: a file entry filter (instance of FileEntryFilter).
    """
    self._filters.append(file_entry_filter)

  def Matches(self, file_entry):
    """Compares the file entry against the filter collection.

    Args:
      file_entry: The file entry (instance of dfvfs.FileEntry).

    Returns:
      A boolean indicating if the file entry matches one of the filters.
      If no filters are provided or applicable the result will be True.
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
      output_writer: the output writer object (instance of
                     StdoutFrontendOutputWriter).
    """
    if self._filters:
      output_writer.Write(u'Filters:\n')
      for file_entry_filter in self._filters:
        file_entry_filter.Print(output_writer)


class FileSaver(object):
  """A simple class that is used to save files."""

  _READ_BUFFER_SIZE = 4096

  md5_dict = {}
  calc_md5 = False

  # TODO: combine write and hash in one function.
  @classmethod
  def _CalculateHash(cls, file_object):
    """Calculates a MD5 hash of the contents of given file object.

    Args:
      file_object: a file-like object.

    Returns:
      A hexadecimal string of the MD5 hash.
    """
    md5 = hashlib.md5()
    file_object.seek(0, os.SEEK_SET)

    data = file_object.read(cls._READ_BUFFER_SIZE)
    while data:
      md5.update(data)
      data = file_object.read(cls._READ_BUFFER_SIZE)

    return md5.hexdigest()

  @classmethod
  def WriteFile(cls, source_path_spec, destination_path, filename_prefix=''):
    """Writes the contents of the source to the destination file.

    Args:
      source_path_spec: the path specification of the source file.
      destination_path: the path of the destination file.
      filename_prefix: optional prefix for the filename. The default is an
                       empty string.
    """
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(source_path_spec)
    if not file_entry.IsFile():
      return

    filename = getattr(source_path_spec, u'location', None)
    if not filename:
      filename = source_path_spec.file_path

    # TODO: this does not hold for Windows fix this.

    # There will be issues on systems that use a different separator than a
    # forward slash. However a forward slash is always used in the pathspec.
    if os.path.sep != u'/':
      filename = filename.replace(u'/', os.path.sep)

    directory = u''
    if os.path.sep in filename:
      directory_string, _, filename = filename.rpartition(os.path.sep)
      if directory_string:
        directory = os.path.join(
            destination_path, *directory_string.split(os.path.sep))

    if filename_prefix:
      extracted_filename = u'{0:s}_{1:s}'.format(filename_prefix, filename)
    else:
      extracted_filename = filename

    while extracted_filename.startswith(os.path.sep):
      extracted_filename = extracted_filename[1:]

    if directory:
      if not os.path.isdir(directory):
        os.makedirs(directory)
    else:
      directory = destination_path

    if cls.calc_md5 and file_entry.IsFile():
      stat = file_entry.GetStat()
      inode = getattr(stat, u'ino', 0)
      file_object = file_entry.GetFileObject()
      md5sum = cls._CalculateHash(file_object)
      if inode in cls.md5_dict:
        if md5sum in cls.md5_dict[inode]:
          return
        cls.md5_dict[inode].append(md5sum)
      else:
        cls.md5_dict[inode] = [md5sum]

    try:
      file_object = file_entry.GetFileObject()
      frontend_utils.OutputWriter.WriteFile(
          file_object, os.path.join(directory, extracted_filename))
    except IOError as exception:
      logging.error(
          u'[skipping] unable to save file: {0:s} with error: {1:s}'.format(
              filename, exception))


class ImageExtractorQueueConsumer(queue.ItemQueueConsumer):
  """Class that implements an image extractor queue consumer."""

  def __init__(self, process_queue, destination_path, filter_collection):
    """Initializes the image extractor queue consumer.

    Args:
      process_queue: the process queue (instance of Queue).
      destination_path: the path where the extracted files should be stored.
      filter_collection: the file entry filter collection (instance of
                         FileEntryFilterCollection)
    """
    super(ImageExtractorQueueConsumer, self).__init__(process_queue)
    self._destination_path = destination_path
    self._filter_collection = filter_collection

  def _ConsumeItem(self, path_spec):
    """Consumes an item callback for ConsumeItems.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).
    """
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    if not self._filter_collection.Matches(file_entry):
      return

    vss_store_number = getattr(path_spec, u'vss_store_number', None)
    if vss_store_number is not None:
      filename_prefix = u'vss_{0:d}'.format(vss_store_number + 1)
    else:
      filename_prefix = u''

    FileSaver.WriteFile(
        path_spec, self._destination_path, filename_prefix=filename_prefix)


class ImageExportFrontend(frontend.StorageMediaFrontend):
  """Class that implements the image export front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(ImageExportFrontend, self).__init__(input_reader, output_writer)
    self._filter_collection = FileEntryFilterCollection()
    self._knowledge_base = None
    self._remove_duplicates = True
    self._source_path_spec = None

  # TODO: merge with collector and/or engine.
  def _Extract(self, destination_path):
    """Extracts files.

    Args:
      destination_path: the path where the extracted files should be stored.
    """
    if not os.path.isdir(destination_path):
      os.makedirs(destination_path)

    input_queue = single_process.SingleProcessQueue()

    # TODO: add support to handle multiple partitions.
    self._source_path_spec = self.GetSourcePathSpec()

    image_collector = collector.Collector(
        input_queue, self._source_path, self._source_path_spec)

    image_collector.Collect()

    FileSaver.calc_md5 = self._remove_duplicates

    input_queue_consumer = ImageExtractorQueueConsumer(
        input_queue, destination_path, self._filter_collection)
    input_queue_consumer.ConsumeItems()

  def _ExtractFile(self, path_spec, destination_path):
    """Extracts a file.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).
      destination_path: the path where the extracted files should be stored.
    """
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    if not self._filter_collection.Matches(file_entry):
      return

    vss_store_number = getattr(path_spec, u'vss_store_number', None)
    if vss_store_number is not None:
      filename_prefix = u'vss_{0:d}'.format(vss_store_number + 1)
    else:
      filename_prefix = u''

    FileSaver.WriteFile(
        path_spec, destination_path, filename_prefix=filename_prefix)

  # TODO: merge with collector and/or engine.
  def _ExtractWithFilter(self, destination_path, filter_file_path):
    """Extracts files using a filter expression.

    This method runs the file extraction process on the image and
    potentially on every VSS if that is wanted.

    Args:
      destination_path: The path where the extracted files should be stored.
      filter_file_path: The path of the file that contains the filter
                        expressions.
    """
    # TODO: add support to handle multiple partitions.
    self._source_path_spec = self.GetSourcePathSpec()

    searcher = self._GetSourceFileSystemSearcher(
        resolver_context=self._resolver_context)

    if self._knowledge_base is None:
      self._Preprocess(searcher)

    if not os.path.isdir(destination_path):
      os.makedirs(destination_path)

    find_specs = engine_utils.BuildFindSpecsFromFile(
        filter_file_path, pre_obj=self._knowledge_base.pre_obj)

    # Save the regular files.
    FileSaver.calc_md5 = self._remove_duplicates

    for path_spec in searcher.Find(find_specs=find_specs):
      self._ExtractFile(path_spec, destination_path)

    if self._process_vss and self._vss_stores:
      volume_path_spec = self._source_path_spec.parent

      logging.info(u'Extracting files from VSS.')
      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
          parent=volume_path_spec)

      vss_file_entry = path_spec_resolver.Resolver.OpenFileEntry(vss_path_spec)

      number_of_vss = vss_file_entry.number_of_sub_file_entries

      # In plaso 1 represents the first store index in dfvfs and pyvshadow 0
      # represents the first store index so 1 is subtracted.
      vss_store_range = [store_nr - 1 for store_nr in self._vss_stores]

      for store_index in vss_store_range:
        logging.info(u'Extracting files from VSS {0:d} out of {1:d}'.format(
            store_index + 1, number_of_vss))

        vss_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_VSHADOW, store_index=store_index,
            parent=volume_path_spec)
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
            parent=vss_path_spec)

        file_system = path_spec_resolver.Resolver.OpenFileSystem(
            path_spec, resolver_context=self._resolver_context)
        searcher = file_system_searcher.FileSystemSearcher(
            file_system, vss_path_spec)

        for path_spec in searcher.Find(find_specs=find_specs):
          self._ExtractFile(path_spec, destination_path)

        file_system.Close()

  # TODO: refactor, this is a duplicate of the function in engine.
  def _GetSourceFileSystemSearcher(self, resolver_context=None):
    """Retrieves the file system searcher of the source.

    Args:
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      The file system searcher object (instance of dfvfs.FileSystemSearcher).

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not self._source_path_spec:
      raise RuntimeError(u'Missing source.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        self._source_path_spec, resolver_context=resolver_context)

    type_indicator = self._source_path_spec.type_indicator
    if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
      mount_point = self._source_path_spec
    else:
      mount_point = self._source_path_spec.parent

    # TODO: add explicit close of file_system.
    return file_system_searcher.FileSystemSearcher(file_system, mount_point)

  def _ParseDateFiltersOption(self, options):
    """Parses the date filters option.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    date_filters = getattr(options, u'date_filters', None)
    if not date_filters:
      return

    file_entry_filter = DateTimeFileEntryFilter()

    for date_filter in date_filters:
      date_filter_pieces = date_filter.split(u',')
      if len(date_filter_pieces) != 3:
        raise errors.BadConfigOption(
            u'Date filter badly formed: {0:s}'.format(date_filter))

      time_value, start_time_string, end_time_string = date_filter_pieces
      time_value = time_value.strip()
      start_time_string = start_time_string.strip()
      end_time_string = end_time_string.strip()

      try:
        file_entry_filter.AddDateTimeRange(
            time_value, start_time_string=start_time_string,
            end_time_string=end_time_string)
      except ValueError:
        raise errors.BadConfigOption(
            u'Date filter badly formed: {0:s}'.format(date_filter))

    self._filter_collection.AddFilter(file_entry_filter)

  def _ParseExtensionsStringOption(self, options):
    """Parses the extensions string option.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    extensions_string = getattr(options, u'extensions_string', None)
    if not extensions_string:
      return

    extensions_string = extensions_string.lower()
    extensions = [
        extension.strip() for extension in extensions_string.split(u',')]
    file_entry_filter = ExtensionsFileEntryFilter(extensions)
    self._filter_collection.AddFilter(file_entry_filter)

  def _ParseNamesStringOption(self, options):
    """Parses the name string option.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    names_string = getattr(options, u'names_string', None)
    if not names_string:
      return

    names_string = names_string.lower()
    names = [name.strip() for name in names_string.split(u',')]
    file_entry_filter = NamesFileEntryFilter(names)
    self._filter_collection.AddFilter(file_entry_filter)

  def _ParseSignatureIdentifiersOptions(self, options):
    """Parses the signature identifiers option.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    signature_identifiers = getattr(options, u'signature_identifiers', None)
    if not signature_identifiers:
      return

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

    signature_identifiers = signature_identifiers.lower()
    signature_identifiers = [
        identifier.strip() for identifier in signature_identifiers.split(u',')]
    file_entry_filter = SignaturesFileEntryFilter(
        specification_store, signature_identifiers)
    self._filter_collection.AddFilter(file_entry_filter)

  def _Preprocess(self, searcher):
    """Preprocesses the image.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
    """
    if self._knowledge_base is not None:
      return

    self._knowledge_base = knowledge_base.KnowledgeBase()

    logging.info(u'Guessing OS')

    platform = preprocess_interface.GuessOS(searcher)
    logging.info(u'OS: {0:s}'.format(platform))

    logging.info(u'Running preprocess.')

    preprocess_manager.PreprocessPluginsManager.RunPlugins(
        platform, searcher, self._knowledge_base)

    logging.info(u'Preprocess done, saving files from image.')

  def _ReadSpecificationFile(self, path):
    """Reads the format specification file.

    Args:
      path: the path of the format specification file.

    Returns:
      The format specification store (instance of FormatSpecificationStore).
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

  def ListSignatureIdentifiers(self, options):
    """Lists the signature identifier.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    data_location = getattr(options, u'data_location', None)
    if not data_location:
      raise errors.BadConfigOption(u'Missing data location.')

    path = os.path.join(data_location, u'signatures.conf')
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

  def ParseOptions(self, options, source_option=u'source'):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: optional name of the source option. The default is source.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ImageExportFrontend, self).ParseOptions(
        options, source_option=source_option)

    filter_file = getattr(options, u'filter', None)
    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'Unable to proceed, filter file: {0:s} does not exist.'.format(
              filter_file))

    if (getattr(options, u'no_vss', False) or
        getattr(options, u'include_duplicates', False)):
      self._remove_duplicates = False

    self._data_location = getattr(options, u'data_location', None)

    self._ParseDateFiltersOption(options)
    self._ParseExtensionsStringOption(options)
    self._ParseNamesStringOption(options)
    self._ParseSignatureIdentifiersOptions(options)

  def PrintFilterCollection(self):
    """Prints the filter collection."""
    self._filter_collection.Print(self._output_writer)

  def ProcessSource(self, options):
    """Processes the source.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      SourceScannerError: if the source scanner could not find a supported
                          file system.
      UserAbort: if the user initiated an abort.
    """
    self.ScanSource(options)

    filter_file = getattr(options, u'filter', None)
    if filter_file:
      self._ExtractWithFilter(options.path, filter_file)
    else:
      self._Extract(options.path)
