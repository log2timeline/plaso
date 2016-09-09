#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the single process processing engine."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.containers import sessions
from plaso.engine import single_process
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib


class SingleProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the single process engine object."""

  # pylint: disable=protected-access

  def testProcessSources(self):
    """Tests the ProcessSources function."""
    test_engine = single_process.SingleProcessEngine()
    resolver_context = context.Context()
    session = sessions.Session()

    source_path = os.path.join(self._TEST_DATA_PATH, u'ímynd.dd')
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_engine.PreprocessSources([source_path_spec])

    storage_writer = fake_storage.FakeStorageWriter(session)

    test_engine.ProcessSources(
        [source_path_spec], storage_writer, resolver_context,
        parser_filter_expression=u'filestat')

    self.assertEqual(len(storage_writer.events), 15)


if __name__ == '__main__':
  unittest.main()
