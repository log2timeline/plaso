#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import unittest

from plaso.frontend import preg as preg_frontend
from plaso.lib import errors
from tests.cli import test_lib as cli_test_lib

from tools import preg
from tools import test_lib


class PregToolTest(test_lib.ToolTestCase):
  """Tests for the preg tool."""

  def _ExtractPluginsAndKey(self, string):
    """Takes a string and returns two sets with names of plugins and keys.

    Args:
      string: a string containing the full output from preg that contains
              headings and results.

    Returns:
      Two sets, plugins and registry_keys. The set plugins contains a list
      of all plugins that were found in the output string and the registry_key
      extracts a list of all Registry keys that were parsed in the supplied
      string.
    """
    # TODO: refactor to more accurate way to test this.
    plugins = set()
    registry_keys = set()

    for line in string.split(b'\n'):
      line = line.lstrip()

      if b'** Plugin' in line:
        _, _, plugin_name_line = line.rpartition(b':')
        plugin_name, _, _ = plugin_name_line.partition(b'*')
        plugins.add(plugin_name.strip())

      if b'Key Path :' in line:
        _, _, key_name = line.rpartition(b':')
        registry_keys.add(key_name.strip())

    return plugins, registry_keys

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = preg.PregTool(output_writer=self._output_writer)

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    options = cli_test_lib.TestOptions()
    options.foo = u'bar'

    with self.assertRaises(errors.BadConfigOption):
      self._test_tool.ParseOptions(options)

    options = cli_test_lib.TestOptions()
    options.registry_file = u'this_path_does_not_exist'

    with self.assertRaises(errors.BadConfigOption):
      self._test_tool.ParseOptions(options)

  def testListPluginInformation(self):
    """Tests the ListPluginInformation function."""
    options = cli_test_lib.TestOptions()
    options.show_info = True

    self._test_tool.ParseOptions(options)

    self._test_tool.ListPluginInformation()

    output = self._output_writer.ReadOutput()

    # TODO: refactor to more accurate way to test this.
    self.assertIn(b'* Supported Plugins *', output)
    self.assertIn(b'userassist : Parser for User Assist Registry data', output)
    self.assertIn(
        b'services : Parser for services and drivers Registry', output)

  def testPrintHeader(self):
    """Tests the PrintHeader function."""
    self._test_tool.PrintHeader(u'Text')
    string = self._output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************* '
        b'Text '
        b'*************************************\n')
    self.assertEqual(string, expected_string)

    self._test_tool.PrintHeader(u'Another Text', character=u'x')
    string = self._output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx '
        b'Another Text '
        b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    self._test_tool.PrintHeader(u'')
    string = self._output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'*************************************** '
        b' '
        b'***************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    self._test_tool.PrintHeader(None)
    string = self._output_writer.ReadOutput()
    expected_string = (
        b'\n'
        b'************************************* '
        b'None '
        b'*************************************\n')
    self.assertEqual(string, expected_string)

    # TODO: determine if this is the desired behavior.
    expected_string = (
        u'\n '
        u'In computer programming, a string is traditionally a sequence '
        u'of characters, either as a literal constant or as some kind of '
        u'variable. \n')
    self._test_tool.PrintHeader(expected_string[2:-2])
    string = self._output_writer.ReadOutput()
    self.assertEqual(string, expected_string)

  def testRunModeRegistryPlugin(self):
    """Tests the RunModeRegistryPlugin function."""
    options = cli_test_lib.TestOptions()
    options.registry_file = self._GetTestFilePath([u'NTUSER.DAT'])
    options.plugin_names = u'userassist'
    options.verbose = False

    self._test_tool.ParseOptions(options)

    self._test_tool.RunModeRegistryPlugin()

    output = self._output_writer.ReadOutput()

    # TODO: refactor to more accurate way to test this.
    self.assertIn((
        b'UEME_RUNPATH:C:\\Program Files\\Internet Explorer\\iexplore.exe : '
        b'[Count: 1]'), output)

    # TODO: Add tests that parse a disk image. Test both Registry key parsing
    # and plugin parsing.

  def testRunModeRegistryKey(self):
    """Tests the RunModeRegistryKey function."""
    options = cli_test_lib.TestOptions()
    options.key = u'\\Microsoft\\Windows NT\\CurrentVersion'
    options.parser_names = u''
    options.registry_file = self._GetTestFilePath([u'SOFTWARE'])
    options.verbose = False

    self._test_tool.ParseOptions(options)

    self._test_tool.RunModeRegistryKey()

    output = self._output_writer.ReadOutput()

    # TODO: refactor to more accurate way to test this.
    self.assertIn(b'Product name : Windows 7 Ultimate', output)

  def testRunModeRegistryFile(self):
    """Tests the RunModeRegistryFile function."""
    options = cli_test_lib.TestOptions()
    options.registry_file = self._GetTestFilePath([u'SOFTWARE'])

    self._test_tool.ParseOptions(options)

    self._test_tool.RunModeRegistryFile()

    output = self._output_writer.ReadOutput()

    plugins, registry_keys = self._ExtractPluginsAndKey(output)

    # Define the minimum set of plugins that need to be in the output.
    # This information is gathered from the actual tool output, which
    # for aesthetics reasons surrounds the text with **. The above processing
    # then cuts of the first half of that, but leaves the second ** intact.
    expected_plugins = set([
        b'windows_run_software',
        b'windows_task_cache',
        b'windows_version',
        b'msie_zone_software'])

    self.assertTrue(expected_plugins.issubset(plugins))

    self.assertIn((
        b'\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\'
        b'TaskCache'), registry_keys)
    self.assertIn(
        b'\\Microsoft\\Windows\\CurrentVersion\\Run', registry_keys)
    self.assertIn((
        b'\\Microsoft\\Windows\\CurrentVersion\\Internet '
        b'Settings\\Lockdown_Zones'), registry_keys)

    # The output should grow with each newly added plugin, and it might be
    # reduced with changes to the codebase, yet there should be at least 1.400
    # lines in the output.
    line_count = 0
    for _ in output:
      line_count += 1
    self.assertGreater(line_count, 1400)


class PregConsoleTest(test_lib.ToolTestCase):
  """Tests for the preg console."""

  _EXPECTED_BANNER_HEADER = [
      (u'******** Welcome to PREG - home of the Plaso Windows Registry '
       u'Parsing. *********'),
      u'',
      u'Some of the commands that are available for use are:',
      u'',
      (u'                 cd key : Navigate the Registry like a directory '
       u'structure.'),
      (u'                ls [-v] : List all subkeys and values of a Registry '
       u'key. If'),
      (u'                          called as ls True then values of '
       u'keys will be'),
      u'                          included in the output.',
      u'             parse -[v] : Parse the current key using all plugins.',
      (u'plugin [-h] plugin_name : Run a particular key-based plugin on the '
       u'loaded'),
      (u'                          hive. The correct Registry key will '
       u'be loaded, opened'),
      u'                          and then parsed.',
      (u'   get_value value_name : Get a value from the currently loaded '
       u'Registry key.'),
      (u'get_value_data value_name : Get a value data from a value stored in '
       u'the'),
      u'                          currently loaded Registry key.',
      u'                get_key : Return the currently loaded Registry key.',
      (u'---------------------------------------------------------------------'
       u'-----------')]

  _EXPECTED_BANNER_FOOTER = u'Happy command line console fu-ing.'

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = preg.PregTool(output_writer=self._output_writer)
    self._test_console = preg.PregConsole(self._test_tool)
    file_entry = self._GetTestFileEntryFromPath([u'NTUSER.DAT'])
    self._file_path = self._GetTestFilePath([u'NTUSER.DAT'])
    self._registry_helper = preg_frontend.PregRegistryHelper(
        file_entry, u'OS', self._test_tool._knowledge_base_object)

  def tearDown(self):
    """Tears down the needed ojects after a test."""
    self._registry_helper.Close()

  def testAddRegistryHelpers(self):
    """Test the add registry helper."""
    self._test_console.AddRegistryHelper(self._registry_helper)
    registry_helpers = getattr(self._test_console, u'_registry_helpers', [])

    self.assertEquals(len(registry_helpers), 1)
    setattr(self._test_console, u'_registry_helpers', [])

  def testPrintBanner(self):
    """Test the PrintBanner function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    setattr(self._test_console, u'_output_writer', output_writer)
    setattr(self._test_console.preg_tool, u'_output_writer', output_writer)

    self.assertFalse(self._test_console.IsLoaded())
    self._test_console.AddRegistryHelper(self._registry_helper)
    self._test_console.LoadRegistryFile(0)
    self.assertTrue(self._test_console.IsLoaded())
    self._test_console.PrintBanner()

    extra_text = (
        u'Opening hive: {0:s} [OS]\n'
        u'Registry file: NTUSER.DAT [{0:s}] is available and '
        u'loaded.\n').format(self._file_path)

    expected_banner = u'\n{0:s}\n{1:s}\n{2:s}'.format(
        u'\n'.join(self._EXPECTED_BANNER_HEADER), extra_text,
        self._EXPECTED_BANNER_FOOTER)
    banner = output_writer.ReadOutput()
    self.assertEquals(banner, expected_banner)

  def testPrintRegistryFileList(self):
    """Test the PrintRegistryFileList function."""
    output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    setattr(self._test_console, u'_output_writer', output_writer)
    setattr(self._test_console.preg_tool, u'_output_writer', output_writer)

    self._test_console.PrintRegistryFileList()
    text = output_writer.ReadOutput()
    self.assertEquals(text, u'')

    self._test_console.AddRegistryHelper(self._registry_helper)
    self._test_console.PrintRegistryFileList()
    text = output_writer.ReadOutput()

    expected_text = u'Index Hive [collector]\n0     {0:s} [OS]\n'.format(
        self._file_path)

    self.assertEquals(text, expected_text)

  def testGetValueData(self):
    """Test getting values and value entries."""
    self._test_console.AddRegistryHelper(self._registry_helper)
    self._test_console.LoadRegistryFile(0)

    # Open a Registry key using the magic class.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    key = self._registry_helper.GetKeyByPath(registry_key_path)
    self.assertEquals(key.path, registry_key_path)

    registry_key = self._test_console._CommandGetCurrentKey()
    self.assertEqual(registry_key.path, registry_key_path)
    helper_key = self._registry_helper.GetCurrentRegistryKey()
    self.assertEqual(helper_key.path, registry_key_path)

    # Get a value out of the currently loaded Registry key.
    value = self._test_console._CommandGetValue(u'VersionXmlURL')
    self.assertEqual(value.name, u'VersionXmlURL')

    value_data = self._test_console._CommandGetValueData(u'VersionXmlURL')
    self.assertEqual(
        value_data,
        u'http://javadl.sun.com/webapps/download/AutoDL?BundleId=33742')


class PregMagicClassTest(test_lib.ToolTestCase):
  """Tests for the IPython magic class."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = preg.PregTool(output_writer=self._output_writer)
    front_end = getattr(test_tool, '_front_end', None)
    front_end.SetKnowledgeBase(test_tool._knowledge_base_object)

    self._test_console = preg.PregConsole(test_tool)
    self._magic_obj = preg.PregMagics(None)
    self._magic_obj.console = self._test_console
    self._magic_obj.output_writer = self._output_writer

    registry_file_entry = self._GetTestFileEntryFromPath([u'NTUSER.DAT'])
    self._registry_helper = preg_frontend.PregRegistryHelper(
        registry_file_entry, u'OS', test_tool._knowledge_base_object)

    self._test_console.AddRegistryHelper(self._registry_helper)
    self._test_console.LoadRegistryFile(0)
    setattr(self._test_console, '_output_writer', self._output_writer)

  def tearDown(self):
    """Tears down the needed ojects after a test."""
    self._registry_helper.Close()

  def testHiveActions(self):
    """Test the HiveAction function."""
    self._magic_obj.HiveActions(u'list')
    text = self._output_writer.ReadOutput()

    registry_file_path = self._GetTestFilePath([u'NTUSER.DAT'])
    expected_text = (
        u'Index Hive [collector]\n0     *{0:s} [OS]\n\n'
        u'To open a Registry file, use: hive open INDEX\n').format(
            registry_file_path)

    self.assertEquals(text, expected_text)

  def testMagicClass(self):
    """Test the magic class functions."""
    self.assertEqual(self._registry_helper.name, u'NTUSER.DAT')
    # Change directory and verify it worked.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    self._magic_obj.ChangeDirectory(registry_key_path)
    registry_key = self._test_console._CommandGetCurrentKey()
    self.assertEqual(registry_key.path, registry_key_path)
    current_key = self._registry_helper.GetCurrentRegistryKey()
    self.assertEqual(current_key.path, registry_key_path)

    # List the directory content.
    self._magic_obj.ListDirectoryContent(u'')
    expected_strings = [
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateBeginTime',
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateFinishTime',
        u'-r-xr-xr-x                            [REG_SZ]  VersionXmlURL\n']
    text = self._output_writer.ReadOutput()
    self.assertEqual(text, u'\n'.join(expected_strings))

    # Parse the current key.
    self._magic_obj.ParseCurrentKey(u'')
    partial_string = (
        u'LastUpdateFinishTime : [REG_SZ] Tue, 04 Aug 2009 15:18:35 GMT')
    self.assertTrue(partial_string in self._output_writer.ReadOutput())

    # Parse using a plugin.
    self._magic_obj.ParseWithPlugin(u'userassist')

    partial_string = (
        u'UEME_RUNPIDL:%csidl2%\\BCWipe 3.0\\BCWipe Task Manager.lnk '
        u': [Count: 1]')
    self.assertTrue(partial_string in self._output_writer.ReadOutput())

    self._magic_obj.PrintCurrentWorkingDirectory(u'')

    current_directory = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
        u'\\UserAssist\\{5E6AB780-7743-11CF-A12B-00AA004AE837}\n')

    self.assertEqual(current_directory, self._output_writer.ReadOutput())

  def testTopLevelMethods(self):
    """Test few of the top level methods in the preg module."""
    # Open a Registry key using the magic class.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    self._magic_obj.ChangeDirectory(registry_key_path)

    registry_key = self._test_console._CommandGetCurrentKey()
    self.assertEqual(registry_key.path, registry_key_path)
    helper_key = self._registry_helper.GetCurrentRegistryKey()
    self.assertEqual(helper_key.path, registry_key_path)

    # Change back to the base key.
    self._magic_obj.ChangeDirectory(u'')
    registry_key = self._test_console._CommandGetCurrentKey()
    self.assertEqual(registry_key.path, u'\\')


if __name__ == '__main__':
  unittest.main()
