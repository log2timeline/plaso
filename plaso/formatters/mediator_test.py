#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the formatter mediator object."""

import unittest

from plaso.formatters import mediator


class FormatterMediatorTest(unittest.TestCase):
  """Tests for the formatter mediator object."""

  def testInitialization(self):
    """Tests the initialization."""
    formatter_mediator = mediator.FormatterMediator()
    self.assertNotEqual(formatter_mediator, None)


if __name__ == '__main__':
  unittest.main()
