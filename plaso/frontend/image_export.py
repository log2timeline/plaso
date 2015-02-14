#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The image export front-end."""

import abc
import argparse
import collections
import hashlib
import logging
import os
import sys

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.artifacts import knowledge_base
from plaso.engine import collector
from plaso.engine import utils as engine_utils
from plaso.engine import queue
from plaso.engine import single_process
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
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
      A boolean indicating if the file entry matches the filter.
    """


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
      A boolean indicating if the file entry matches the filter.
    """
    location = getattr(file_entry.path_spec, u'location', None)
    if not location:
      return False

    _, _, extension = location.rpartition(u'.')
    if not extension:
      return False

    return extension.lower() in self._extensions


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
    """
    if not self._filters:
      return False

    result = False
    for file_entry_filter in self._filters:
      result = file_entry_filter.Matches(file_entry)
      if result:
        break

    return result


# TODO: migrate to FileEntryFilter in a follow up CL.
class DateFilter(object):
  """Class that implements a date filter for file entries."""

  DATE_FILTER_INSTANCE = collections.namedtuple(
      'date_filter_instance', 'type start end')

  DATE_FILTER_TYPES = frozenset([
      u'atime', u'bkup', u'ctime', u'crtime', u'dtime', u'mtime'])

  def __init__(self):
    """Initialize the date filter object."""
    super(DateFilter, self).__init__()
    self._filters = []

  @property
  def number_of_filters(self):
    """Return back the filter count."""
    return len(self._filters)

  def Add(self, filter_type, filter_start=None, filter_end=None):
    """Add a date filter.

    Args:
      filter_type: String that defines what timestamp is affected by the
                    date filter, valid values are atime, ctime, crtime,
                    dtime, bkup and mtime.
      filter_start: Optional start date of the filter. This is a string
                    in the form of "YYYY-MM-DD HH:MM:SS", or "YYYY-MM-DD".
                    If not supplied there will be no limitation to the initial
                    timeframe.
      filter_end: Optional end date of the filter. This is a string
                  in the form of "YYYY-MM-DD HH:MM:SS", or "YYYY-MM-DD".
                  If not supplied there will be no limitation to the initial
                  timeframe.

    Raises:
      errors.WrongFilterOption: If the filter is badly formed.
    """
    if not isinstance(filter_type, basestring):
      raise errors.WrongFilterOption(u'Filter type must be a string.')

    if filter_start is None and filter_end is None:
      raise errors.WrongFilterOption(
          u'A date filter has to have either a start or an end date.')

    filter_type_lower = filter_type.lower()
    if filter_type_lower not in self.DATE_FILTER_TYPES:
      raise errors.WrongFilterOption(u'Unknown filter type: {0:s}.'.format(
          filter_type))

    date_filter_type = filter_type_lower
    date_filter_start = None
    date_filter_end = None

    if filter_start is not None:
      # If the date string is invalid the timestamp will be set to zero,
      # which is also a valid date. Thus all invalid timestamp strings
      # will be set to filter from the POSIX epoch time.
      # Thus the actual value of the filter is printed out so that the user
      # may catch this potentially unwanted behavior.
      date_filter_start = timelib.Timestamp.FromTimeString(filter_start)
      logging.info(
          u'Date filter for start date configured: [{0:s}] {1:s}'.format(
              date_filter_type,
              timelib.Timestamp.CopyToIsoFormat(date_filter_start)))

    if filter_end is not None:
      date_filter_end = timelib.Timestamp.FromTimeString(filter_end)
      logging.info(
          u'Date filter for end date configured: [{0:s}] {1:s}'.format(
              date_filter_type,
              timelib.Timestamp.CopyToIsoFormat(date_filter_end)))

      # Make sure that the end timestamp occurs after the beginning.
      # If not then we need to reverse the time range.
      if (date_filter_start is not None and
          date_filter_start > date_filter_end):
        temporary_placeholder = date_filter_end
        date_filter_end = date_filter_start
        date_filter_start = temporary_placeholder

    self._filters.append(self.DATE_FILTER_INSTANCE(
        date_filter_type, date_filter_start, date_filter_end))

  def CompareFileEntry(self, file_entry):
    """Compare the set date filters against timestamps of a file entry.

    Args:
      file_entry: The file entry (instance of dfvfs.FileEntry).

    Returns:
      True, if there are no date filters set. Otherwise the date filters are
      compared and True only returned if the timestamps are outside of the time
      range.

    Raises:
        errors.WrongFilterOption: If an attempt is made to filter against
                                  a date type that is not stored in the stat
                                  object.
    """
    if not self._filters:
      return True

    # Compare timestamps of the file entry.
    stat = file_entry.GetStat()

    # Go over each filter.
    for date_filter in self._filters:
      posix_time = getattr(stat, date_filter.type, None)

      if posix_time is None:
        # Trying to filter against a date type that is not saved in the stat
        # object.
        raise errors.WrongFilterOption(
            u'Date type: {0:s} is not stored in the file entry'.format(
                date_filter.type))

      timestamp = timelib.Timestamp.FromPosixTime(posix_time)

      if date_filter.start is not None and (timestamp < date_filter.start):
        logging.debug((
            u'[skipping] Not saving file: {0:s}, timestamp out of '
            u'range.').format(file_entry.path_spec.location))
        return False

      if date_filter.end is not None and (timestamp > date_filter.end):
        logging.debug((
            u'[skipping] Not saving file: {0:s}, timestamp out of '
            u'range.').format(file_entry.path_spec.location))
        return False

    return True

  def Remove(self, filter_type, filter_start=None, filter_end=None):
    """Remove a date filter from the set of defined date filters.

    Args:
      filter_type: String that defines what timestamp is affected by the
                    date filter, valid values are atime, ctime, crtime,
                    dtime, bkup and mtime.
      filter_start: Optional start date of the filter. This is a string
                    in the form of "YYYY-MM-DD HH:MM:SS", or "YYYY-MM-DD".
                    If not supplied there will be no limitation to the initial
                    timeframe.
      filter_end: Optional end date of the filter. This is a string
                  in the form of "YYYY-MM-DD HH:MM:SS", or "YYYY-MM-DD".
                  If not supplied there will be no limitation to the initial
                  timeframe.
    """
    if not self._filters:
      return

    # TODO: Instead of doing it this way calculate a hash for every filter
    # that is stored and use that for removals.
    for date_filter_index, date_filter in enumerate(self._filters):
      if filter_start is None:
        date_filter_start = filter_start
      else:
        date_filter_start = timelib.Timestamp.FromTimeString(filter_start)
      if filter_end is None:
        date_filter_end = filter_end
      else:
        date_filter_end = timelib.Timestamp.FromTimeString(filter_end)

      if (date_filter.type == filter_type and
          date_filter.start == date_filter_start and
          date_filter.end == date_filter_end):
        del self._filters[date_filter_index]
        return

  def Reset(self):
    """Resets the date filter."""
    self._filters = []


class FileSaver(object):
  """A simple class that is used to save files."""

  _READ_BUFFER_SIZE = 4096

  md5_dict = {}
  calc_md5 = False

  # TODO: Move this functionality into the frontend as a state attribute.
  _date_filter = None

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
    file_object.seek(0)

    data = file_object.read(cls._READ_BUFFER_SIZE)
    while data:
      md5.update(data)
      data = file_object.read(cls._READ_BUFFER_SIZE)

    return md5.hexdigest()

  @classmethod
  def SetDateFilter(cls, date_filter):
    """Set a date filter for the file saver.

    If a date filter is set files will not be saved unless they are within
    the time boundaries.

    Args:
      date_filter: A date filter object (instance of DateFilter).
    """
    cls._date_filter = date_filter

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

    filename = getattr(source_path_spec, u'location', None)
    if not filename:
      filename = source_path_spec.file_path

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

    # Check if we do not want to save the file.
    if cls._date_filter and not cls._date_filter.CompareFileEntry(file_entry):
      return

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

    self._knowledge_base = None
    self._remove_duplicates = True
    self._source_path_spec = None

  # TODO: merge with collector and/or engine.
  def _ExtractWithExtensions(self, extensions, destination_path):
    """Extracts files using extensions.

    Args:
      extensions: a list of extensions.
      destination_path: the path where the extracted files should be stored.
    """
    logging.info(u'Finding files with extensions: {0:s}'.format(extensions))

    if not os.path.isdir(destination_path):
      os.makedirs(destination_path)

    input_queue = single_process.SingleProcessQueue()

    # TODO: add support to handle multiple partitions.
    self._source_path_spec = self.GetSourcePathSpec()

    image_collector = collector.Collector(
        input_queue, self._source_path, self._source_path_spec)

    image_collector.Collect()

    FileSaver.calc_md5 = self._remove_duplicates

    filter_collection = FileEntryFilterCollection()
    file_entry_filter = ExtensionsFileEntryFilter(extensions)
    filter_collection.AddFilter(file_entry_filter)

    input_queue_consumer = ImageExtractorQueueConsumer(
        input_queue, destination_path, filter_collection)
    input_queue_consumer.ConsumeItems()

  # TODO: merge with collector and/or engine.
  def _ExtractWithFilter(self, filter_file_path, destination_path):
    """Extracts files using a filter expression.

    This method runs the file extraction process on the image and
    potentially on every VSS if that is wanted.

    Args:
      filter_file_path: The path of the file that contains the filter
                        expressions.
      destination_path: The path where the extracted files should be stored.
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
      FileSaver.WriteFile(path_spec, destination_path)

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

        filename_prefix = u'vss_{0:d}'.format(store_index)

        file_system = path_spec_resolver.Resolver.OpenFileSystem(
            path_spec, resolver_context=self._resolver_context)
        searcher = file_system_searcher.FileSystemSearcher(
            file_system, vss_path_spec)

        for path_spec in searcher.Find(find_specs=find_specs):
          FileSaver.WriteFile(
              path_spec, destination_path, filename_prefix=filename_prefix)

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

    return file_system_searcher.FileSystemSearcher(file_system, mount_point)

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
    if not filter_file and not getattr(options, u'extension_string', None):
      raise errors.BadConfigOption(
          u'Neither an extension string or a filter is defined.')

    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'Unable to proceed, filter file: {0:s} does not exist.'.format(
              filter_file))

    if (getattr(options, u'no_vss', False) or
        getattr(options, u'include_duplicates', False)):
      self._remove_duplicates = False

    # Process date filter.
    date_filters = getattr(options, u'date_filters', [])
    if date_filters:
      date_filter_object = DateFilter()

      for date_filter in date_filters:
        date_filter_pieces = date_filter.split(u',')
        if len(date_filter_pieces) != 3:
          raise errors.BadConfigOption(
              u'Date filter badly formed: {0:s}'.format(date_filter))

        filter_type, filter_start, filter_end = date_filter_pieces
        date_filter_object.Add(
            filter_type=filter_type.strip(), filter_start=filter_start.strip(),
            filter_end=filter_end.strip())

      # TODO: Move the date filter to the front-end as an attribute.
      FileSaver.SetDateFilter(date_filter_object)

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
      self._ExtractWithFilter(filter_file, options.path)

    extension_string = getattr(options, u'extension_string', None)
    if extension_string:
      extensions = [x.strip() for x in extension_string.split(u',')]

      self._ExtractWithExtensions(extensions, options.path)
      logging.info(u'Files based on extension extracted.')


def Main():
  """The main function, running the show."""
  front_end = ImageExportFrontend()

  arg_parser = argparse.ArgumentParser(
      description=(
          u'This is a simple collector designed to export files inside an '
          u'image, both within a regular RAW image as well as inside a VSS. '
          u'The tool uses a collection filter that uses the same syntax as a '
          u'targeted plaso filter.'),
      epilog=u'And that\'s how you export files, plaso style.')

  arg_parser.add_argument(
      u'-d', u'--debug', dest=u'debug', action=u'store_true', default=False,
      help=u'Turn on debugging information.')

  arg_parser.add_argument(
      u'-w', u'--write', dest=u'path', action=u'store', default=u'.', type=str,
      help=u'The directory in which extracted files should be stored in.')

  arg_parser.add_argument(
      u'-x', u'--extensions', dest=u'extension_string', action=u'store',
      type=str, metavar=u'EXTENSION_STRING', help=(
          u'If the purpose is to find all files given a certain extension '
          u'this options should be used. This option accepts a comma separated '
          u'string denoting all file extensions, eg: -x "csv,docx,pst".'))

  arg_parser.add_argument(
      u'-f', u'--filter', action=u'store', dest=u'filter',
      metavar=u'FILTER_FILE', type=str, help=(
          u'Full path to the file that contains the collection filter, '
          u'the file can use variables that are defined in preprocesing, '
          u'just like any other log2timeline/plaso collection filter.'))

  arg_parser.add_argument(
      u'--date-filter', u'--date_filter', action=u'append', type=str,
      dest=u'date_filters', metavar=u'TYPE_START_END', default=None, help=(
          u'Add a date based filter to the export criteria. If a date based '
          u'filter is set no file is saved unless it\'s within the date '
          u'boundary. This parameter should be in the form of "TYPE,START,END" '
          u'where TYPE defines which timestamp this date filter affects, eg: '
          u'atime, ctime, crtime, bkup, etc. START defines the start date and '
          u'time of the boundary and END defines the end time. Both timestamps '
          u'are optional and should be set as - if not needed. The correct '
          u'form of the timestamp value is in the form of "YYYY-MM-DD '
          u'HH:MM:SS" or "YYYY-MM-DD". Examples are "atime, 2013-01-01 '
          u'23:12:14, 2013-02-23". This parameter can be repeated as needed '
          u'to add additional date date boundaries, eg: once for atime, once '
          u'for crtime, etc.'))

  arg_parser.add_argument(
      u'--include_duplicates', dest=u'include_duplicates', action=u'store_true',
      default=False, help=(
          u'By default if VSS is turned on all files saved will have their '
          u'MD5 sum calculated and compared to other files already saved '
          u'with the same inode value. If the MD5 sum is the same the file '
          u'does not get saved again. This option turns off that behavior '
          u'so that all files will get stored, even if they are duplicates.'))

  front_end.AddImageOptions(arg_parser)
  front_end.AddVssProcessingOptions(arg_parser)

  arg_parser.add_argument(
      u'image', action=u'store', metavar=u'IMAGE', default=None, type=str,
      help=(
          u'The full path to the image file that we are about to extract files '
          u'from, it should be a raw image or another image that plaso '
          u'supports.'))

  options = arg_parser.parse_args()

  format_str = u'%(asctime)s [%(levelname)s] %(message)s'
  if options.debug:
    logging.basicConfig(level=logging.DEBUG, format=format_str)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  try:
    front_end.ParseOptions(options, source_option='image')
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error(u'{0:s}'.format(exception))
    return False

  try:
    front_end.ProcessSource(options)
    logging.info(u'Processing completed.')

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except errors.SourceScannerError as exception:
    logging.warning((
        u'Unable to scan for a supported filesystem with error: {0:s}\n'
        u'Most likely the image format is not supported by the '
        u'tool.').format(exception))
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
