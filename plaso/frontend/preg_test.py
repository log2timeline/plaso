#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory

from plaso.frontend import frontend
from plaso.frontend import preg
from plaso.frontend import test_lib

from plaso.lib import errors


class PregFrontendTest(test_lib.FrontendTestCase):
  """Tests for the preg front-end."""

  def _GetHelperAndOutputWriter(self):
    """Return a helper object (instance of PregHelper) and an output writer."""
    hive_storage = preg.PregStorage()
    options = frontend.Options()

    output_writer = test_lib.StringIOOutputWriter()
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

    self.assertEqual(hive_paths_for_usersassist, test_paths_for_userassist)

    # Set the path to the system registry.
    preg.PregCache.knowledge_base_object.pre_obj.sysregistry = u'C:/Windows/Foo'

    # Test the SOFTWARE hive.
    test_paths = front_end._GetRegistryFilePaths(u'', u'SOFTWARE')
    self.assertEqual(test_paths, [u'C:/Windows/Foo/SOFTWARE'])

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


if __name__ == '__main__':
  unittest.main()
