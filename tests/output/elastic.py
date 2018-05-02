#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Elasticsearch output module."""

from __future__ import unicode_literals

import unittest

from plaso.output import elastic

from tests.output import test_lib


class ElasticSearchOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the Elasticsearch output module."""

  # TODO: test Close function
  # TODO: test SetServerInformation function
  # TODO: test SetFlushInterval function
  # TODO: test SetIndexName function
  # TODO: test SetDocType function
  # TODO: test SetRawFields function
  # TODO: test WriteEventBody function
  # TODO: test WriteHeader function


if __name__ == '__main__':
  unittest.main()
