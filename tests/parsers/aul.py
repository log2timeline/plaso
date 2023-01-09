#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple Unified Logging parser."""

import csv
import glob
import logging
import tempfile
import os
import re
import subprocess
import unittest

from pathlib import Path

from plaso.parsers import aul

from plaso.helpers.mac import dns

from tests.parsers import test_lib


class AULParserTest(test_lib.ParserTestCase):
  """Tests for the AUL parser."""
  def setUp(self) -> None:
    logging.basicConfig(level=logging.DEBUG, format='%(message)s', handlers=[logging.FileHandler("/tmp/fry.log"), logging.StreamHandler()])
    return super().setUp()

  def testParseBasic(self):
    """Tests the Parse function."""
    parser = aul.AULParser()
    storage_writer = self._ParseFile([
      'AUL', 'private', 'var', 'db', 'diagnostics', 'Special',
      '0000000000000346.tracev3'
    ], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'mac:aul:event',
        'date_time': '2022-08-28T09:02:09.099778189+00:00',
        'level': 'Default',
        'subsystem': 'com.apple.sbd',
        'thread_id': '0x1da055',
        'pid': 823,
        'euid': 802300,
        'library': '/System/Library/PrivateFrameworks/CloudServices.framework/Helpers/com.apple.sbd',
        'library_uuid': '1F58234E37DD3B3789213BCD74F49AC6',
        'activity_id': '0x29ec60',
        'category': 'daemon',
        'message': 'sbd listener begin from pid 2115 ((null)) [com.apple.SecureBackupDaemon]'
        }

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:aul:event',
        'date_time': '2022-08-28T23:28:16.834004518+00:00',
        'level': 'Error',
        'subsystem': 'com.apple.sbd',
        'thread_id': '0x2349fa',
        'pid': 823,
        'euid': 802300,
        'library': '/System/Library/PrivateFrameworks/CloudServices.framework/Helpers/com.apple.sbd',
        'library_uuid': '1F58234E37DD3B3789213BCD74F49AC6',
        'activity_id': '0x29ec68',
        'category': 'daemon',
        'message': 'No iCloud account yet'
        }

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

  def testParseAdvanced(self):
    """Tests the Parse function."""
    parser = aul.AULParser()
    storage_writer = self._ParseFile([
    #  'AUL', 'MANDIANT', 'tmp_bg74v6n', 'private', 'var', 'db', 'diagnostics', #'Special',
    #  'Extra', 'logdata.LiveData.tracev3'
    'AUL', 'private', 'var', 'db', 'diagnostics', 'Special', '000000000000036b.tracev3'
    ], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 41954)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testParseAdvancedLoop(self):

    """Tests the Parse function."""
    files = [
      "035",
      "050",
      "041"
    ]
    for filename in files:
      cmd = "echo -n > /tmp/fryoutput.csv && echo -n > /tmp/logs.rust"
      subprocess.run(cmd, shell=True, check=True)

      parser = aul.AULParser()
      storage_writer = self._ParseFile([
        'AUL', 'ec2', 'private', 'var', 'db', 'diagnostics', 'Special',
        '0000000000000{0:s}.tracev3'.format(filename)
      ], parser)

      cmd = "rm /home/fryy/AUL/RUST_TEST/Special/*"
      subprocess.run(cmd, shell=True, check=False)
      cmd = ["cp", "/home/fryy/AUL/EC2/diagnostics/Special/0000000000000{0:s}.tracev3".format(filename), "/home/fryy/AUL/RUST_TEST/Special/"]
      subprocess.run(cmd, check=True)
      cmd = ["/home/fryy/Code/macos-UnifiedLogs/examples/target/debug/unifiedlog_parser", "-i", "/home/fryy/AUL/RUST_TEST", "-o", "/tmp/logs.rust"]
      result = subprocess.run(cmd, capture_output=True, check=True)
      number_results = int((str(result.stdout).split('\\n')[-4]).split(" ")[1])

      number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
      self.assertLess((number_results-number_of_events), 5)

      number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
          'extraction_warning')
      self.assertEqual(number_of_warnings, 0)

      number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
          'recovery_warning')
      self.assertEqual(number_of_warnings, 0)

  def testMandiantTests(self):
    """Tests the Parse function."""
    i = 0
    for operating_system in glob.glob("/home/fryy/AUL/Mandiant/test_data/*logarchive*"):
      i += 1
      if i == 1:
        continue
      # Clean output files
      cmd = "echo -n > /tmp/fryoutput.csv"
      subprocess.run(cmd, shell=True, check=True)
      # Set up directory structure
      with tempfile.TemporaryDirectory(dir="/home/fryy/Code/plaso/test_data/AUL/MANDIANT/") as t:
        uuidpath = os.path.join(t, "private/var/db/uuidtext")
        diagpath = os.path.join(t, "private/var/db/diagnostics")
        Path(diagpath).mkdir(parents=True, exist_ok=True)
        Path(uuidpath).mkdir(parents=True, exist_ok=True)
        subprocess.run("cp -r {0:s}/* {1:s}/".format(operating_system, uuidpath), shell=True, check=True)
        subprocess.run("mv {}/Extra {}/Special {}/HighVolume {}/Persist {}/Signpost {}/timesync {}/".format(uuidpath, uuidpath, uuidpath, uuidpath, uuidpath, uuidpath, diagpath), shell=True, check=True)
        subprocess.run("mv {}/logdata.LiveData.tracev3 {}/Extra".format(uuidpath, diagpath), shell=True, check=False)

        # Run full Mandiant command
        #cmd = ["/home/fryy/Code/macos-UnifiedLogs/examples/target/debug/unifiedlog_parser", "-i", operating_system, "-o", "/tmp/logs.rust"]
        #subprocess.run(cmd, check=True)

        # Run on each of the files
        for f in sorted(glob.glob(os.path.join(diagpath, "Special/*.tracev3"))) + sorted(glob.glob(os.path.join(diagpath, "Extra/*.tracev3"))) + sorted(glob.glob(os.path.join(diagpath, "Signpost/*.tracev3"))) + sorted(glob.glob(os.path.join(diagpath, "Persist/*.tracev3"))):
          # cmd = "echo -n > /tmp/fryoutput.csv"
          # subprocess.run(cmd, shell=True, check=True)

          parser = aul.AULParser()
          storage_writer = self._ParseFile([f], parser)

          number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
              'extraction_warning')
          self.assertEqual(number_of_warnings, 0)

          number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
              'recovery_warning')
          self.assertEqual(number_of_warnings, 0)


if __name__ == '__main__':
  unittest.main()
