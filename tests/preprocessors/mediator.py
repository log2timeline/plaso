#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the preprocess mediator."""

import unittest

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
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.PreprocessMediator(
        session, storage_writer, knowledge_base_object)

    storage_writer.Open()

    parser_mediator.ProducePreprocessingWarning('test_plugin', 'test message')


if __name__ == '__main__':
  unittest.main()
