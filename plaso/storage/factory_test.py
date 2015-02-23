#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the storage factory."""

import unittest

from plaso.storage import factory


class TestStorage(object):
  """This is a test storage that does not work."""

  NAME = u'teststorage'
  DESCRIPTION = u'This is a test storage object.'


class StorageFactoryTest(unittest.TestCase):
  """Tests for the storage factory."""

  def testStorageRegistration(self):
    """Tests the RegisterStorage and DeregisterStorage functions."""
    # pylint: disable=protected-access
    number_of_storages = len(factory.StorageFactory._storage_classes)

    factory.StorageFactory.RegisterStorage(TestStorage)

    self.assertEquals(
        len(factory.StorageFactory._storage_classes),
        number_of_storages + 1)

    with self.assertRaises(KeyError):
      factory.StorageFactory.RegisterStorage(TestStorage)

    factory.StorageFactory.DeregisterStorage(TestStorage)
    self.assertEquals(
        len(factory.StorageFactory._storage_classes),
        number_of_storages)

  def testGetAllTypeIndicators(self):
    """Test the GetAllTypeIndicators function."""
    factory.StorageFactory.RegisterStorage(TestStorage)

    indicators = factory.StorageFactory.GetAllTypeIndicators()

    self.assertIn(u'teststorage', indicators)
    factory.StorageFactory.DeregisterStorage(TestStorage)

  def testNewStorage(self):
    """Test the NewStorage function."""
    factory.StorageFactory.RegisterStorage(TestStorage)

    storage_obj = factory.StorageFactory.NewStorage(
        TestStorage.NAME)

    # TODO: When the test storage has been implemented, after
    # the new storage interface has been designed, make this a
    # more full fledged test.
    self.assertEqual(storage_obj.NAME, TestStorage.NAME)
    self.assertTrue(isinstance(storage_obj, TestStorage))

    with self.assertRaises(ValueError):
      factory.StorageFactory.NewStorage(1234)

    factory.StorageFactory.DeregisterStorage(TestStorage)

    with self.assertRaises(KeyError):
      factory.StorageFactory.DeregisterStorage(TestStorage)


if __name__ == '__main__':
  unittest.main()
