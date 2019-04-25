#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Docker JSON event formatters."""

from __future__ import unicode_literals

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

    expected_attribute_names = ['action',
                                'container_id',
                                'container_name']

    self._TestGetFormatStringAttributeNames(
        event_formatter1, expected_attribute_names)

    event_formatter2 = docker.DockerContainerLogEventFormatter()

    expected_attribute_names = ['container_id',
                                'log_line',
                                'log_source']

    self._TestGetFormatStringAttributeNames(
        event_formatter2, expected_attribute_names)

    event_formatter3 = docker.DockerLayerEventFormatter()

    expected_attribute_names = ['command',
                                'layer_id']

    self._TestGetFormatStringAttributeNames(
        event_formatter3, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
