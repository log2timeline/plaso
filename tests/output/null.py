#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test for the null output module."""
import unittest

from plaso.output import null

from tests.cli import test_lib as cli_test_lib
from tests.output import test_lib


class DynamicOutputModuleTest(test_lib.OutputModuleTestCase):
  """Test the null output module."""

  def testNoOutput(self):
    """Tests that nothing is output by the null output module."""
    event_object = test_lib.TestEventObject
    output_mediator = self._CreateOutputMediator()
    output_writer = cli_test_lib.TestOutputWriter()
    output_module = null.NullOutputModule(output_mediator)

    output_module.WriteHeader()
    output_module.WriteEventBody(event_object)
    output_module.WriteFooter()

    output = output_writer.ReadOutput()
    self.assertEqual(u'', output)


if __name__ == '__main__':
  unittest.main()
