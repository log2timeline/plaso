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
"""Tests for the preg front-end."""

import StringIO
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.frontend import frontend
from plaso.frontend import preg
from plaso.frontend import test_lib

from plaso.lib import errors


class StringIOOutputWriter(object):
  """Class that implements a StringIO output writer."""

  def __init__(self):
    """Initialize the string output writer."""
    super(StringIOOutputWriter, self).__init__()
    self._string_obj = StringIO.StringIO()

    # Make the output writer compatible with a filehandle interface.
    self.write = self.Write

  def flush(self):
    """Flush the internal buffer."""
    self._string_obj.flush()

  def GetValue(self):
    """Returns the write buffer from the output writer."""
    return self._string_obj.getvalue()

  def GetLine(self):
    """Returns a single line read from the output buffer."""
    return self._string_obj.readline()

  def SeekToBeginning(self):
    """Seeks the output buffer to the beginning of the buffer."""
    self._string_obj.seek(0)

  def Write(self, string):
    """Writes a string to the StringIO object."""
    self._string_obj.write(string)


class PregFrontendTest(test_lib.FrontendTestCase):
  """Tests for the preg front-end."""

  def _GetHelperAndOutputWriter(self):
    """Return a helper object (instance of PregHelper) and an output writer."""
    hive_storage = preg.PregStorage()
    options = frontend.Options()

    output_writer = StringIOOutputWriter()
    test_front_end = preg.PregFrontend(output_writer)

    shell_helper = preg.PregHelper(options, test_front_end, hive_storage)

    return shell_helper, output_writer

  def testBadRun(self):
    """Test few functions that should raise exceptions."""
    shell_helper, _ = self._GetHelperAndOutputWriter()

    options = frontend.Options()
    options.foo = u'bar'

    with self.assertRaises(errors.BadConfigOption):
      shell_helper.tool_front_end.ParseOptions(options)

    options.regfile = 'this_path_does_not_exist'
    with self.assertRaises(errors.BadConfigOption):
      shell_helper.tool_front_end.ParseOptions(options)

  def testFrontEnd(self):
    """Test various functions inside the front end object."""
    shell_helper, _ = self._GetHelperAndOutputWriter()
    front_end = shell_helper.tool_front_end

    options = frontend.Options()
    hive_path = self._GetTestFilePath([u'NTUSER.DAT'])
    options.regfile = hive_path

    front_end.ParseOptions(options, source_option='image')

    # Test the --info parameter to the tool.
    info_string = front_end.GetListOfAllPlugins()
    self.assertTrue(u'* Supported Plugins *' in info_string)
    self.assertTrue(
        u'userassist : Parser for User Assist Registry data' in info_string)
    self.assertTrue(
        u'services : Parser for services and drivers Registry ' in info_string)

    # Get paths to various registry files.
    hive_paths_for_usersassist = set([
        u'/Documents And Settings/.+/NTUSER.DAT', '/Users/.+/NTUSER.DAT'])
    # Testing functions within the front end, thus need to access protected
    # members.
    # pylint: disable=protected-access
    test_paths_for_userassist = set(
        front_end._GetRegistryFilePaths(u'userassist'))

    self.assertEquals(hive_paths_for_usersassist, test_paths_for_userassist)

    # Set the path to the system registry.
    preg.PregCache.knowledge_base_object.pre_obj.sysregistry = u'C:/Windows/Foo'

    # Test the SOFTWARE hive.
    test_paths = front_end._GetRegistryFilePaths(u'', u'SOFTWARE')
    self.assertEqual(test_paths, [u'C:/Windows/Foo/SOFTWARE'])

  def testMagicClass(self):
    """Test the magic class functions."""
    # Open up a hive.
    hive_path = self._GetTestFilePath([u'NTUSER.DAT'])
    shell_helper, _ = self._GetHelperAndOutputWriter()

    hive_helper = shell_helper.OpenHive(hive_path, None)
    self.assertEqual(hive_helper.name, u'NTUSER.DAT')

    preg.PregCache.shell_helper = shell_helper
    preg.PregCache.hive_storage = shell_helper.hive_storage
    preg.PregCache.parser_mediator = shell_helper.BuildParserMediator()

    # Mark this hive as the currently opened one.
    preg.PregCache.hive_storage.AppendHive(hive_helper)
    storage_length = len(preg.PregCache.hive_storage)
    preg.PregCache.hive_storage.SetOpenHive(storage_length - 1)

    magic_obj = preg.MyMagics(None)

    # Change directory and verify it worked.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    magic_obj.ChangeDirectory(registry_key_path)
    registry_key = preg.GetCurrentKey()
    self.assertEquals(registry_key.path, registry_key_path)
    self.assertEquals(
        hive_helper.GetCurrentRegistryKey().path, registry_key_path)

    # List the directory content.
    output_string = StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.ListDirectoryContent(u'')
    expected_strings = [
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateBeginTime',
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateFinishTime',
        u'-r-xr-xr-x                            [REG_SZ]  VersionXmlURL\n']
    self.assertEquals(output_string.GetValue(), u'\n'.join(expected_strings))

    # Parse the current key.
    output_string = StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.ParseCurrentKey(u'')
    partial_string = (
        u'LastUpdateFinishTime : [REG_SZ] Tue, 04 Aug 2009 15:18:35 GMT')
    self.assertTrue(partial_string in output_string.GetValue())

    # Parse using a plugin.
    output_string = StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.ParseWithPlugin(u'userassist')

    partial_string = (
        u'UEME_RUNPIDL:%csidl2%\\BCWipe 3.0\\BCWipe Task Manager.lnk '
        u': [Count: 1]')
    self.assertTrue(partial_string in output_string.GetValue())

    # Let's see where we are at the moment.
    output_string = StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.PrintCurrentWorkingDirectory(u'')

    current_directory = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
        u'\\UserAssist\\{5E6AB780-7743-11CF-A12B-00AA004AE837}\n')

    self.assertEquals(current_directory, output_string.GetValue())

  def testParseHive(self):
    """Test the ParseHive function."""
    shell_helper, _ = self._GetHelperAndOutputWriter()

    # TODO: Replace this once _GetTestFileEntry is pushed in.
    system_hive_path = self._GetTestFilePath(['SYSTEM'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=system_hive_path)
    collectors = [('current', None)]

    key_paths = [
        u'\\ControlSet001\\Enum\\USBSTOR',
        u'\\ControlSet001\\Enum\\USB',
        u'\\ControlSet001\\Control\\Windows']

    output = shell_helper.tool_front_end.ParseHive(
        path_spec, collectors, shell_helper, key_paths=key_paths,
        use_plugins=None, verbose=False)

    self.assertTrue(u'ComponentizedBuild : [REG_DWORD_LE] 1' in output)
    self.assertTrue(u'subkey_name : Disk&Ven_HP&Prod_v100w&Rev_1024' in output)

  def testRunPlugin(self):
    """Tests running the preg frontend against a plugin."""
    shell_helper, output_writer = self._GetHelperAndOutputWriter()

    options = shell_helper.tool_options
    options.regfile = self._GetTestFilePath(['NTUSER.DAT'])
    options.verbose = False

    shell_helper.tool_front_end.ParseOptions(options, source_option='image')
    shell_helper.tool_front_end.RunModeRegistryPlugin(options, u'userassist')

    self.assertTrue((
        u'UEME_RUNPATH:C:\\Program Files\\Internet Explorer\\iexplore.exe : '
        u'[Count: 1]') in output_writer.GetValue())

    # TODO: Add tests that parse a disk image. Test both Registry key parsing
    # and plugin parsing.

  def testRunAgainstKey(self):
    """Tests running the preg frontend against a Registry key."""
    shell_helper, output_writer = self._GetHelperAndOutputWriter()

    options = shell_helper.tool_options
    options.key = u'\\Microsoft\\Windows NT\\CurrentVersion'
    options.regfile = self._GetTestFilePath(['SOFTWARE'])
    options.verbose = False

    shell_helper.tool_front_end.ParseOptions(options, source_option='image')
    shell_helper.tool_front_end.RunModeRegistryKey(options, u'')

    self.assertTrue(
        u'Product name : Windows 7 Ultimate' in output_writer.GetValue())

  def testRunAgainstFile(self):
    """Tests running the preg frontend against a whole Registry file."""
    shell_helper, output_writer = self._GetHelperAndOutputWriter()

    options = shell_helper.tool_options
    options.regfile = self._GetTestFilePath(['SOFTWARE'])

    shell_helper.tool_front_end.ParseOptions(options, source_option='image')
    shell_helper.tool_front_end.RunModeRegistryFile(options, options.regfile)

    plugins = set()
    registry_keys = set()
    line_count = 0

    output_writer.SeekToBeginning()
    line = output_writer.GetLine()
    while line:
      line_count += 1
      line = line.lstrip()
      if line.startswith('** Plugin'):
        _, _, plugin_name = line.rpartition(':')
        plugins.add(plugin_name.strip())
      if line.startswith('Key Path :'):
        _, _, key_name = line.rpartition(':')
        registry_keys.add(key_name.strip())
      line = output_writer.GetLine()

    # Define the minimum set of plugins that need to be in the output.
    expected_plugins = set([
        u'winreg_run_software **', u'winreg_task_cache **', u'winreg_winver **',
        u'winreg_msie_zone_software **', u'winreg_default **'])

    self.assertTrue(expected_plugins.issubset(plugins))

    self.assertTrue((
        u'\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\'
        u'TaskCache') in registry_keys)
    self.assertTrue(
        u'\\Microsoft\\Windows\\CurrentVersion\\RunOnce' in registry_keys)

    # The output should grow with each newly added plugin, and it might be
    # reduced with changes to the codebase, yet there should be at least 1.500
    # lines in the output.
    self.assertGreater(line_count, 1500)

  def testTopLevelMethods(self):
    """Test few of the top level methods in the preg module."""
    shell_helper, _ = self._GetHelperAndOutputWriter()

    # Set the cache.
    preg.PregCache.shell_helper = shell_helper
    preg.PregCache.hive_storage = shell_helper.hive_storage
    preg.PregCache.parser_mediator = shell_helper.BuildParserMediator()

    # Open up a hive.
    hive_path = self._GetTestFilePath([u'NTUSER.DAT'])
    hive_helper = shell_helper.OpenHive(hive_path, None)
    preg.PregCache.hive_storage.AppendHive(hive_helper)
    preg.PregCache.hive_storage.SetOpenHive(
        len(preg.PregCache.hive_storage) - 1)

    self.assertTrue(preg.IsLoaded())
    self.assertEqual(
        preg.PregCache.hive_storage.loaded_hive.name, u'NTUSER.DAT')

    # Open a Registry key using the magic class.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    magic_obj = preg.MyMagics(None)
    magic_obj.ChangeDirectory(registry_key_path)

    registry_key = preg.GetCurrentKey()
    hive_helper = preg.PregCache.hive_storage.loaded_hive
    self.assertEquals(registry_key.path, registry_key_path)
    self.assertEquals(
        hive_helper.GetCurrentRegistryKey().path, registry_key_path)

    # Get a value out of the currently loaded Registry key.
    value = preg.GetValue(u'VersionXmlURL')
    self.assertEquals(value.name, u'VersionXmlURL')

    value_data = preg.GetValueData(u'VersionXmlURL')
    self.assertEquals(
        value_data,
        u'http://javadl.sun.com/webapps/download/AutoDL?BundleId=33742')

    # Parse a Registry key.
    parsed_strings = preg.ParseKey(
        registry_key, shell_helper=shell_helper, hive_helper=hive_helper)
    self.assertTrue(parsed_strings[1].lstrip().startswith(u'** Plugin : '))

    # Change back to the root key.
    magic_obj.ChangeDirectory(u'')
    registry_key = preg.GetCurrentKey()
    self.assertEquals(registry_key.path, u'\\')

    # TODO: Add tests for formatting of events, eg: parse a key, get the event
    # objects and test the formatting of said event object.
    # TODO: Add tests for running in console mode.


if __name__ == '__main__':
  unittest.main()
