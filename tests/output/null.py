#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test for the null output module."""

from __future__ import unicode_literals

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.output import null

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class DynamicOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the null output module."""

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:output',
       'display_name': 'OS: /var/log/syslog.1',
       'hostname': 'ubuntu',
       'inode': 12345678,
       'pathspec': path_spec_factory.Factory.NewPathSpec(
           dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
           location='/var/log/syslog.1', parent=_OS_PATH_SPEC),
       'text': (
           'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': timelib.Timestamp.CopyFromString('2012-06-27 18:17:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'username': 'root'}]

  def testNoOutput(self):
    """Tests that nothing is output by the null output module."""
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = null.NullOutputModule(output_mediator)

    output_module.WriteHeader()

    event, event_data = self._CreateTestEvent(self._TEST_EVENTS[0])
    output_module.WriteEventBody(event, event_data, None)

    output_module.WriteFooter()

    output = output_writer.ReadOutput()
    self.assertEqual('', output)


if __name__ == '__main__':
  unittest.main()
