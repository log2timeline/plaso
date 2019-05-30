#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the formatter mediator object."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mediator

from tests import test_lib as shared_test_lib


class FormatterMediatorTest(shared_test_lib.BaseTestCase):
  """Tests for the formatter mediator object."""

  def testInitialization(self):
    """Tests the initialization."""
    formatter_mediator = mediator.FormatterMediator()
    self.assertIsNotNone(formatter_mediator)


if __name__ == '__main__':
  unittest.main()
