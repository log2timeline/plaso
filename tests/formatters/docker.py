#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Docker JSON event formatters."""

import unittest

from plaso.formatters import docker

from tests.formatters import test_lib


class DockerJSONFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Docker JSON event formatters."""

  def testInitializations(self):
    """Tests the initialization of the formatters."""
    event_formatter = docker.DockerBaseEventFormatter()
    self.assertIsNotNone(event_formatter)

    event_formatter1 = docker.DockerContainerEventFormatter()
    self.assertIsNotNone(event_formatter1)

    event_formatter2 = docker.DockerContainerLogEventFormatter()
    self.assertIsNotNone(event_formatter2)

    event_formatter3 = docker.DockerLayerEventFormatter()
    self.assertIsNotNone(event_formatter3)


  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""

    event_formatter = docker.DockerBaseEventFormatter()

    expected_attribute_names = []

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

    event_formatter1 = docker.DockerContainerEventFormatter()

    expected_attribute_names = [u'action',
                                u'container_id',
                                u'container_name']

    self._TestGetFormatStringAttributeNames(
        event_formatter1, expected_attribute_names)

    event_formatter2 = docker.DockerContainerLogEventFormatter()

    expected_attribute_names = [u'container_id',
                                u'log_line',
                                u'log_source']

    self._TestGetFormatStringAttributeNames(
        event_formatter2, expected_attribute_names)

    event_formatter3 = docker.DockerLayerEventFormatter()

    expected_attribute_names = [u'command',
                                u'layer_id']

    self._TestGetFormatStringAttributeNames(
        event_formatter3, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
