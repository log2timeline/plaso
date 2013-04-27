#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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

import glob
# TODO: move to ArgParser
from optparse import OptionParser

from plaso.classifier import classifier
from plaso.classifier import re2scanner
from plaso.classifier import scanner
from plaso.classifier import test_store


def main():
  usage = "Usage: %prog filename(s)"
  args_parser = OptionParser(usage)
  args_parser.add_option("-t", "--type", type="choice", action="store",
                         dest="scanner_type",
                         choices=["re2", "scan-tree", "scan_tree"],
                         default="re2", help="The scanner type")
  args_parser.add_option("-v", "--verbose", action="store_true",
                         dest="verbose", default=False,
                         help="Print verbose output")
  options, args = args_parser.parse_args()

  if options.verbose:
    logging.set_verbosity(logging.DEBUG)

  files_to_classify = []
  for input_glob in args:
    files_to_classify += glob.glob(input_glob)

  store = test_store.CreateSpecificationStore()

  if (options.scanner_type == "scan-tree" or
      options.scanner_type == "scan_tree"):
    scan = scanner.Scanner(store)
  else:
    if not options.scanner_type == "re2":
      print u"Unsupported scanner type defaulting to: re2"
    scan = re2scanner.RE2Scanner(store)
  classify = classifier.Classifier(scan)

  for input_filename in files_to_classify:
    classifications = classify.ClassifyFile(input_filename)

    print u"File: {0:s}".format(input_filename)
    if not classifications:
      print u"No classifications found."
    else:
      print u"Classifications:"
      for classification in classifications:
        print u"\tformat: {0:s}".format(
            classification.identifier)

    print u""


if __name__ == "__main__":
  main()
