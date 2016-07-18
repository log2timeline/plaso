#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin."""
import unittest

import mock
from dfvfs.path import fake_path_spec

from plaso.analysis import nsrlsvr
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.lib import timelib
from plaso.parsers import pe

from tests.analysis import test_lib

class MockNsrlsvrSocket(object):
  """Mock socket object for testing."""

  def recv(self):
    return u'OK'

  def sendall(self):
    return

  def connect(self):
    pass

class NsrlSvrTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Viper analysis plugin."""
  EVENT_1_HASH = (
      u'2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')
  TEST_EVENTS = [{
      u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
      u'sha256_hash': EVENT_1_HASH,
      u'uuid': u'8'}]


  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch(
        'socket.create_connection', self._MockReply)
    self.requests_patcher.start()


  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def _MockReply(self):