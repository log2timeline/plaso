#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import unittest

from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.engine import knowledge_base
from plaso.frontend import preg

from tests import test_lib as shared_test_lib


class PregFrontendTest(shared_test_lib.BaseTestCase):
  """Tests for the preg front-end."""

  def _ConfigureSingleFileTest(self, knowledge_base_values=None):
    """Configure a single file test.

    Args:
      knowledge_base_values: optional dict containing the knowledge base
                             values.

    Returns:
      A front-end object (instance of PregFrontend).
    """
    front_end = preg.PregFrontend()
    front_end.SetSingleFile(True)
    registry_file_path = self._GetTestFilePath([u'SYSTEM'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=registry_file_path)

    front_end.SetSourcePath(registry_file_path)
    front_end.SetSourcePathSpecs([path_spec])

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.iteritems():
        knowledge_base_object.SetValue(identifier, value)

    front_end.SetKnowledgeBase(knowledge_base_object)
    return front_end

  @shared_test_lib.skipUnlessHasTestFile([u'registry_test.dd'])
  def _ConfigureStorageMediaFileTest(self):
    """Configure a test against a storage media file.

    Returns:
      A front-end object (instance of PregFrontend).
    """
    front_end = preg.PregFrontend()
    front_end.SetSingleFile(False)

    knowledge_base_object = knowledge_base.KnowledgeBase()
    front_end.SetKnowledgeBase(knowledge_base_object)

    storage_media_path = self._GetTestFilePath([u'registry_test.dd'])

    test_source_scanner = source_scanner.SourceScanner()
    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(storage_media_path)
    test_source_scanner.Scan(scan_context)

    # Getting the most upper node.
    scan_node = scan_context.GetRootScanNode()
    while scan_node.sub_nodes:
      scan_node = scan_node.sub_nodes[0]

    front_end.SetSourcePath(storage_media_path)
    front_end.SetSourcePathSpecs([scan_node.path_spec])
    return front_end

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testExpandKeysRedirect(self):
    """Tests the ExpandKeysRedirect function."""
    front_end = self._ConfigureSingleFileTest()
    registry_key_paths = [
        u'\\Software\\Foobar',
        u'\\Software\\Key\\SubKey\\MagicalKey',
        u'\\Canons\\Blast\\Night',
        u'\\EvilCorp\\World Plans\\Takeover']
    front_end.ExpandKeysRedirect(registry_key_paths)

    added_key_paths = [
        u'\\Software\\Wow6432Node\\Foobar',
        u'\\Software\\Wow6432Node\\Key\\SubKey\\MagicalKey']

    for added_key_path in added_key_paths:
      self.assertIn(added_key_path, registry_key_paths)

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetRegistryFilePaths(self):
    """Tests the GetRegistryFilePaths function."""
    front_end = self._ConfigureSingleFileTest()

    expected_paths = [u'%UserProfile%\\NTUSER.DAT']
    registry_file_types = [u'NTUSER']
    paths = front_end.GetRegistryFilePaths(registry_file_types)
    self.assertEqual(sorted(paths), sorted(expected_paths))

    expected_paths = [u'%SystemRoot%\\System32\\config\\SOFTWARE']
    registry_file_types = [u'SOFTWARE']
    paths = front_end.GetRegistryFilePaths(registry_file_types)
    self.assertEqual(sorted(paths), sorted(expected_paths))

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  @shared_test_lib.skipUnlessHasTestFile([u'registry_test.dd'])
  def testGetRegistryHelpers(self):
    """Tests the GetRegistryHelpers function."""
    front_end = self._ConfigureSingleFileTest()
    with self.assertRaises(ValueError):
      front_end.GetRegistryHelpers()

    registry_helpers = front_end.GetRegistryHelpers(
        registry_file_types=[u'SYSTEM'])

    self.assertEquals(len(registry_helpers), 1)

    registry_helper = registry_helpers[0]

    file_path = self._GetTestFilePath([u'SYSTEM'])
    self.assertEquals(registry_helper.path, file_path)

    front_end = self._ConfigureStorageMediaFileTest()
    registry_helpers = front_end.GetRegistryHelpers(
        registry_file_types=[u'NTUSER'])

    self.assertEquals(len(registry_helpers), 3)

    registry_helper = registry_helpers[0]
    registry_helper.Open()
    expected_file_type = preg.REGISTRY_FILE_TYPE_NTUSER
    self.assertEquals(registry_helper.file_type, expected_file_type)
    self.assertEquals(registry_helper.name, u'NTUSER.DAT')
    self.assertEquals(registry_helper.collector_name, u'TSK')
    registry_helper.Close()

    registry_helpers = front_end.GetRegistryHelpers(
        plugin_names=[u'userassist'])
    self.assertEquals(len(registry_helpers), 3)

    registry_helpers = front_end.GetRegistryHelpers(
        registry_file_types=[u'SAM'])
    self.assertEquals(len(registry_helpers), 1)

    # TODO: Add a test for getting Registry helpers from a storage media file
    # that contains VSS stores.

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetRegistryPlugins(self):
    """Tests the GetRegistryPlugin function."""
    front_end = self._ConfigureSingleFileTest()
    usb_plugins = front_end.GetRegistryPlugins(u'usb')
    self.assertIsNotNone(usb_plugins)

    usb_plugin_names = [plugin.NAME for plugin in usb_plugins]
    self.assertIn(u'windows_usb_devices', usb_plugin_names)
    self.assertIn(u'windows_usbstor_devices', usb_plugin_names)

    other_plugins = front_end.GetRegistryPlugins(u'user')
    self.assertIsNotNone(other_plugins)
    other_plugin_names = [plugin.NAME for plugin in other_plugins]

    self.assertIn(u'userassist', other_plugin_names)

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testParseRegistry(self):
    """Tests the ParseRegistryFile and ParseRegistryKey functions."""
    front_end = self._ConfigureSingleFileTest()

    registry_helpers = front_end.GetRegistryHelpers(
        registry_file_types=[u'SYSTEM'])
    registry_helper = registry_helpers[0]

    plugins = front_end.GetRegistryPluginsFromRegistryType(u'SYSTEM')
    key_list = []
    plugin_list = []
    for plugin in plugins:
      plugin_list.append(plugin.NAME)
      key_list.extend(plugin.GetKeyPaths())

    front_end.ExpandKeysRedirect(key_list)

    parsed_data = front_end.ParseRegistryFile(
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

    self.assertEquals(len(event_objects), 5)
    event_object = event_objects[2]

    self.assertEquals(event_object.data_type, u'windows:registry:key_value')

    parse_key_data = front_end.ParseRegistryKey(
        usb_key, registry_helper, use_plugins=u'windows_usbstor_devices')

    self.assertEquals(len(parse_key_data.keys()), 1)
    parsed_key_value = parse_key_data.values()[0]

    for index, event_object in enumerate(event_objects):
      parsed_key_event = parsed_key_value[index]
      self.assertEquals(
          event_object.EqualityString(), parsed_key_event.EqualityString())


if __name__ == '__main__':
  unittest.main()
