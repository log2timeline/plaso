#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.engine import knowledge_base
from plaso.frontend import preg

from tests.frontend import test_lib


class PregFrontendTest(test_lib.FrontendTestCase):
  """Tests for the preg front-end."""

  def setUp(self):
    """Sets up the necessary objects."""
    self._front_end = preg.PregFrontend()
    # TODO: Move this to a single file test and test storage media parsing as
    # well.
    self._front_end.SetSingleFile(True)
    registry_file_path = self._GetTestFilePath([u'SYSTEM'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=registry_file_path)

    self._front_end.SetSourcePath(registry_file_path)
    self._front_end.SetSourcePathSpecs([path_spec])
    self._knowledge_base_object = knowledge_base.KnowledgeBase()
    self._front_end.SetKnowledgeBase(self._knowledge_base_object)

  def testExpandKeysRedirect(self):
    """Tests the ExpandKeysRedirect function."""
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
    expected_paths = [
        u'/Documents And Settings/.+/NTUSER.DAT',
        u'/Users/.+/NTUSER.DAT']

    paths = self._front_end.GetRegistryFilePaths(plugin_name=u'userassist')
    self.assertEqual(sorted(paths), sorted(expected_paths))

    # TODO: refactor this into a method.
    self._knowledge_base_object.pre_obj.sysregistry = u'C:/Windows/Foo'
    expected_paths = [u'C:/Windows/Foo/SOFTWARE']

    paths = self._front_end.GetRegistryFilePaths(registry_type=u'SOFTWARE')
    self.assertEqual(sorted(paths), sorted(expected_paths))

  def testGetRegistryHelpers(self):
    """Test the GetRegistryHelpers function."""
    with self.assertRaises(ValueError):
      _ = self._front_end.GetRegistryHelpers()

    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_types=[u'SYSTEM'])

    self.assertEquals(len(registry_helpers), 1)

    registry_helper = registry_helpers[0]

    file_path = self._GetTestFilePath([u'SYSTEM'])
    self.assertEquals(registry_helper.path, file_path)
    # TODO: Add extracting Registry helper objects from a disk image, with and
    # without VSS.

  def testGetRegistryPlugins(self):
    """Test the GetRegistryPlugin function."""
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
    registry_helpers = self._front_end.GetRegistryHelpers(
        registry_types=[u'SYSTEM'])
    registry_helper = registry_helpers[0]

    plugins = self._front_end.GetRegistryPluginsFromRegistryType(u'SYSTEM')
    key_list = []
    plugin_list = []
    for plugin in plugins:
      plugin_list.append(plugin.NAME)
      key_list.extend(plugin.REG_KEYS)

    self._front_end.ExpandKeysRedirect(key_list)
    parsed_data = self._front_end.ParseRegistryFile(
        registry_helper, key_paths=key_list, use_plugins=plugin_list)
    for key_parsed in parsed_data:
      self.assertIn(key_parsed, key_list)

    usb_parsed_data = parsed_data.get(
        u'\\{current_control_set}\\Enum\\USBSTOR', None)
    self.assertIsNotNone(usb_parsed_data)
    usb_key = usb_parsed_data.get(u'key', None)
    self.assertIsNotNone(usb_key)
    self.assertEquals(usb_key.path, u'\\ControlSet001\\Enum\\USBSTOR')

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
