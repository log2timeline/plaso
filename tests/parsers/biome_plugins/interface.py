#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple biome plugin interface."""
import abc
import unittest
import os

from plaso.parsers.biome_plugins import interface
from tests.parsers.biome_plugins import test_lib


class TestAppleBiomePlugin(interface.AppleBiomePlugin):
  """Apple biome plugin for test purposes."""

  NAME = 'test'
  DATA_FORMAT = 'Apple biome test file'

  _DEFINITION_FILE = os.path.join(
      'plaso', 'parsers', 'apple_biome.yaml')

  REQUIRED_SCHEMA = {
    '1': {'type': 'string'},
    '2': {'type': 'int'},
    '3': {'type': 'int'},
    '4': {'type': 'fixed64'},
    '5': {'type': 'fixed64'},
    '6': {'type': 'string'},
    '9': {'type': 'string'},
    '10': {'type': 'string'}}

  def __int__(self):
    """Initializes the test plugin."""
    super(TestAppleBiomePlugin, self).__init__()

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, biome_file=None, **unused_kwargs):
    """Extracts information from an Apple biome file. This is the main method
    that an Apple biome file plugin needs to implement.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      biome_file (Optional[AppleBiomeFile]): Apple biome file.

    Raises:
      ValueError: If the file_object value is missing.
    """


class AppleBiomeInterfaceTest(test_lib.AppleBiomeTestCase):
  """Tests for the Apple biome plugin interface."""

  def testCheckRequiredSchema(self):
    """Tests the CheckRequiredSchema function."""
    plugin = TestAppleBiomePlugin()

    biome_file = self._OpenAppleBiomeFile([
      'apple_biome', 'applaunch-segb'])

    raw_protobuf = biome_file.records[1].protobuf

    required_schema_present = plugin.CheckRequiredSchema(raw_protobuf)
    self.assertTrue(required_schema_present)


if __name__ == '__main__':
  unittest.main()
