#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

import unittest

from plaso.output import mediator


class OutputMediatorTest(unittest.TestCase):
  """Tests for the output mediator object."""

  def testInitialization(self):
    """Tests the initialization."""
    output_mediator = mediator.OutputMediator(None, None)
    self.assertNotEqual(output_mediator, None)

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
