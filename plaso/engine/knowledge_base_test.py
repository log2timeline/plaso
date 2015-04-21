#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the knowledge base."""

import unittest

from plaso.engine import knowledge_base


class KnowledgeBaseTest(unittest.TestCase):
  """Tests for the knowledge base."""

  def testGetSetValue(self):
    """Tests the GetValue and SetValue functions."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    expected_value = u'test value'
    knowledge_base_object.SetValue(u'Test', expected_value)

    value = knowledge_base_object.GetValue(u'Test')
    self.assertEqual(value, expected_value)

    value = knowledge_base_object.GetValue(u'tEsT')
    self.assertEqual(value, expected_value)

    value = knowledge_base_object.GetValue(u'Bogus')
    self.assertEqual(value, None)


if __name__ == '__main__':
  unittest.main()
