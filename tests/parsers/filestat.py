#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for filestat parser."""

import os
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

# pylint: disable=unused-import
from plaso.formatters import file_system as file_system_formatter
from plaso.parsers import filestat

from tests.parsers import test_lib


class FileStatTest(test_lib.ParserTestCase):
  """Tests for filestat parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = filestat.FileStatParser()

  def testTSKFile(self):
    """Read a file within an image file and make few tests."""
    test_file = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=15, location=u'/passwords.txt',
        parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, tsk_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The TSK file entry has 3 event objects.
    self.assertEqual(len(event_objects), 3)

    event_object = event_objects[0]

    expected_message = (
        u'TSK:/passwords.txt '
        u'Type: file')
    expected_message_short = u'/passwords.txt'
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

  def testZipFile(self):
    """Test a ZIP file."""
    test_file = self._GetTestFilePath([u'syslog.zip'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_ZIP, location=u'/syslog',
        parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, zip_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The ZIP file has 1 event object.
    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    expected_message = (
        u'ZIP:/syslog '
        u'Type: file')
    expected_message_short = u'/syslog'
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

  def testGzipFile(self):
    """Test a GZIP file."""
    test_file = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, gzip_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The gzip file has 1 event object.
    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    test_path = os.path.join(os.getcwd(), u'test_data', u'syslog.gz')
    expected_message = (
        u'GZIP:{0:s} '
        u'Type: file').format(test_path)
    expected_message_short = self._GetShortMessage(test_path)
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

  def testTarFile(self):
    """Test a TAR file."""
    test_file = self._GetTestFilePath([u'syslog.tar'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, tar_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The tar file has 1 event object.
    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    expected_message = (
        u'TAR:/syslog '
        u'Type: file')
    expected_message_short = u'/syslog'
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

  def testNestedFile(self):
    """Test a nested file."""
    test_file = self._GetTestFilePath([u'syslog.tgz'])
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
    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    expected_message = (
        u'TAR:/syslog '
        u'Type: file')
    expected_message_short = u'/syslog'
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

    test_file = self._GetTestFilePath([u'syslog.tgz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    event_queue_consumer = self._ParseFileByPathSpec(
        self._parser, gzip_path_spec)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The gzip file has 1 event object.
    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    test_path = os.path.join(os.getcwd(), u'test_data', u'syslog.tgz')
    expected_message = (
        u'GZIP:{0:s} '
        u'Type: file').format(test_path)
    expected_message_short = self._GetShortMessage(test_path)
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

  def testNestedTSK(self):
    """Test a nested TSK file."""
    test_file = self._GetTestFilePath([u'syslog_image.dd'])
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
    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    expected_message = (
        u'ZIP:/syslog '
        u'Type: file')
    expected_message_short = u'/syslog'
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
