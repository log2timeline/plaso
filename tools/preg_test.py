#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import unittest

from plaso.frontend import frontend
from plaso.frontend import preg as preg_frontend

from tools import preg
from tools import test_lib


class PregToolTest(test_lib.ToolTestCase):
  """Tests for the preg tool."""

  def _GetHelperAndOutputWriter(self):
    """Return a helper object (instance of PregHelper) and an output writer."""
    hive_storage = preg_frontend.PregStorage()
    options = frontend.Options()

    output_writer = test_lib.StringIOOutputWriter()
    test_front_end = preg_frontend.PregFrontend(output_writer)

    shell_helper = preg_frontend.PregHelper(
        options, test_front_end, hive_storage)

    return shell_helper, output_writer

  def testMagicClass(self):
    """Test the magic class functions."""
    # Open up a hive.
    hive_path = self._GetTestFilePath([u'NTUSER.DAT'])
    shell_helper, _ = self._GetHelperAndOutputWriter()

    hive_helper = shell_helper.OpenHive(hive_path, None)
    self.assertEqual(hive_helper.name, u'NTUSER.DAT')

    preg_frontend.PregCache.shell_helper = shell_helper
    preg_frontend.PregCache.hive_storage = shell_helper.hive_storage
    preg_frontend.PregCache.parser_mediator = shell_helper.BuildParserMediator()

    # Mark this hive as the currently opened one.
    preg_frontend.PregCache.hive_storage.AppendHive(hive_helper)
    storage_length = len(preg_frontend.PregCache.hive_storage)
    preg_frontend.PregCache.hive_storage.SetOpenHive(storage_length - 1)

    magic_obj = preg.MyMagics(None)

    # Change directory and verify it worked.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    magic_obj.ChangeDirectory(registry_key_path)
    registry_key = preg.GetCurrentKey()
    self.assertEqual(registry_key.path, registry_key_path)
    self.assertEqual(
        hive_helper.GetCurrentRegistryKey().path, registry_key_path)

    # List the directory content.
    output_string = test_lib.StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.ListDirectoryContent(u'')
    expected_strings = [
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateBeginTime',
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateFinishTime',
        u'-r-xr-xr-x                            [REG_SZ]  VersionXmlURL\n']
    self.assertEqual(output_string.GetValue(), u'\n'.join(expected_strings))

    # Parse the current key.
    output_string = test_lib.StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.ParseCurrentKey(u'')
    partial_string = (
        u'LastUpdateFinishTime : [REG_SZ] Tue, 04 Aug 2009 15:18:35 GMT')
    self.assertTrue(partial_string in output_string.GetValue())

    # Parse using a plugin.
    output_string = test_lib.StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.ParseWithPlugin(u'userassist')

    partial_string = (
        u'UEME_RUNPIDL:%csidl2%\\BCWipe 3.0\\BCWipe Task Manager.lnk '
        u': [Count: 1]')
    self.assertTrue(partial_string in output_string.GetValue())

    # Let's see where we are at the moment.
    output_string = test_lib.StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.PrintCurrentWorkingDirectory(u'')

    current_directory = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
        u'\\UserAssist\\{5E6AB780-7743-11CF-A12B-00AA004AE837}\n')

    self.assertEqual(current_directory, output_string.GetValue())

  def testTopLevelMethods(self):
    """Test few of the top level methods in the preg module."""
    shell_helper, _ = self._GetHelperAndOutputWriter()

    # Set the cache.
    preg_frontend.PregCache.shell_helper = shell_helper
    preg_frontend.PregCache.hive_storage = shell_helper.hive_storage
    preg_frontend.PregCache.parser_mediator = shell_helper.BuildParserMediator()

    # Open up a hive.
    hive_path = self._GetTestFilePath([u'NTUSER.DAT'])
    hive_helper = shell_helper.OpenHive(hive_path, None)
    preg_frontend.PregCache.hive_storage.AppendHive(hive_helper)
    preg_frontend.PregCache.hive_storage.SetOpenHive(
        len(preg_frontend.PregCache.hive_storage) - 1)

    self.assertTrue(preg.IsLoaded())
    self.assertEqual(
        preg_frontend.PregCache.hive_storage.loaded_hive.name, u'NTUSER.DAT')

    # Open a Registry key using the magic class.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    magic_obj = preg.MyMagics(None)
    magic_obj.ChangeDirectory(registry_key_path)

    registry_key = preg.GetCurrentKey()
    hive_helper = preg_frontend.PregCache.hive_storage.loaded_hive
    self.assertEqual(registry_key.path, registry_key_path)
    self.assertEqual(
        hive_helper.GetCurrentRegistryKey().path, registry_key_path)

    # Get a value out of the currently loaded Registry key.
    value = preg.GetValue(u'VersionXmlURL')
    self.assertEqual(value.name, u'VersionXmlURL')

    value_data = preg.GetValueData(u'VersionXmlURL')
    self.assertEqual(
        value_data,
        u'http://javadl.sun.com/webapps/download/AutoDL?BundleId=33742')

    # Parse a Registry key.
    parsed_strings = preg_frontend.ParseKey(
        registry_key, shell_helper=shell_helper, hive_helper=hive_helper)
    self.assertTrue(parsed_strings[1].lstrip().startswith(u'** Plugin : '))

    # Change back to the root key.
    magic_obj.ChangeDirectory(u'')
    registry_key = preg.GetCurrentKey()
    self.assertEqual(registry_key.path, u'\\')

    # TODO: Add tests for formatting of events, eg: parse a key, get the event
    # objects and test the formatting of said event object.
    # TODO: Add tests for running in console mode.


if __name__ == '__main__':
  unittest.main()
