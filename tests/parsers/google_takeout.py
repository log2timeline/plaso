#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Google Takeout plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import google_takeout as _  # pylint: disable=unused-import
from plaso.parsers import czip # pylint: disable=unused-import
from plaso.parsers.czip_plugins import google_takeout # pylint: disable=unused-import

from tests import test_lib as shared_test_lib # pylint: disable=unused-import
from tests.parsers.czip_plugins import test_lib

class GoogleTakeoutTest(test_lib.CompoundZIPPluginTestCase):
  """Tests for the Google Takeout plugin."""

  # pylint: disable=protected-access

if __name__ == '__main__':
  unittest.main()
