#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the storage reader."""

import unittest

from acstore.containers import interface as containers_interface

from plaso.containers import event_sources
from plaso.storage import reader
from plaso.storage.fake import fake_store

from tests.storage import test_lib


class StorageReaderTest(test_lib.StorageTestCase):
  """Tests for the storage reader."""

  # pylint: disable=protected-access

  def testInitialization(self):
    """Tests the __init__ function."""
    test_reader = reader.StorageReader()
    self.assertIsNotNone(test_reader)

  # TODO: add tests for __enter__ and __exit__
  # TODO: add tests for Close

  def testGetAttributeContainerByIdentifier(self):
    """Tests the GetAttributeContainerByIdentifier function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()
    test_reader._store.Open()

    try:
      event_source = event_sources.EventSource()
      test_reader._store.AddAttributeContainer(event_source)

      test_identifier = event_source.GetIdentifier()
      test_container = test_reader.GetAttributeContainerByIdentifier(
          event_source.CONTAINER_TYPE, test_identifier)
      self.assertIsNotNone(test_container)

      test_identifier = containers_interface.AttributeContainerIdentifier(
          name=event_source.CONTAINER_TYPE, sequence_number=99)
      test_container = test_reader.GetAttributeContainerByIdentifier(
          event_source.CONTAINER_TYPE, test_identifier)
      self.assertIsNone(test_container)

    finally:
      test_reader._store.Close()

  def testGetAttributeContainerByIndex(self):
    """Tests the GetAttributeContainerByIndex function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()
    test_reader._store.Open()

    try:
      event_source = event_sources.EventSource()
      test_reader._store.AddAttributeContainer(event_source)

      test_container = test_reader.GetAttributeContainerByIndex(
          event_source.CONTAINER_TYPE, 0)
      self.assertIsNotNone(test_container)

      test_container = test_reader.GetAttributeContainerByIndex(
          event_source.CONTAINER_TYPE, 99)
      self.assertIsNone(test_container)

    finally:
      test_reader._store.Close()

  def testGetAttributeContainers(self):
    """Tests the GetAttributeContainers function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()
    test_reader._store.Open()

    try:
      event_source = event_sources.EventSource()
      test_reader._store.AddAttributeContainer(event_source)

      test_generator = test_reader.GetAttributeContainers(
          event_source.CONTAINER_TYPE)
      test_containers = list(test_generator)
      self.assertEqual(len(test_containers), 1)

    finally:
      test_reader._store.Close()

  def testGetFormatVersion(self):
    """Tests the GetFormatVersion function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()

    format_version = test_reader.GetFormatVersion()
    self.assertIsNone(format_version)

  def testGetNumberOfAttributeContainers(self):
    """Tests the GetNumberOfAttributeContainers function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()
    test_reader._store.Open()

    try:
      event_source = event_sources.EventSource()
      test_reader._store.AddAttributeContainer(event_source)

      number_of_containers = test_reader.GetNumberOfAttributeContainers(
          event_source.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

    finally:
      test_reader._store.Close()

  def testGetSerializationFormat(self):
    """Tests the GetSerializationFormat function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()

    serialization_format = test_reader.GetSerializationFormat()
    self.assertIsNone(serialization_format)

  # TODO: add tests for GetSessions
  # TODO: add tests for GetSortedEvents

  def testHasAttributeContainers(self):
    """Tests the HasAttributeContainers function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()
    test_reader._store.Open()

    try:
      event_source = event_sources.EventSource()
      test_reader._store.AddAttributeContainer(event_source)

      result = test_reader.HasAttributeContainers(event_source.CONTAINER_TYPE)
      self.assertTrue(result)

    finally:
      test_reader._store.Close()

  def testSetSerializersProfiler(self):
    """Tests the SetSerializersProfiler function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()

    test_reader.SetSerializersProfiler(None)

  def testSetStorageProfiler(self):
    """Tests the SetStorageProfiler function."""
    test_reader = reader.StorageReader()
    test_reader._store = fake_store.FakeStore()

    test_reader.SetStorageProfiler(None)


if __name__ == '__main__':
  unittest.main()
