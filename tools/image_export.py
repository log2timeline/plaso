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
"""A simple script to export files out of an image."""

import argparse
import hashlib
import logging
import os
import sys

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso import preprocessors
from plaso.collector import collector
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import preprocess_interface
from plaso.lib import queue


class ImageExtractor(object):
  """Class that implements the image extractor."""

  def __init__(self):
    """Initializes the image extractor object."""
    super(ImageExtractor, self).__init__()
    self._image_path = None
    self._image_offset = 0
    self._image_collector = None
    self._pre_obj = None

  def Open(self, image_path, sector_offset=0):
    """Opens the image.

    Args:
      image_path: The path to the disk image to parse.
      sector_offset: Option offset in sectors into the image where the partition
                     containing the file system starts. The default is 0.
    """
    self._image_path = image_path
    self._image_offset = sector_offset * 512

  def _Preprocess(self):
    """Preprocesses the image.

    Returns:
      The image collector object.
    """
    if self._pre_obj is not None:
      return

    self._pre_obj = event.PreprocessObject()

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=self._image_path)

    if self._image_offset > 0:
      volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
        start_offset=self._image_offset, parent=os_path_spec)
    else:
      volume_path_spec = os_path_spec

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    image_collector = collector.GenericPreprocessCollector(
        self._pre_obj, self._image_path, path_spec)

    plugin_list = preprocessors.PreProcessList(self._pre_obj)

    logging.info(u'Guessing OS')
    guessed_os = preprocess_interface.GuessOS(image_collector)
    logging.info(u'OS: {0:s}'.format(guessed_os))

    logging.info(u'Running preprocess.')
    for weight in plugin_list.GetWeightList(guessed_os):
      for plugin in plugin_list.GetWeight(guessed_os, weight):
        try:
          plugin.Run(image_collector)
        except errors.PreProcessFail as exception:
          logging.warning(
              u'Unable to run preprocessor: {0:s} with error: {1:s}'.format(
                  plugin.__class__.__name__, exception))

    logging.info(u'Preprocess done, saving files from image.')

    return image_collector

  def ExtractWithFilter(
      self, filter_file_path, destination_path, process_vss=False,
      remove_duplicates=False):
    """Extracts files using a filter expression.

    This method runs the file extraction process on the image and
    potentially on every VSS if that is wanted.

    Args:
      filter_file_path: The path of the file that contains the filter
                        expressions.
      destination_path: The path where the extracted files should be stored.
      process_vss: Optional boolean value to indicate if VSS should be detected
                   and processed. The default is false.
      remove_duplicates: Optional boolean value to indicate if duplicates should
                         be detected and removed. The default is false.
    """
    if self._pre_obj is None:
      image_collector = self._Preprocess()

    if not os.path.isdir(destination_path):
      os.makedirs(destination_path)

    # Save the regular files.
    FileSaver.calc_md5 = remove_duplicates
    filter_object = collector.BuildCollectionFilterFromFile(filter_file_path)

    for path_spec in image_collector.GetPathSpecs(filter_object):
      FileSaver.WriteFile(path_spec, destination_path)

    if process_vss:
      logging.info(u'Extracting files from VSS.')
      os_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_OS, location=self._image_path)

      if self._image_offset > 0:
        volume_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
          start_offset=self._image_offset, parent=os_path_spec)
      else:
        volume_path_spec = os_path_spec

      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
          parent=volume_path_spec)

      vss_file_entry = path_spec_resolver.Resolver.OpenFileEntry(vss_path_spec)

      number_of_vss = vss_file_entry.number_of_sub_file_entries

      for store_index in range(0, number_of_vss):
        logging.info(u'Extracting files from VSS {0:d} out of {1:d}'.format(
            store_index + 1, number_of_vss))

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_VSHADOW, store_index=store_index,
            parent=volume_path_spec)
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
            parent=path_spec)

        vss_collector = collector.GenericPreprocessCollector(
            self._pre_obj, self._image_path, path_spec)

        filename_prefix = 'vss_{0:d}'.format(store_index)
        filter_object = collector.BuildCollectionFilterFromFile(
            filter_file_path)

        for path_spec in vss_collector.GetPathSpecs(filter_object):
          FileSaver.WriteFile(
              path_spec, destination_path, filename_prefix=filename_prefix)

  def ExtractWithExtensions(
       self, extensions, destination_path, remove_duplicates=False):
    """Extracts files using extensions.

    Args:
      extensions: a list of extensions.
      destination_path: the path where the extracted files should be stored.
      remove_duplicates: optional boolean value to indicate if duplicates should
                         be detected and removed. The default is false.
    """
    if not os.path.isdir(destination_path):
      os.makedirs(destination_path)

    input_queue = queue.SingleThreadedQueue()
    output_queue = queue.SingleThreadedQueue()
    output_producer = queue.EventObjectQueueProducer(output_queue)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
         dfvfs_definitions.TYPE_INDICATOR_OS, location=self._source_path)

    if self._image_offset > 0:
      volume_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
          start_offset=self._byte_offset, parent=os_path_spec)
    else:
      volume_path_spec = os_path_spec

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    image_collector = collector.Collector(
        input_queue, output_producer, self._image_path, path_spec)

    image_collector.Collect()

    FileSaver.calc_md5 = remove_duplicates

    input_queue_consumer = ImageExtractorQueueConsumer(
        input_queue, extensions, destination_path)
    input_queue_consumer.ConsumePathSpecs()


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
      inode = stat.attributes.get('ino', 0)
      md5sum = CalculateHash(file_entry)
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


def CalculateHash(file_object):
  """Return a hash for a given file object."""
  md5 = hashlib.md5()
  file_object.seek(0)

  data = file_object.read(4098)
  while data:
    md5.update(data)
    data = file_object.read(4098)

  return md5.hexdigest()


def Main():
  """The main function, running the show."""
  arg_parser = argparse.ArgumentParser(
      description=(
          'This is a simple collector designed to export files inside an '
          'image, both within a regular RAW image as well as inside a VSS. '
          'The tool uses a collection filter that uses the same syntax as a '
          'targeted plaso filter.'),
      epilog='And that\'s how you export files, plaso style.')

  arg_parser.add_argument(
      '-v', '--vss', dest='vss', action='store_true', default=False,
      help='Also extract files from VSS.')

  arg_parser.add_argument(
      '-o', '--offset', dest='offset', action='store', default=0, type=int,
      help='Offset in sectors into where the partition starts.')

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

  arg_parser.add_argument(
      'image', action='store', metavar='IMAGE', default=None, type=str, help=(
          'The full path to the image file that we are about to extract files '
          'from, it should be a raw image or another image that plaso '
          'supports.'))

  options = arg_parser.parse_args()

  format_str = '[%(levelname)s] %(message)s'
  logging.basicConfig(level=logging.INFO, format=format_str)

  if not os.path.isfile(options.image):
    raise RuntimeError(u'Unable to proceed, image file does not exist.')

  if not (options.filter or options.extension_string):
    arg_parser.print_help()
    print ''
    logging.error(u'Neither extension string nor filter defined.')
    sys.exit(1)

  if options.filter:
    if not os.path.isfile(options.filter):
      arg_parser.print_help()
      print ''
      logging.error(u'Unable to proceed, filter file does not exist.')
      sys.exit(1)

  if not options.vss:
    options.remove_duplicates = False
  elif options.include_duplicates:
    options.remove_duplicates = False
  else:
    options.remove_duplicates = True

  image_extractor = ImageExtractor()
  image_extractor.Open(options.image, sector_offset=options.offset)

  # The option of running both options.
  if options.filter:
    image_extractor.ExtractWithFilter(
        options.filter, options.path, process_vss=options.vss,
        remove_duplicates=options.remove_duplicates)

  if options.extension_string:
    extensions = [x.strip() for x in options.extension_string.split(',')]

    image_extractor.ExtractWithExtensions(
        extensions, options.path, remove_duplicates=options.remove_duplicates)
    logging.info(u'Files based on extension extracted.')


if __name__ == '__main__':
  Main()
