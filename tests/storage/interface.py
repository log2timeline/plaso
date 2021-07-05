#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the sttribute container store interface."""

import unittest

from plaso.containers import events
from plaso.storage import interface

from tests.storage import test_lib


class BaseStoreTest(test_lib.StorageTestCase):
  """Tests for the attribute container store interface."""

  # pylint: disable=protected-access

  def testGetAttributeContainerNextSequenceNumber(self):
    """Tests the _GetAttributeContainerNextSequenceNumber function."""
    event_data_stream = events.EventDataStream()

    test_store = interface.BaseStore()

    sequence_number = test_store._GetAttributeContainerNextSequenceNumber(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(sequence_number, 1)

    sequence_number = test_store._GetAttributeContainerNextSequenceNumber(
        event_data_stream.CONTAINER_TYPE)
    self.assertEqual(sequence_number, 2)

  # TODO: add tests for _SetAttributeContainerNextSequenceNumber


if __name__ == '__main__':
  unittest.main()
