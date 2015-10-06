#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import unittest

from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.engine import knowledge_base
from plaso.frontend import preg

from tests.frontend import test_lib


class PregFrontendTest(test_lib.FrontendTestCase):
  """Tests for the preg front-end."""

  def _ConfigureSingleFileTest(self, knowledge_base_values=None):
    """Configure a single file test.

    Args:
      knowledge_base_values: optional dict containing the knowledge base
                             values. The default is None.
    """
    self._front_end = preg.PregFrontend()
    self._front_end.SetSingleFile(True)
    registry_file_path = self._GetTestFilePath([u'SYSTEM'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=registry_file_path)

    self._front_end.SetSourcePath(registry_file_path)
    self._front_end.SetSourcePathSpecs([path_spec])

    self._knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.iteritems():
        self._knowledge_base_object.SetValue(identifier, value)

    self._front_end.SetKnowledgeBase(self._knowledge_base_object)

  def _ConfigureStorageMediaFileTest(self):
    """Configure a test against a storage media file."""
    self._front_end = preg.PregFrontend()
    self._front_end.SetSingleFile(False)

    self._knowledge_base_object = knowledge_base.KnowledgeBase()
    self._front_end.SetKnowledgeBase(self._knowledge_base_object)

    storage_media_path = self._GetTestFilePath([u'registry_test.dd'])

    test_source_scanner = source_scanner.SourceScanner()
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(storage_media_path)
    test_source_scanner.Scan(scan_context)

    # Getting the most upper node.
    scan_node = scan_context.GetRootScanNode()
    while scan_node.sub_nodes:
      scan_node = scan_node.sub_nodes[0]

    self._front_end.SetSourcePath(storage_media_path)
    self._front_end.SetSourcePathSpecs([scan_node.path_spec])

  def testExpandKeysRedirect(self):
    """Tests the ExpandKeysRedirect function."""
    self._ConfigureSingleFileTest()
    registry_key_paths = [
        u'\\Software\\Foobar',
        u'\\Software\\Key\\SubKey\\MagicalKey',
        u'\\Canons\\Blast\\Night',
        u'\\EvilCorp\\World Plans\\Takeover']
    self._front_end.ExpandKeysRedirect(registry_key_paths)

    added_key_paths = [
        u'\\Software\\Wow6432Node\\Foobar',
        u'\\Software\\Wow6432Node\\Key\\SubKey\\MagicalKey']

    for added_key_path in added_key_paths:
      self.assertIn(added_key_path, registry_key_paths)

  def testGetRegistryFilePaths(self):
    """Tests the GetRegistryFilePaths function."""
    self._ConfigureSingleFileTest()
    expected_paths = [
        u'/Documents And Settings/.+/NTUSER.DAT',
        u'/Users/.+/NTUSER.DAT']

    paths = self._front_end.GetRegistryFilePaths(plugin_name=u'userassist')
    self.assertEqual(sorted(paths), sorted(expected_paths))

    # TODO: refactor this into a method.
    self._knowledge_base_object.pre_obj.sysregistry = u'C:/Windows/Foo'
    expected_paths = [u'C:/Windows/Foo/SOFTWARE']

    paths = self._front_end.GetRegistryFilePaths(
        registry_file_type=u'SOFTWARE')
    self.assertEqual(sorted(paths), sorted(expected_paths))

  def testGetRegistryHelpers(self):
    """Test the GetRegistryHelpers function."""
    self._ConfigureSingleFileTest()
    with self.assertRaises(ValueError):
      _ = self._front_end.GetRegistryHelpers()

    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_file_types=[u'SYSTEM'])

    self.assertEquals(len(registry_helpers), 1)

    registry_helper = registry_helpers[0]

    file_path = self._GetTestFilePath([u'SYSTEM'])
    self.assertEquals(registry_helper.path, file_path)

    self._ConfigureStorageMediaFileTest()
    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_file_types=[u'NTUSER'])

    self.assertEquals(len(registry_helpers), 3)

    registry_helper = registry_helpers[0]
    registry_helper.Open()
    expected_file_type = preg.REGISTRY_FILE_TYPE_NTUSER
    self.assertEquals(registry_helper.file_type, expected_file_type)
    self.assertEquals(registry_helper.name, u'NTUSER.DAT')
    self.assertEquals(registry_helper.collector_name, u'TSK')
    registry_helper.Close()

    registry_helpers = self._front_end.GetRegistryHelpers(
        plugin_names=[u'userassist'])
    self.assertEquals(len(registry_helpers), 3)

    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_file_types=[u'SAM'])
    self.assertEquals(len(registry_helpers), 1)

    # TODO: Add a test for getting Registry helpers from a storage media file
    # that contains VSS stores.

  def testGetRegistryPlugins(self):
    """Test the GetRegistryPlugin function."""
    self._ConfigureSingleFileTest()
    usb_plugins = self._front_end.GetRegistryPlugins(u'usb')
    self.assertIsNotNone(usb_plugins)

    usb_plugin_names = [plugin.NAME for plugin in usb_plugins]
    self.assertIn(u'windows_usb_devices', usb_plugin_names)
    self.assertIn(u'windows_usbstor_devices', usb_plugin_names)

    other_plugins = self._front_end.GetRegistryPlugins(u'user')
    self.assertIsNotNone(other_plugins)
    other_plugin_names = [plugin.NAME for plugin in other_plugins]

    self.assertIn(u'userassist', other_plugin_names)

  def testParseRegistry(self):
    """Test the ParseRegistryFile and ParseRegistryKey functions."""
    knowledge_base_values = {u'current_control_set': u'ControlSet001'}
    self._ConfigureSingleFileTest(knowledge_base_values=knowledge_base_values)

    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_file_types=[u'SYSTEM'])
    registry_helper = registry_helpers[0]

    plugins = self._front_end.GetRegistryPluginsFromRegistryType(u'SYSTEM')
    key_list = []
    plugin_list = []
    for plugin in plugins:
      plugin_list.append(plugin.NAME)
      key_list.extend(plugin.GetKeyPaths())

    self._front_end.ExpandKeysRedirect(key_list)

    parsed_data = self._front_end.ParseRegistryFile(
        registry_helper, key_paths=key_list, use_plugins=plugin_list)
    for key_parsed in parsed_data:
      self.assertIn(key_parsed, key_list)

    usb_parsed_data = parsed_data.get(
        u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USBSTOR', None)
    self.assertIsNotNone(usb_parsed_data)
    usb_key = usb_parsed_data.get(u'key', None)
    self.assertIsNotNone(usb_key)

    expected_key_path = (
        u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR')
    self.assertEquals(usb_key.path, expected_key_path)

    data = usb_parsed_data.get(u'data', None)
    self.assertIsNotNone(data)

    plugin_names = [plugin.NAME for plugin in data.keys()]
    self.assertIn(u'windows_usbstor_devices', plugin_names)

    usb_plugin = None
    for plugin in data.keys():
      if plugin.NAME == u'windows_usbstor_devices':
        usb_plugin = plugin
        break

    event_objects = data.get(usb_plugin, [])

    self.assertEquals(len(event_objects), 3)
    event_object = event_objects[2]

    self.assertEquals(event_object.data_type, u'windows:registry:key_value')

    parse_key_data = self._front_end.ParseRegistryKey(
        usb_key, registry_helper, use_plugins=u'windows_usbstor_devices')

    self.assertEquals(len(parse_key_data.keys()), 1)
    parsed_key_value = parse_key_data.values()[0]

    for index, event_object in enumerate(event_objects):
      parsed_key_event = parsed_key_value[index]
      self.assertEquals(
          event_object.EqualityString(), parsed_key_event.EqualityString())


if __name__ == '__main__':
  unittest.main()
