#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.storage import fake_storage

from tests.parsers import test_lib


class ParsersMediatorTest(test_lib.ParserTestCase):
  """Tests for the parsers mediator."""

  def testGetDisplayName(self):
    """Tests the GetDisplayName function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(
        storage_writer, knowledge_base_values=None)

    with self.assertRaises(ValueError):
      _ = parsers_mediator.GetDisplayName(file_entry=None)

    test_path = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'OS:{0:s}'.format(test_path)
    self.assertEqual(display_name, expected_display_name)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'GZIP:{0:s}'.format(test_path)
    self.assertEqual(display_name, expected_display_name)

    test_path = self._GetTestFilePath([u'vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    vshadow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/vss2',
        store_index=1, parent=qcow_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=35, location=u'/syslog.gz',
        parent=vshadow_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'VSS2:TSK:/syslog.gz'
    self.assertEqual(display_name, expected_display_name)

    parsers_mediator.SetTextPrepend(u'C:')
    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)
    expected_display_name = u'VSS2:TSK:C:/syslog.gz'
    self.assertEqual(display_name, expected_display_name)

    # TODO: add test with relative path.

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
