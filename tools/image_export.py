#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import os
import logging

from plaso import preprocessors

from plaso.lib import collector_filter
from plaso.lib import errors
from plaso.lib import pfile
from plaso.lib import preprocess
from plaso.lib import putils
from plaso.lib import vss


def ExtractFiles(
    my_collector, filter_definition, export_path, fscache=None, prefix='',
    calc_md5=False, md5_dict=None):
  """Extracts files that match the filter.

  Args:
    my_collector: A collection object that can be used to locate files.
    filter_definition: This can be either a PathFilter protobuf,
    a path to a file with ASCII presentation of the protobuf or a list
    of entries, where each entry is a single path.
    export_path: The path to where the files should be stored.
    fscache: A filesystem cache object, if applicable.
    prefix: If the filename should be prepended by a prefix value.
    calc_md5: Boolean value indicating if a MD5 value should be returned.
    md5_dict: None, unless calc_md5 is set, then it should be a dict.

  Returns:
    None, unless calc_md5 is set then it returns a dict with MD5 sums.
  """
  col_fil = collector_filter.CollectionFilter(my_collector, filter_definition)

  if calc_md5:
    if md5_dict:
      md5s = md5_dict
    else:
      md5s = {}

  for pathspec_string in col_fil.GetPathSpecs():
    with pfile.OpenPFile(pathspec_string, fscache=fscache) as fh:
      directory = ''
      if '/' in fh.name:
        directory_string, _, filename = fh.name.rpartition('/')
        if directory_string:
          directory = os.path.join(export_path, *directory_string.split('/'))
      else:
        filename = fh.name

      if prefix:
        extracted_filename = '{}_{}'.format(prefix, filename)
      else:
        extracted_filename = filename

      if directory:
        if not os.path.isdir(directory):
          os.makedirs(directory)
      else:
        directory = export_path

      save_file = True
      if calc_md5:
        stat = fh.Stat()
        inode = stat.attributes.get('ino', 0)
        md5sum = CalculateHash(fh)
        if inode in md5s:
          if md5sum in md5s[inode]:
            save_file = False
          else:
            md5s[inode].append(md5sum)
        else:
          md5s[inode] = [md5sum]

      if save_file:
        putils.Pfile2File(fh, os.path.join(directory, extracted_filename))

  if calc_md5:
    return md5s


def CalculateHash(file_object):
  """Return a hash for a given file object."""
  md5 = hashlib.md5()
  file_object.seek(0)

  data = file_object.read(4098)
  while data:
    md5.update(data)
    data = file_object.read(4098)

  return md5.hexdigest()


def RunPreprocess(image_path, image_offset):
  """Preprocess an image and return back a collector and a fscache.

  Args:
    image_path: The path to the disk image to parse.
    image_offset: The sector offset into the volume where the partition starts.

  Returns:
    A tuple with three attributes, a collector, fileystem cache object and
    a pre processing object.
  """
  fscache = pfile.FilesystemCache()
  pre_obj = preprocess.PlasoPreprocess()

  # Start with a regular TSK collector.
  try:
    tsk_col = preprocess.TSKFileCollector(
        pre_obj, image_path, image_offset * 512)
  except errors.UnableToOpenFilesystem as e:
    raise RuntimeError('Unable to proceed, not an image file? [%s]' % e)

  plugin_list = preprocessors.PreProcessList(pre_obj, tsk_col)

  logging.info('Guessing OS')
  guessed_os = preprocess.GuessOS(tsk_col)
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

  return tsk_col, fscache, pre_obj


def RunExtraction(options, tsk_col, pre_obj, fscache):
  """Run the extraction process.

  This method runs the file extraction process on the image and
  potentially on every VSS if that is wanted.

  Args:
    options: A configuration object, something like an argparse object.
    tsk_col: A collector...
    pre_obj: Pre.
    fscache: A filesystem cache object.
  """
  # Save the regular files.
  ret_dict = ExtractFiles(
      tsk_col, options.filter, options.path, fscache=fscache,
      calc_md5=options.remove_duplicates)
  logging.info('Files extracted.')

  # Go through VSS if desired.
  if options.vss:
    logging.info('Extracting files from VSS.')
    vss_numbers = vss.GetVssStoreCount(options.image, options.offset * 512)
    for store_nr in range(0, vss_numbers):
      logging.info('Extracting files from VSS %d/%d', store_nr + 1, vss_numbers)
      vss_col = preprocess.VSSFileCollector(
          pre_obj, options.image, store_nr, options.offset * 512)
      ret_dict_back = ExtractFiles(
          vss_col, options.filter, options.path, fscache, 'vss_%d' % store_nr,
          calc_md5=options.remove_duplicates, md5_dict=ret_dict)
      ret_dict = ret_dict_back


def Main():
  """The main function, running the show."""
  arg_parser = argparse.ArgumentParser(
      description=('This is a simple collector designed to export files'
                   ' inside an image, both within a regular raw image as '
                   'well as inside a VSS. The tool uses a collection filter '
                   'that uses the same syntax as a targeted plaso filter.'),
      epilog='And that\'s how you export files, plaso style.')

  arg_parser.add_argument(
      '-v', '--vss', dest='vss', action='store_true', default=False,
      help='Indicate to the tool that we want to extract files from VSS too.')

  arg_parser.add_argument(
      '-o', '--offset', dest='offset', action='store', default=0, type=int,
      help='Offset in sectors into where the partition starts.')

  arg_parser.add_argument(
      '-w', '--write', dest='path', action='store', default='.', type=str,
      help='The directory in which extracted files should be stored in.')

  arg_parser.add_argument(
      '--include_duplicates', dest='include_duplicates', action='store_true',
      default=False, help=(
          'By default if VSS is turned on all files saved will have their'
          'MD5 sum calculated and compared to other files already saved '
          'with the same inode value. If the MD5 sum is the same the file '
          'does not get saved again. This option turns off that behavior '
          'so that all files will get stored, even if they are duplicates.'))

  arg_parser.add_argument(
      'image', action='store', metavar='IMAGE', default=None, type=str, help=(
          'The full path to the image file that we are about to extract files'
          ' from, it should be a raw image or another image that plaso '
          'supports.'))

  arg_parser.add_argument(
      'filter', action='store', metavar='FILTERFILE', type=str, help=(
          'Full path to the file that contains the collection filter, '
          'the file can use variables that are defined in preprocesing'
          ', just like any other log2timeline/plaso collection filter.'))

  options = arg_parser.parse_args()

  format_str = '[%(levelname)s] %(message)s'
  logging.basicConfig(level=logging.INFO, format=format_str)

  if not os.path.isfile(options.filter):
    raise RuntimeError('Unable to proceed, filter file does not exist.')
  if not os.path.isfile(options.image):
    raise RuntimeError('Unable to proceed, image file does not exist.')
  if not os.path.isdir(options.path):
    os.makedirs(options.path)

  if options.vss:
    if options.include_duplicates:
      options.remove_duplicates = False
    else:
      options.remove_duplicates = True
  else:
    options.remove_duplicates = False

  collector, fscache, pre_obj = RunPreprocess(options.image, options.offset)
  RunExtraction(options, collector, pre_obj, fscache)


if __name__ == '__main__':
  Main()
