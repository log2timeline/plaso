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


class FileSaver(object):
  """A simple class that is used to save files."""
  md5_dict = {}
  calc_md5 = False

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

    save_file = True
    if cls.calc_md5:
      stat = file_entry.GetStat()
      inode = getattr(stat, 'ino', 0)
      file_object = file_entry.GetFileObject()
      md5sum = CalculateHash(file_object)
      if inode in cls.md5_dict:
        if md5sum in cls.md5_dict[inode]:
          save_file = False
        else:
          cls.md5_dict[inode].append(md5sum)
      else:
        cls.md5_dict[inode] = [md5sum]

    if save_file:
      try:
        file_object = file_entry.GetFileObject()
        frontend_utils.OutputWriter.WriteFile(
            file_object, os.path.join(directory, extracted_filename))
      except IOError as exception:
        logging.error(
            u'[skipping] unable to save file: {0:s} with error: {1:s}'.format(
                filename, exception))


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

    if self._process_vss:
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

  format_str = '[%(levelname)s] %(message)s'
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
