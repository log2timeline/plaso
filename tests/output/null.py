#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test for the null output module."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.lib import definitions
from plaso.output import null

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class NullOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the null output module."""

  # pylint: disable=protected-access

  _OS_PATH_SPEC = path_spec_factory.Factory.NewPathSpec(
      dfvfs_definitions.TYPE_INDICATOR_OS, location='{0:s}{1:s}'.format(
          os.path.sep, os.path.join('cases', 'image.dd')))

  _TEST_EVENTS = [
      {'data_type': 'test:output',
       'display_name': 'OS: /var/log/syslog.1',
       'hostname': 'ubuntu',
       'inode': 12345678,
       'path_spec': path_spec_factory.Factory.NewPathSpec(
           dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
           location='/var/log/syslog.1', parent=_OS_PATH_SPEC),
       'text': (
           'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN,
       'username': 'root'}]

  def testGetFieldValues(self):
    """Tests the _GetFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    output_module = null.NullOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabel('Test')

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self.assertEqual(field_values, {})

  def testWriteFieldValues(self):
    """Tests the _WriteFieldValues function."""
    output_mediator = self._CreateOutputMediator()

    output_module = null.NullOutputModule()

    event, event_data, event_data_stream = (
        containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0]))

    event_tag = events.EventTag()
    event_tag.AddLabel('Test')

    field_values = output_module._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    output_module._WriteFieldValues(output_mediator, field_values)


if __name__ == '__main__':
  unittest.main()
