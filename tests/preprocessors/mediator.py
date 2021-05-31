#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the preprocess mediator."""

import unittest

from dfvfs.path import fake_path_spec

from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.preprocessors import mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class PreprocessMediatorTest(shared_test_lib.BaseTestCase):
  """Tests for the preprocess mediator."""

  def testProducePreprocessingWarning(self):
    """Tests the ProducePreprocessingWarning method."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.PreprocessMediator(
        storage_writer, knowledge_base_object)

    storage_writer.Open()

    path_spec = fake_path_spec.FakePathSpec(location='/')
    parser_mediator.ProducePreprocessingWarning(
        'test_plugin', path_spec, 'test message')


if __name__ == '__main__':
  unittest.main()
