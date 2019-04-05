#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the KML output module."""

from __future__ import unicode_literals

import os
import sys
import unittest

from plaso.output import kml

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class KMLOutputTest(test_lib.OutputModuleTestCase):
  """Tests for the KML output module."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    output_mediator = self._CreateOutputMediator()
    self._output_writer = cli_test_lib.TestOutputWriter()
    self._output_module = kml.KMLOutputModule(output_mediator)
    self._output_module.SetOutputWriter(self._output_writer)
    self._event_object = test_lib.TestEventObject()

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    expected_header = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>')

    self._output_module.WriteHeader()

    header = self._output_writer.ReadOutput()
    self.assertEqual(header, expected_header)

  def testWriteFooter(self):
    """Tests the WriteFooter function."""
    expected_footer = '</Document></kml>'

    self._output_module.WriteFooter()

    footer = self._output_writer.ReadOutput()
    self.assertEqual(footer, expected_footer)

  def testWriteEventBody(self):
    """Tests the WriteEventBody function."""

    # Test event object without geo-location.
    self._output_module.WriteEventBody(self._event_object)
    event_body = self._output_writer.ReadOutput()
    self.assertEqual(event_body, '')

    # Test event object with geo-location.
    self._event_object.latitude = 37.4222899014
    self._event_object.longitude = -122.082203543
    self._output_module.WriteEventBody(self._event_object)
    event_body = self._output_writer.ReadOutput()

    if sys.platform.startswith('win'):
      # The dict comparison is very picky on Windows hence we
      # have to make sure the drive letter is in the same case.
      expected_os_location = os.path.abspath('\\{0:s}'.format(
          os.path.join('cases', 'image.dd')))
    else:
      expected_os_location = '{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd'))

    expected_event_body = (
        '<Placemark><name>PLACEHOLDER FOR EVENT IDENTIFIER</name><description>'
        '+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-'
        '+-+-+-+-+-+-\n'
        '[Timestamp]:\n'
        '  2012-06-27T18:17:01+00:00\n'
        '[Pathspec]:\n'
        '  type: OS, location: {0:s}\n'
        '  type: TSK, inode: 15, location: /var/log/syslog.1\n'
        '  \n'
        '\n'
        '[Reserved attributes]:\n'
        '  {{data_type}} test:output\n'
        '  {{display_name}} OS: /var/log/syslog.1\n'
        '  {{hostname}} ubuntu\n'
        '  {{inode}} 12345678\n'
        '  {{timestamp}} 1340821021000000\n'
        '  {{username}} root\n'
        '\n'
        '[Additional attributes]:\n'
        '  {{latitude}} 37.4222899014\n'
        '  {{longitude}} -122.082203543\n'
        '  {{text}} Reporter &lt;CRON&gt; PID: |8442| '
        '(pam_unix(cron:session): session\n'
        ' closed for user root)\n'
        '</description>'
        '<Point><coordinates>-122.082203543,37.4222899014</coordinates>'
        '</Point></Placemark>').format(expected_os_location)

    self.assertEqual(event_body.split('\n'), expected_event_body.split('\n'))


if __name__ == '__main__':
  unittest.main()
