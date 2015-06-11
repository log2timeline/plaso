#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import io
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.frontend import preg as preg_frontend
from plaso.lib import errors
from tests.cli import test_lib as cli_test_lib

from tools import preg
from tools import test_lib


# TODO: replace by cli_test_lib.TestOutputWriter.
class StringIOOutputWriter(object):
  """Class that implements a StringIO output writer."""

  def __init__(self):
    """Initialize the string output writer."""
    super(StringIOOutputWriter, self).__init__()
    self._string_io = io.StringIO()

    # Make the output writer compatible with a filehandle interface.
    self.write = self.Write

  def flush(self):
    """Flush the internal buffer."""
    self._string_io.flush()

  def GetValue(self):
    """Returns the write buffer from the output writer."""
    return self._string_io.getvalue()

  def GetLine(self):
    """Returns a single line read from the output buffer."""
    return self._string_io.readline()

  def SeekToBeginning(self):
    """Seeks the output buffer to the beginning of the buffer."""
    self._string_io.seek(0)

  def Write(self, string):
    """Writes a string to the StringIO object."""
    self._string_io.write(string)


class PregToolTest(test_lib.ToolTestCase):
  """Tests for the preg tool."""

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

  def testRunModeRegistryPlugin(self):
    """Tests the RunModeRegistryPlugin function."""
    options = cli_test_lib.TestOptions()
    options.registry_file = self._GetTestFilePath([u'NTUSER.DAT'])
    options.parser_names = u'userassist'
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

    # TODO: refactor to more accurate way to test this.
    plugins = set()
    registry_keys = set()
    line_count = 0

    output = self._output_writer.ReadOutput()

    for line in output.split(b'\n'):
      line = line.lstrip()
      line_count += 1

      if line.startswith(b'** Plugin'):
        _, _, plugin_name = line.rpartition(b':')
        plugins.add(plugin_name.strip())

      if line.startswith(b'Key Path :'):
        _, _, key_name = line.rpartition(b':')
        registry_keys.add(key_name.strip())

    # Define the minimum set of plugins that need to be in the output.
    # This information is gathered from the actual tool output, which
    # for aesthetics reasons surrounds the text with **. The above processing
    # then cuts of the first half of that, but leaves the second ** intact.
    expected_plugins = set([
        b'windows_run_software **',
        b'windows_task_cache **',
        b'windows_version **',
        b'msie_zone_software **',
        b'winreg_default **'])

    self.assertTrue(expected_plugins.issubset(plugins))

    self.assertIn((
        b'\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\'
        b'TaskCache'), registry_keys)
    self.assertIn(
        b'\\Microsoft\\Windows\\CurrentVersion\\RunOnce', registry_keys)

    # The output should grow with each newly added plugin, and it might be
    # reduced with changes to the codebase, yet there should be at least 1.500
    # lines in the output.
    self.assertGreater(line_count, 1500)

  # TODO: clean up PregHelper.
  def testParseHive(self):
    """Tests the ParseHive function."""
    options = cli_test_lib.TestOptions()
    hive_storage = preg_frontend.PregStorage()
    preg_helper = preg.PregHelper(options, self._test_tool, hive_storage)

    # TODO: Replace this once _GetTestFileEntry is pushed in.
    system_hive_path = self._GetTestFilePath([u'SYSTEM'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=system_hive_path)
    collectors = [(u'current', None)]

    key_paths = [
        u'\\ControlSet001\\Enum\\USBSTOR',
        u'\\ControlSet001\\Enum\\USB',
        u'\\ControlSet001\\Control\\Windows']

    output = self._test_tool.ParseHive(
        path_spec, collectors, preg_helper, key_paths=key_paths,
        use_plugins=None, verbose=False)

    self.assertTrue(u'ComponentizedBuild : [REG_DWORD_LE] 1' in output)
    self.assertTrue(u'subkey_name : Disk&Ven_HP&Prod_v100w&Rev_1024' in output)


class PregConsoleTest(test_lib.ToolTestCase):
  """Tests for the preg console."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = preg.PregTool(output_writer=self._output_writer)
    self._test_console = preg.PregConsole(self._test_tool)

  def testMagicClass(self):
    """Test the magic class functions."""
    # Open up a hive.
    hive_path = self._GetTestFilePath([u'NTUSER.DAT'])

    options = cli_test_lib.TestOptions()
    hive_storage = preg_frontend.PregStorage()
    preg_helper = preg.PregHelper(options, self._test_tool, hive_storage)

    hive_helper = preg_helper.OpenHive(hive_path, None)
    self.assertEqual(hive_helper.name, u'NTUSER.DAT')

    preg_frontend.PregCache.shell_helper = preg_helper
    preg_frontend.PregCache.hive_storage = preg_helper.hive_storage
    preg_frontend.PregCache.parser_mediator = preg_helper.BuildParserMediator()

    # Mark this hive as the currently opened one.
    preg_frontend.PregCache.hive_storage.AppendHive(hive_helper)
    storage_length = len(preg_frontend.PregCache.hive_storage)
    preg_frontend.PregCache.hive_storage.SetOpenHive(storage_length - 1)

    magic_obj = preg.PregMagics(None)

    # Change directory and verify it worked.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    magic_obj.ChangeDirectory(registry_key_path)
    registry_key = self._test_console._CommandGetCurrentKey()
    self.assertEqual(registry_key.path, registry_key_path)
    self.assertEqual(
        hive_helper.GetCurrentRegistryKey().path, registry_key_path)

    # List the directory content.
    output_string = StringIOOutputWriter()
    magic_obj.RedirectOutput(output_string)
    magic_obj.ListDirectoryContent(u'')
    expected_strings = [
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateBeginTime',
        u'-r-xr-xr-x                            [REG_SZ]  LastUpdateFinishTime',
        u'-r-xr-xr-x                            [REG_SZ]  VersionXmlURL\n']
    self.assertEqual(output_string.GetValue(), u'\n'.join(expected_strings))

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

    self.assertEqual(current_directory, output_string.GetValue())

  def testTopLevelMethods(self):
    """Test few of the top level methods in the preg module."""
    options = cli_test_lib.TestOptions()
    hive_storage = preg_frontend.PregStorage()
    preg_helper = preg.PregHelper(options, self._test_tool, hive_storage)

    # Set the cache.
    preg_frontend.PregCache.shell_helper = preg_helper
    preg_frontend.PregCache.hive_storage = preg_helper.hive_storage
    preg_frontend.PregCache.parser_mediator = preg_helper.BuildParserMediator()

    # Open up a hive.
    hive_path = self._GetTestFilePath([u'NTUSER.DAT'])
    hive_helper = preg_helper.OpenHive(hive_path, None)
    preg_frontend.PregCache.hive_storage.AppendHive(hive_helper)
    preg_frontend.PregCache.hive_storage.SetOpenHive(
        len(preg_frontend.PregCache.hive_storage) - 1)

    self.assertTrue(preg.IsLoaded())
    self.assertEqual(
        preg_frontend.PregCache.hive_storage.loaded_hive.name, u'NTUSER.DAT')

    # Open a Registry key using the magic class.
    registry_key_path = u'\\Software\\JavaSoft\\Java Update\\Policy'
    magic_obj = preg.PregMagics(None)
    magic_obj.ChangeDirectory(registry_key_path)

    registry_key = self._test_console._CommandGetCurrentKey()
    hive_helper = preg_frontend.PregCache.hive_storage.loaded_hive
    self.assertEqual(registry_key.path, registry_key_path)
    self.assertEqual(
        hive_helper.GetCurrentRegistryKey().path, registry_key_path)

    # Get a value out of the currently loaded Registry key.
    value = self._test_console._CommandGetValue(u'VersionXmlURL')
    self.assertEqual(value.name, u'VersionXmlURL')

    value_data = self._test_console._CommandGetValueData(u'VersionXmlURL')
    self.assertEqual(
        value_data,
        u'http://javadl.sun.com/webapps/download/AutoDL?BundleId=33742')

    # Parse a Registry key.
    parsed_strings = self._test_tool.ParseKey(
        registry_key, shell_helper=preg_helper, hive_helper=hive_helper)
    self.assertTrue(parsed_strings[1].lstrip().startswith(u'** Plugin : '))

    # Change back to the root key.
    magic_obj.ChangeDirectory(u'')
    registry_key = self._test_console._CommandGetCurrentKey()
    self.assertEqual(registry_key.path, u'\\')

    # TODO: Add tests for formatting of events, eg: parse a key, get the event
    # objects and test the formatting of said event object.
    # TODO: Add tests for running in console mode.


if __name__ == '__main__':
  unittest.main()
