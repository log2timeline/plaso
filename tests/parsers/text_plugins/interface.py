#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the text plugins interface."""

import unittest

from tests.parsers import test_lib


class TextPluginTest(test_lib.ParserTestCase):
  """Tests for the text plugins interface."""

  # pylint: disable=protected-access

  # TODO: add tests for _GetMatchingLineStructure
  # TODO: add tests for _GetValueFromStructure
  # TODO: add tests for _ParseLines
  # TODO: add tests for _ParseLineStructure
  # TODO: add tests for _SetLineStructures
  # TODO: add tests for Process


if __name__ == '__main__':
  unittest.main()
