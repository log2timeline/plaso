#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the analysis context."""

import unittest

from plaso.analysis import context
from plaso.analysis import test_lib
from plaso.lib import queue


class AnalysisContextTest(test_lib.AnalysisPluginTestCase):
  """Tests for the analysis context."""

  MAC_PATHS = [
      '/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions',
      ('/Users/dude/Libary/Application Data/Google/Chrome/Default/Extensions/'
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
    """Sets up the needed objects used throughout the test."""
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_report_queue = queue.SingleThreadedQueue()
    analysis_report_queue_producer = queue.AnalysisReportQueueProducer(
        analysis_report_queue)

    self._analysis_context = context.AnalysisContext(
        analysis_report_queue_producer, knowledge_base)

  def testGetPathSegmentSeparator(self):
    """Tests the GetPathSegmentSeparator function."""
    for path in self.MAC_PATHS:
      path_segment_separator = self._analysis_context.GetPathSegmentSeparator(
          path)
      self.assertEquals(path_segment_separator, u'/')

    for path in self.WIN_PATHS:
      path_segment_separator = self._analysis_context.GetPathSegmentSeparator(
          path)
      self.assertEquals(path_segment_separator, u'\\')

  def testGetUserPaths(self):
    """Tests the GetUserPaths function."""
    user_paths = self._analysis_context.GetUserPaths(self.MAC_USERS)
    self.assertEquals(
        set(user_paths.keys()), set([u'frank', u'dude', u'hans', u'root']))
    self.assertEquals(user_paths[u'frank'], u'/users/frank')
    self.assertEquals(user_paths[u'dude'], u'/users/dude')
    self.assertEquals(user_paths[u'hans'], u'/users/hans')
    self.assertEquals(user_paths[u'root'], u'/var/root')

    user_paths = self._analysis_context.GetUserPaths(self.WIN_USERS)
    self.assertEquals(set(user_paths.keys()), set([u'frank', u'dude']))
    self.assertEquals(user_paths[u'frank'], u'/users/frank')
    self.assertEquals(user_paths[u'dude'], u'/users/dude')

  def testGetUsernameFromPath(self):
    """Tests the GetUsernameFromPath function."""
    user_paths = self._analysis_context.GetUserPaths(self.MAC_USERS)

    username = self._analysis_context.GetUsernameFromPath(
        user_paths, self.MAC_PATHS[0], u'/')
    self.assertEquals(username, u'dude')

    username = self._analysis_context.GetUsernameFromPath(
        user_paths, self.MAC_PATHS[4], u'/')
    self.assertEquals(username, u'hans')

    username = self._analysis_context.GetUsernameFromPath(
        user_paths, self.WIN_PATHS[0], u'/')
    self.assertEquals(username, None)

    user_paths = self._analysis_context.GetUserPaths(self.WIN_USERS)

    username = self._analysis_context.GetUsernameFromPath(
        user_paths, self.WIN_PATHS[0], u'\\')
    self.assertEquals(username, u'dude')

    username = self._analysis_context.GetUsernameFromPath(
        user_paths, self.WIN_PATHS[2], u'\\')
    self.assertEquals(username, u'frank')

    username = self._analysis_context.GetUsernameFromPath(
        user_paths, self.MAC_PATHS[2], u'\\')
    self.assertEquals(username, None)


if __name__ == '__main__':
  unittest.main()
