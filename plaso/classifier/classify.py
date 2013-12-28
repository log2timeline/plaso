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
"""This file contains a small classify test program."""

import argparse
import glob
import logging

from plaso.classifier import classifier
from plaso.classifier import scanner
from plaso.classifier import test_lib


def Main():
  args_parser = argparse.ArgumentParser(
      decription='Classify test program.')

  args_parser.add_argument(
      '-t', '--type', type='choice', metavar='TYPE', action='store',
      dest='scanner_type', choices=['scan-tree', 'scan_tree'],
      default='scan-tree', help='The scanner type')

  args_parser.add_argument(
      '-v', '--verbose', action='store_true', dest='verbose', default=False,
      help='Print verbose output')

  args_parser.add_argument(
      'filenames', nargs='+', action='store', metavar='FILENAMES',
      default=None, help='The input filename(s) to classify.')

  options = args_parser.parse_args()

  if options.verbose:
    logging.set_verbosity(logging.DEBUG)

  files_to_classify = []
  for input_glob in options.filenames:
    files_to_classify += glob.glob(input_glob)

  store = test_lib.CreateSpecificationStore()

  if options.scanner_type not in ['scan-tree', 'scan_tree']:
    print u'Unsupported scanner type defaulting to: scan-tree'

  scan = scanner.Scanner(store)
  classify = classifier.Classifier(scan)

  for input_filename in files_to_classify:
    classifications = classify.ClassifyFile(input_filename)

    print u'File: {0:s}'.format(input_filename)
    if not classifications:
      print u'No classifications found.'
    else:
      print u'Classifications:'
      for classification in classifications:
        print u'\tformat: {0:s}'.format(classification.identifier)

    print u''


if __name__ == '__main__':
  Main()
