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
"""This file contains tests for the format classifier classes."""

import os
import unittest

from plaso.classifier import classifier
from plaso.classifier import scanner
from plaso.classifier import test_lib


class ClassifierTest(unittest.TestCase):
  """Class to test Classifier."""

  def setUp(self):
    """Function to test the initialize function."""
    self._store = test_lib.CreateSpecificationStore()

    self._test_file1 = os.path.join('test_data', 'NTUSER.DAT')
    self._test_file2 = os.path.join('test_data', 'syslog.zip')

  def testClassifyFileWithScanner(self):
    """Function to test the classify file function."""
    test_scanner = scanner.Scanner(self._store)

    test_classifier = classifier.Classifier(test_scanner)
    classifications = test_classifier.ClassifyFile(self._test_file1)
    self.assertEqual(len(classifications), 1)

    # TODO: assert the contents of the classification.

    test_classifier = classifier.Classifier(test_scanner)
    classifications = test_classifier.ClassifyFile(self._test_file2)
    self.assertEqual(len(classifications), 1)

    # TODO: assert the contents of the classification.

  def testClassifyFileWithOffsetBoundScanner(self):
    """Function to test the classify file function."""
    test_scanner = scanner.OffsetBoundScanner(self._store)

    test_classifier = classifier.Classifier(test_scanner)
    classifications = test_classifier.ClassifyFile(self._test_file1)
    self.assertEqual(len(classifications), 1)

    # TODO: assert the contents of the classification.

    test_classifier = classifier.Classifier(test_scanner)
    classifications = test_classifier.ClassifyFile(self._test_file2)
    self.assertEqual(len(classifications), 1)

    # TODO: assert the contents of the classification.


if __name__ == "__main__":
  unittest.main()
