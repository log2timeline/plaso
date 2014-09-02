#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""Tests for filestat parser."""

import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

# pylint: disable=unused-import
from plaso.formatters import filestat as filestat_formatter
from plaso.parsers import filestat
from plaso.parsers import test_lib


class FileStatTest(test_lib.ParserTestCase):
  """Tests for filestat parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = filestat.FileStatParser()

  def testTSKFile(self):
    """Read a file within an image file and make few tests."""
    test_file = self._GetTestFilePath(['image.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=15, location=u'/passwords.txt',
        parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, tsk_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The TSK file entry has 3 event objects.
    self.assertEquals(len(event_objects), 3)

  def testZipFile(self):
    """Test a ZIP file."""
    test_file = self._GetTestFilePath(['syslog.zip'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_ZIP, location=u'/syslog',
        parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, zip_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The ZIP file has 1 event object.
    self.assertEquals(len(event_objects), 1)

  def testGzipFile(self):
    """Test a GZIP file."""
    test_file = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, gzip_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The gzip file has 1 event object.
    self.assertEquals(len(event_objects), 1)

  def testTarFile(self):
    """Test a TAR file."""
    test_file = self._GetTestFilePath(['syslog.tar'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, tar_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The tar file has 1 event object.
    self.assertEquals(len(event_objects), 1)

  def testNestedFile(self):
    """Test a nested file."""
    test_file = self._GetTestFilePath(['syslog.tgz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=gzip_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, tar_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The tar file has 1 event object.
    self.assertEquals(len(event_objects), 1)

    test_file = self._GetTestFilePath(['syslog.tgz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, gzip_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The gzip file has 1 event object.
    self.assertEquals(len(event_objects), 1)

  def testNestedTSK(self):
    """Test a nested TSK file."""
    test_file = self._GetTestFilePath(['syslog_image.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=11, location=u'/logs/hidden.zip',
        parent=os_path_spec)
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_ZIP, location=u'/syslog',
        parent=tsk_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, zip_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The ZIP file has 1 event objects.
    self.assertEquals(len(event_objects), 1)


if __name__ == '__main__':
  unittest.main()
