#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
import os
import logging

from plaso import preprocessors

from plaso.lib import collector_filter
from plaso.lib import event
from plaso.lib import errors
from plaso.lib import pfile
from plaso.lib import preprocess
from plaso.lib import putils
from plaso.lib import vss


def ExtractFiles(my_collector, filter_file, fscache, export_path, prefix=''):
  """Extracts files that match the filter."""
  col_fil = collector_filter.CollectionFilter(my_collector, filter_file)

  for pathspec_string in col_fil.GetPathSpecs():
    with pfile.OpenPFile(pathspec_string, fscache=fscache) as fh:
      # TODO: Add support for folder structure.
      if '/' in fh.name:
        filename = fh.name.split('/')[-1]
      else:
        filename = fh.name

      if prefix:
        extracted_filename = '{}_{}'.format(prefix, filename)
      else:
        extracted_filename = filename

      putils.Pfile2File(fh, os.path.join(export_path, extracted_filename))


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
    raise RuntimeError('Unable to proceed, write path does not exist.')

  fscache = pfile.FilesystemCache()
  pre_obj = preprocess.PlasoPreprocess()

  # Start with a regular TSK collector.
  try:
    tsk_col = preprocess.TSKFileCollector(
        pre_obj, options.image, options.offset * 512)
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
  # Save the regular files.
  ExtractFiles(tsk_col, options.filter, fscache, options.path)
  logging.info('Files extracted.')

  # Go through VSS if desired.
  if options.vss:
    logging.info('Extracting files from VSS.')
    vss_numbers = vss.GetVssStoreCount(options.image, options.offset * 512)
    for store_nr in range(0, vss_numbers):
      logging.info('Extracting files from VSS %d/%d', store_nr + 1, vss_numbers)
      vss_col = preprocess.VSSFileCollector(
          pre_obj, options.image, store_nr, options.offset * 512)
      ExtractFiles(
          vss_col, options.filter, fscache, options.path, 'vss_%d' % store_nr)


if __name__ == '__main__':
  Main()
