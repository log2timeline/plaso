#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the attribute container manager."""

import unittest

from plaso.containers import events
from plaso.containers import manager

from tests import test_lib as shared_test_lib
from tests.containers import test_lib


class AttributeContainersManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the attribute container manager."""

  def testCreateAttributeContainer(self):
    """Tests the CreateAttributeContainer function."""
    attribute_container = (
        manager.AttributeContainersManager.CreateAttributeContainer('event'))
    self.assertIsNotNone(attribute_container)

    with self.assertRaises(ValueError):
      manager.AttributeContainersManager.CreateAttributeContainer('bogus')

  def testGetContainerTypes(self):
    """Tests the GetContainerTypes function."""
    container_types = manager.AttributeContainersManager.GetContainerTypes()
    self.assertIn('event', container_types)

  def testGetSchema(self):
    """Tests the GetSchema function."""
    schema = manager.AttributeContainersManager.GetSchema('event')
    self.assertIsNotNone(schema)
    self.assertEqual(schema, events.EventObject.SCHEMA)

    with self.assertRaises(ValueError):
      manager.AttributeContainersManager.GetSchema('bogus')

  def testAttributeContainerRegistration(self):
    """Tests the Register and DeregisterAttributeContainer functions."""
    # pylint: disable=protected-access
    number_of_classes = len(
        manager.AttributeContainersManager._attribute_container_classes)

    manager.AttributeContainersManager.RegisterAttributeContainer(
        test_lib.TestAttributeContainer)
    self.assertEqual(
        len(manager.AttributeContainersManager._attribute_container_classes),
        number_of_classes + 1)

    with self.assertRaises(KeyError):
      manager.AttributeContainersManager.RegisterAttributeContainer(
          test_lib.TestAttributeContainer)

    manager.AttributeContainersManager.DeregisterAttributeContainer(
        test_lib.TestAttributeContainer)
    self.assertEqual(
        len(manager.AttributeContainersManager._attribute_container_classes),
        number_of_classes)


if __name__ == '__main__':
  unittest.main()
