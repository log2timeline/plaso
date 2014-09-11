#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The image export front-end."""

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

from plaso import preprocessors
from plaso.artifacts import knowledge_base
from plaso.engine import collector
from plaso.engine import utils as engine_utils
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import timelib
from plaso.lib import queue
from plaso.preprocessors import interface as preprocess_interface


def CalculateHash(file_object):
  """Return a hash for a given file object."""
  md5 = hashlib.md5()
  file_object.seek(0)

  data = file_object.read(4098)
  while data:
    md5.update(data)
    data = file_object.read(4098)

  return md5.hexdigest()


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
        errros.WrongFilterOption: If an attempt is made to filter against
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

  md5_dict = {}
  calc_md5 = False
  # TODO: Move this functionality into the frontend as a state attribute.
  _date_filter = None

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
    directory = u''
    filename = getattr(source_path_spec, 'location', None)
    if not filename:
      filename = source_path_spec.file_path

    # There will be issues on systems that use a different separator than a
    # forward slash. However a forward slash is always used in the pathspec.
    if os.path.sep != u'/':
      filename = filename.replace(u'/', os.path.sep)

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

    if cls.calc_md5:
      stat = file_entry.GetStat()
      inode = getattr(stat, 'ino', 0)
      file_object = file_entry.GetFileObject()
      md5sum = CalculateHash(file_object)
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


class ImageExtractorQueueConsumer(queue.PathSpecQueueConsumer):
  """Class that implements an image extractor queue consumer."""

  def __init__(self, process_queue, extensions, destination_path):
    """Initializes the image extractor queue consumer.

    Args:
      process_queue: the process queue (instance of Queue).
      extensions: a list of extensions.
      destination_path: the path where the extracted files should be stored.
    """
    super(ImageExtractorQueueConsumer, self).__init__(process_queue)
    self._destination_path = destination_path
    self._extensions = extensions

  def _ConsumePathSpec(self, path_spec):
    """Consumes a path specification callback for ConsumePathSpecs."""
    # TODO: move this into a function of path spec e.g. GetExtension().
    location = getattr(path_spec, 'location', None)
    if not location:
      location = path_spec.file_path
    _, _, extension = location.rpartition('.')
    if extension.lower() in self._extensions:
      vss_store_number = getattr(path_spec, 'vss_store_number', None)
      if vss_store_number is not None:
        filename_prefix = 'vss_{0:d}'.format(vss_store_number + 1)
      else:
        filename_prefix = ''

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

    input_queue = queue.SingleThreadedQueue()
    output_queue = queue.SingleThreadedQueue()
    output_producer = queue.EventObjectQueueProducer(output_queue)

    # TODO: add support to handle multiple partitions.
    self._source_path_spec = self.GetSourcePathSpec()

    image_collector = collector.Collector(
        input_queue, output_producer, self._source_path,
        self._source_path_spec)

    image_collector.Collect()

    FileSaver.calc_md5 = self._remove_duplicates

    input_queue_consumer = ImageExtractorQueueConsumer(
        input_queue, extensions, destination_path)
    input_queue_consumer.ConsumePathSpecs()

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

        filename_prefix = 'vss_{0:d}'.format(store_index)

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
    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
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

    guessed_os = preprocess_interface.GuessOS(searcher)
    logging.info(u'OS: {0:s}'.format(guessed_os))

    logging.info(u'Running preprocess.')
    for weight in preprocessors.PreProcessorsManager.GetWeightList(guessed_os):
      for plugin in preprocessors.PreProcessorsManager.GetWeight(
          guessed_os, weight):
        try:
          plugin.Run(searcher, self._knowledge_base)
        except errors.PreProcessFail as exception:
          logging.warning(
              u'Unable to run preprocessor: {0:s} with error: {1:s}'.format(
                  plugin.__class__.__name__, exception))

    logging.info(u'Preprocess done, saving files from image.')

  def ParseOptions(self, options, source_option='source'):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: optional name of the source option. The default is source.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(ImageExportFrontend, self).ParseOptions(
        options, source_option=source_option)

    filter_file = getattr(options, 'filter', None)
    if not filter_file and not getattr(options, 'extension_string', None):
      raise errors.BadConfigOption(
          u'Neither an extension string or a filter is defined.')

    if filter_file and not os.path.isfile(filter_file):
      raise errors.BadConfigOption(
          u'Unable to proceed, filter file: {0:s} does not exist.'.format(
              filter_file))

    if (getattr(options, 'no_vss', False) or
        getattr(options, 'include_duplicates', False)):
      self._remove_duplicates = False

    # Process date filter.
    date_filters = getattr(options, 'date_filters', [])
    if date_filters:
      date_filter_object = DateFilter()

      for date_filter in date_filters:
        date_filter_pieces = date_filter.split(',')
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
      BadConfigOption: if the options are incorrect or not supported.
    """
    super(ImageExportFrontend, self).ProcessSource(options)

    filter_file = getattr(options, 'filter', None)
    if filter_file:
      self._ExtractWithFilter(filter_file, options.path)

    extension_string = getattr(options, 'extension_string', None)
    if extension_string:
      extensions = [x.strip() for x in extension_string.split(',')]

      self._ExtractWithExtensions(extensions, options.path)
      logging.info(u'Files based on extension extracted.')


def Main():
  """The main function, running the show."""
  front_end = ImageExportFrontend()

  arg_parser = argparse.ArgumentParser(
      description=(
          'This is a simple collector designed to export files inside an '
          'image, both within a regular RAW image as well as inside a VSS. '
          'The tool uses a collection filter that uses the same syntax as a '
          'targeted plaso filter.'),
      epilog='And that\'s how you export files, plaso style.')

  arg_parser.add_argument(
      '-d', '--debug', dest='debug', action='store_true', default=False,
      help='Turn on debugging information.')

  arg_parser.add_argument(
      '-w', '--write', dest='path', action='store', default='.', type=str,
      help='The directory in which extracted files should be stored in.')

  arg_parser.add_argument(
      '-x', '--extensions', dest='extension_string', action='store',
      type=str, metavar='EXTENSION_STRING', help=(
          'If the purpose is to find all files given a certain extension '
          'this options should be used. This option accepts a comma separated '
          'string denoting all file extensions, eg: -x "csv,docx,pst".'))

  arg_parser.add_argument(
      '-f', '--filter', action='store', dest='filter', metavar='FILTER_FILE',
      type=str, help=(
          'Full path to the file that contains the collection filter, '
          'the file can use variables that are defined in preprocesing, '
          'just like any other log2timeline/plaso collection filter.'))

  arg_parser.add_argument(
      '--date-filter', '--date_filter', action='append', type=str,
      dest='date_filters', metavar="TYPE_START_END", default=None, help=(
          'Add a date based filter to the export criteria. If a date based '
          'filter is set no file is saved unless it\'s within the date '
          'boundary. This parameter should be in the form of "TYPE,START,END" '
          'where TYPE defines which timestamp this date filter affects, eg: '
          'atime, ctime, crtime, bkup, etc. START defines the start date and '
          'time of the boundary and END defines the end time. Both timestamps '
          'are optional and should be set as - if not needed. The correct form '
          'of the timestamp value is in the form of "YYYY-MM-DD HH:MM:SS" or '
          '"YYYY-MM-DD". Examples are "atime, 2013-01-01 23:12:14, 2013-02-23" '
          'This parameter can be repeated as needed to add additional date '
          'date boundaries, eg: once for atime, once for crtime, etc.'))

  arg_parser.add_argument(
      '--include_duplicates', dest='include_duplicates', action='store_true',
      default=False, help=(
          'By default if VSS is turned on all files saved will have their '
          'MD5 sum calculated and compared to other files already saved '
          'with the same inode value. If the MD5 sum is the same the file '
          'does not get saved again. This option turns off that behavior '
          'so that all files will get stored, even if they are duplicates.'))

  front_end.AddImageOptions(arg_parser)
  front_end.AddVssProcessingOptions(arg_parser)

  arg_parser.add_argument(
      'image', action='store', metavar='IMAGE', default=None, type=str, help=(
          'The full path to the image file that we are about to extract files '
          'from, it should be a raw image or another image that plaso '
          'supports.'))

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
  except KeyboardInterrupt:
    logging.warning(u'Aborted by user.')
    return False
  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
