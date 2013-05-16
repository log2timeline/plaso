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
"""This file contains tests for the format classifier classes."""
import os
import unittest

from plaso.classifier import classifier
from plaso.classifier import scanner
from plaso.classifier import test_store


class ClassifierTest(unittest.TestCase):
  """Class to test Classifier."""

  def setUp(self):
    self._store = test_store.CreateSpecificationStore()
    self._scanner = scanner.Scanner(self._store)

    self._input_filenames = [
        os.path.join("test_data", "NTUSER.DAT"),
        os.path.join("test_data", "syslog.zip")]

  def testClassifyFileScannerFull(self):
    """Function to test the ClassifyFile function with the scan tree scanner."""
    for input_filename in self._input_filenames:
      test_classifier = classifier.Classifier(self._scanner)
      classifications = test_classifier.ClassifyFile(input_filename)

      self.assertEqual(len(classifications), 1)

  def testClassifyFileScannerHeadTail(self):
    """Function to test the ClassifyFile function with the scan tree scanner."""
    for input_filename in self._input_filenames:
      test_classifier = classifier.Classifier(
          self._scanner, classifier.Classifier.HEAD_TAIL_SCAN)
      classifications = test_classifier.ClassifyFile(input_filename)

      self.assertEqual(len(classifications), 1)


if __name__ == "__main__":
  unittest.main()
