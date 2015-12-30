#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis mediator."""

import unittest

from plaso.analysis import mediator
from plaso.engine import queue
from plaso.engine import single_process

from tests.analysis import test_lib


class AnalysisMediatorTest(test_lib.AnalysisPluginTestCase):
  """Tests for the analysis mediator."""

  MAC_PATHS = [
      '/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions',
      ('/Users/dude/Library/Application Data/Google/Chrome/Default/Extensions/'
       'apdfllckaahabafndbhieahigkjlhalf'),
      '/private/var/log/system.log',
      '/Users/frank/Library/Application Data/Google/Chrome/Default',
      '/Users/hans/Library/Application Data/Google/Chrome/Default',
      ('/Users/frank/Library/Application Data/Google/Chrome/Default/'
       'Extensions/pjkljhegncpnkpknbcohdijeoejaedia'),
      '/Users/frank/Library/Application Data/Google/Chrome/Default/Extensions',]

  WIN_PATHS = [
      'C:\\Users\\Dude\\SomeFolder\\Chrome\\Default\\Extensions',
      ('C:\\Users\\Dude\\SomeNoneStandardFolder\\Chrome\\Default\\Extensions\\'
       'hmjkmjkepdijhoojdojkdfohbdgmmhki'),
      ('\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'blpcfgokakmgnkcojhhkbfbldkacnbeo'),
      '\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions',
      ('\\Users\\frank\\AppData\\Local\\Google\\Chrome\\Extensions\\'
       'icppfcnhkcmnfdhfhphakoifcfokfdhg'),
      'C:\\Windows\\System32',
      '\\Stuff/with path separator\\Folder']

  MAC_USERS = [
      {u'name': u'root', u'path': u'/var/root', u'sid': u'0'},
      {u'name': u'frank', u'path': u'/Users/frank', u'sid': u'4052'},
      {u'name': u'hans', u'path': u'/Users/hans', u'sid': u'4352'},
      {u'name': u'dude', u'path': u'/Users/dude', u'sid': u'1123'}]

  WIN_USERS = [
      {u'name': u'dude', u'path': u'C:\\Users\\dude', u'sid': u'S-1'},
      {u'name': u'frank', u'path': u'C:\\Users\\frank', u'sid': u'S-2'}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_report_queue = single_process.SingleProcessQueue()
    analysis_report_queue_producer = queue.ItemQueueProducer(
        analysis_report_queue)

    self._analysis_mediator = mediator.AnalysisMediator(
        analysis_report_queue_producer, knowledge_base)

  def testGetPathSegmentSeparator(self):
    """Tests the GetPathSegmentSeparator function."""
    for path in self.MAC_PATHS:
      path_segment_separator = self._analysis_mediator.GetPathSegmentSeparator(
          path)
      self.assertEqual(path_segment_separator, u'/')

    for path in self.WIN_PATHS:
      path_segment_separator = self._analysis_mediator.GetPathSegmentSeparator(
          path)
      self.assertEqual(path_segment_separator, u'\\')

  def testGetUserPaths(self):
    """Tests the GetUserPaths function."""
    user_paths = self._analysis_mediator.GetUserPaths(self.MAC_USERS)
    self.assertEqual(
        set(user_paths.keys()), set([u'frank', u'dude', u'hans', u'root']))
    self.assertEqual(user_paths[u'frank'], u'/users/frank')
    self.assertEqual(user_paths[u'dude'], u'/users/dude')
    self.assertEqual(user_paths[u'hans'], u'/users/hans')
    self.assertEqual(user_paths[u'root'], u'/var/root')

    user_paths = self._analysis_mediator.GetUserPaths(self.WIN_USERS)
    self.assertEqual(set(user_paths.keys()), set([u'frank', u'dude']))
    self.assertEqual(user_paths[u'frank'], u'/users/frank')
    self.assertEqual(user_paths[u'dude'], u'/users/dude')

  def testGetUsernameFromPath(self):
    """Tests the GetUsernameFromPath function."""
    user_paths = self._analysis_mediator.GetUserPaths(self.MAC_USERS)

    username = self._analysis_mediator.GetUsernameFromPath(
        user_paths, self.MAC_PATHS[0], u'/')
    self.assertEqual(username, u'dude')

    username = self._analysis_mediator.GetUsernameFromPath(
        user_paths, self.MAC_PATHS[4], u'/')
    self.assertEqual(username, u'hans')

    username = self._analysis_mediator.GetUsernameFromPath(
        user_paths, self.WIN_PATHS[0], u'/')
    self.assertIsNone(username)

    user_paths = self._analysis_mediator.GetUserPaths(self.WIN_USERS)

    username = self._analysis_mediator.GetUsernameFromPath(
        user_paths, self.WIN_PATHS[0], u'\\')
    self.assertEqual(username, u'dude')

    username = self._analysis_mediator.GetUsernameFromPath(
        user_paths, self.WIN_PATHS[2], u'\\')
    self.assertEqual(username, u'frank')

    username = self._analysis_mediator.GetUsernameFromPath(
        user_paths, self.MAC_PATHS[2], u'\\')
    self.assertIsNone(username)


if __name__ == '__main__':
  unittest.main()
