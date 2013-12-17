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

from plaso import preprocessors

from plaso.collector import factory as collector_factory
from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import preprocess
from plaso.lib import putils
from plaso.lib import queue
from plaso.pvfs import pfile
from plaso.pvfs import pvfs
from plaso.pvfs import vss


class ImageExtractor(object):
  """Class that implements the image extractor."""

  def __init__(self):
    """Initializes the image extractor object."""
    super(ImageExtractor, self).__init__()
    self._image_path = None
    self._image_offset = 0
    self._fscache = pvfs.FilesystemCache()
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

    self._pre_obj = preprocess.PlasoPreprocess()
    try:
      image_collector = collector_factory.GetImagePreprocessCollector(
          self._pre_obj, self._image_path, byte_offset=self._image_offset)

    except errors.UnableToOpenFilesystem as e:
      raise RuntimeError('Unable to proceed, not an image file? [%s]' % e)

    plugin_list = preprocessors.PreProcessList(
        self._pre_obj, image_collector)

    logging.info('Guessing OS')
    guessed_os = preprocess.GuessOS(image_collector)
    logging.info('OS: %s', guessed_os)

    logging.info('Running preprocess.')
    for weight in plugin_list.GetWeightList(guessed_os):
      for plugin in plugin_list.GetWeight(guessed_os, weight):
        try:
          plugin.Run()
        except errors.PreProcessFail as e:
          logging.warning(
              'Unable to run preprocessor: %s, reason: %s',
              plugin.__class__.__name__, e)

    logging.info('Preprocess done, saving files from image.')

    return image_collector

  def _ExtractFiles(self, image_collector, filter_expression, destination_path):
    """Extracts files that match the filter.

    Args:
      image_collector: The image collector object.
      filter_expression: String containing a collection filter expression.
      destination_path: The path where the extracted files should be stored.

    Returns:
      None, unless calc_md5 is set then it returns a dict with MD5 sums.
    """
    filter_object = collector_filter.CollectionFilter(
        image_collector, filter_expression)

    for path_spec in filter_object.GetPathSpecs():
      with pfile.OpenPFile(path_spec, fscache=self._fscache) as fh:
        # There will be issues on systems that use a different separator than a
        # forward slash. However a forward slash is always used in the pathspec.
        if os.path.sep != '/':
          fh.name = fh.name.replace('/', os.path.sep)
        FileSaver.SaveFile(fh, destination_path)

  def ExtractWithFilter(
      self, filter_expression, destination_path, process_vss=False,
      remove_duplicates=False):
    """Extracts files using a filter expression.

    This method runs the file extraction process on the image and
    potentially on every VSS if that is wanted.

    Args:
      filter_expression: String containing a collection filter expression.
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
    self._ExtractFiles(image_collector, filter_expression, destination_path)

    if process_vss:
      logging.info('Extracting files from VSS.')
      vss_numbers = vss.GetVssStoreCount(self._image_path, self._image_offset)

      for store_nr in range(0, vss_numbers):
        logging.info(
            'Extracting files from VSS %d/%d', store_nr + 1, vss_numbers)

        vss_collector = collector_factory.GetImagePreprocessCollector(
            self._pre_obj, self._image_path, byte_offset=self._image_offset,
            vss_store_number=store_nr)

        FileSaver.prefix = 'vss_%d' % store_nr
        self._ExtractFiles(vss_collector, filter_expression, destination_path)

  def ExtractWithExtensions(
       self, extensions, destination_path, process_vss=False,
       remove_duplicates=False):
    """Extracts files using extensions.

    Args:
      extensions: List of extensions.
      destination_path: The path where the extracted files should be stored.
      process_vss: Optional boolean value to indicate if VSS should be detected
                   and processed. The default is false.
      remove_duplicates: Optional boolean value to indicate if duplicates should
                         be detected and removed. The default is false.
    """
    if not os.path.isdir(destination_path):
      os.makedirs(destination_path)

    input_queue = queue.SingleThreadedQueue()
    output_queue = queue.SingleThreadedQueue()

    image_collector = collector_factory.GetImageCollector(
        input_queue, output_queue, self._image_path,
        byte_offset=self._image_offset, parse_vss=process_vss,
        fscache=self._fscache)

    image_collector.Collect()

    FileSaver.calc_md5 = remove_duplicates

    for path_spec_string in input_queue.PopItems():
      pathspec = event.EventPathSpec()
      pathspec.FromProtoString(path_spec_string)

      _, _, extension = pathspec.file_path.rpartition('.')
      if extension.lower() in extensions:
        fh = pfile.OpenPFile(pathspec, fscache=self._fscache)
        if getattr(pathspec, 'vss_store_number', None):
          FileSaver.prefix = 'vss_%d' % pathspec.vss_store_number + 1
        else:
          FileSaver.prefix = ''
        if os.path.sep != '/':
          fh.name = fh.name.replace('/', os.path.sep)

        FileSaver.SaveFile(fh, destination_path)


class FileSaver(object):
  """A simple class that is used to save files."""
  md5_dict = {}
  calc_md5 = False
  prefix = ''

  @classmethod
  def SaveFile(cls, fh, destination_path):
    """Take a filehandle and an export path and save the file."""
    directory = ''
    filename = ''
    if os.path.sep in fh.name:
      directory_string, _, filename = fh.name.rpartition(os.path.sep)
      if directory_string:
        directory = os.path.join(
            destination_path, *directory_string.split(os.path.sep))
    else:
      filename = fh.name

    if cls.prefix:
      extracted_filename = '{}_{}'.format(cls.prefix, filename)
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
      stat = fh.Stat()
      inode = stat.attributes.get('ino', 0)
      md5sum = CalculateHash(fh)
      if inode in cls.md5_dict:
        if md5sum in cls.md5_dict[inode]:
          save_file = False
        else:
          cls.md5_dict[inode].append(md5sum)
      else:
        cls.md5_dict[inode] = [md5sum]

    if save_file:
      try:
        putils.Pfile2File(fh, os.path.join(directory, extracted_filename))
      except IOError as e:
        logging.error(u'Unable to save file: {} [skipping]. Error {}'.format(
            fh.name, e))


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
    raise RuntimeError('Unable to proceed, image file does not exist.')

  if not (options.filter or options.extension_string):
    arg_parser.print_help()
    print ''
    logging.error('Neither extension string nor filter defined.')
    sys.exit(1)

  if options.filter:
    if not os.path.isfile(options.filter):
      arg_parser.print_help()
      print ''
      logging.error('Unable to proceed, filter file does not exist.')
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
        options.path, options.filter, 
        process_vss=options.vss,
        remove_duplicates=options.remove_duplicates)

  if options.extension_string:
    extensions = [x.strip() for x in options.extension_string.split(',')]

    image_extractor.ExtractWithExtensions(
        extensions, options.path, process_vss=options.vss,
        remove_duplicates=options.remove_duplicates)
    logging.info('Files based on extension extracted.')


if __name__ == '__main__':
  Main()
