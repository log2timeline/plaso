#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for filestat parser."""

import os
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.formatters import file_system  # pylint: disable=unused-import
from plaso.parsers import filestat

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class FileStatTest(test_lib.ParserTestCase):
  """Tests for filestat parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testTSKFile(self):
    """Read a file within an image file and make few tests."""
    parser = filestat.FileStatParser()

    test_file = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=15, location=u'/passwords.txt',
        parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(tsk_path_spec, parser)

    # The TSK file entry has 3 events.
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.file_size, 116)

    expected_message = (
        u'TSK:/passwords.txt '
        u'Type: file')
    expected_short_message = u'/passwords.txt'
    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.zip'])
  def testZipFile(self):
    """Test a ZIP file."""
    parser = filestat.FileStatParser()

    test_file = self._GetTestFilePath([u'syslog.zip'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_ZIP, location=u'/syslog',
        parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(zip_path_spec, parser)

    # The ZIP file has 1 event.
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.file_size, 1247)

    expected_message = (
        u'ZIP:/syslog '
        u'Type: file')
    expected_short_message = u'/syslog'
    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.gz'])
  def testGzipFile(self):
    """Test a GZIP file."""
    parser = filestat.FileStatParser()

    test_file = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    # The gzip file has 1 event.
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.file_size, 1247)

    test_path = os.path.join(os.getcwd(), u'test_data', u'syslog.gz')
    expected_message = (
        u'GZIP:{0:s} '
        u'Type: file').format(test_path)
    expected_short_message = self._GetShortMessage(test_path)
    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.tar'])
  def testTarFile(self):
    """Test a TAR file."""
    parser = filestat.FileStatParser()

    test_file = self._GetTestFilePath([u'syslog.tar'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(tar_path_spec, parser)

    # The tar file has 1 event.
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.file_size, 1247)

    expected_message = (
        u'TAR:/syslog '
        u'Type: file')
    expected_short_message = u'/syslog'
    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.tgz'])
  def testNestedFile(self):
    """Test a nested file."""
    parser = filestat.FileStatParser()

    test_file = self._GetTestFilePath([u'syslog.tgz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=gzip_path_spec)

    storage_writer = self._ParseFileByPathSpec(tar_path_spec, parser)

    # The tar file has 1 event.
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.file_size, 1247)

    expected_message = (
        u'TAR:/syslog '
        u'Type: file')
    expected_short_message = u'/syslog'
    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

    test_file = self._GetTestFilePath([u'syslog.tgz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    storage_writer = self._ParseFileByPathSpec(gzip_path_spec, parser)

    # The gzip file has 1 event.
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.file_size, 10240)

    test_path = os.path.join(os.getcwd(), u'test_data', u'syslog.tgz')
    expected_message = (
        u'GZIP:{0:s} '
        u'Type: file').format(test_path)
    expected_short_message = self._GetShortMessage(test_path)
    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_image.dd'])
  def testNestedTSK(self):
    """Test a nested TSK file."""
    parser = filestat.FileStatParser()

    test_file = self._GetTestFilePath([u'syslog_image.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_file)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK, inode=11, location=u'/logs/hidden.zip',
        parent=os_path_spec)
    zip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_ZIP, location=u'/syslog',
        parent=tsk_path_spec)

    storage_writer = self._ParseFileByPathSpec(zip_path_spec, parser)

    # The ZIP file has 1 events.
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.file_size, 1247)

    expected_message = (
        u'ZIP:/syslog '
        u'Type: file')
    expected_short_message = u'/syslog'
    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
