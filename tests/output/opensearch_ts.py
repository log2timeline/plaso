#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OpenSearchTimesketch output module."""

import unittest

from unittest.mock import MagicMock

from plaso.output import opensearch_ts
from plaso.output import shared_opensearch

from tests.output import test_lib


class TestOpenSearchTimesketchOutputModule(
    opensearch_ts.OpenSearchTimesketchOutputModule):
  """OpenSearchsearch output module for testing."""

  def _Connect(self):
    """Connects to an OpenSearch server."""
    self._client = MagicMock()


@unittest.skipIf(
    shared_opensearch.opensearchpy is None, 'missing opensearch-py')
class OpenSearchTimesketchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the OpenSearchTimesketch output module."""

  # pylint: disable=protected-access

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    output_mediator = self._CreateOutputMediator()
    output_module = TestOpenSearchTimesketchOutputModule(output_mediator)

    self.assertIsNone(output_module._client)

    output_module.WriteHeader()

    self.assertIsNotNone(output_module._client)


if __name__ == '__main__':
  unittest.main()
