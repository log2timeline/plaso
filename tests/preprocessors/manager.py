#!/usr/bin/env python3
"""Tests for the preprocess plugins manager."""

import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.helpers import fake_file_system_builder
from dfvfs.helpers import file_system_searcher
from dfvfs.path import fake_path_spec
from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher

from plaso.preprocessors import interface
from plaso.preprocessors import manager
from plaso.preprocessors import mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class TestArtifactPreprocessorPlugin(interface.ArtifactPreprocessorPlugin):
    """Test artifact preprocessor plugin."""

    ARTIFACT_DEFINITION_NAME = "TestArtifactDefinition"

    # pylint: disable=unused-argument
    def ParseValueData(self, value_data):
        """Parses artifact value data for a preprocessing attribute.

        Args:
          value_data (object): artifact value data.
        """
        return


class SecondTestArtifactPreprocessorPlugin(TestArtifactPreprocessorPlugin):
    """Second test artifact preprocessor plugin."""

    ARTIFACT_DEFINITION_NAME = "SecondTestArtifactDefinition"


class PreprocessPluginsManagerTest(shared_test_lib.BaseTestCase):
    """Tests for the preprocess plugins manager."""

    # pylint: disable=protected-access

    def _CreateLinuxFileSystem(self):
        """Creates a fake file system with Linux configuration files.

        Returns:
          dfvfs.FakeFileSystem: file system.
        """
        file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
        file_system_builder.AddFile("/etc/hostname", b"plaso.kiddaland.net\n")
        file_system_builder.AddFile(
            "/etc/system-release", b"Fedora release 26 (Twenty Six)\n"
        )
        return file_system_builder.file_system

    def _CreateTestArtifactsRegistry(self):
        """Creates an artifact definitions registry from the test data.

        Returns:
          artifacts.ArtifactDefinitionsRegistry: artifact definitions registry.

        Raises:
          SkipTest: if the artifact definitions test data does not exist.
        """
        artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(artifacts_path)

        registry = artifacts_registry.ArtifactDefinitionsRegistry()
        reader = artifacts_reader.YamlArtifactsReader()
        registry.ReadFromDirectory(reader, artifacts_path)

        return registry

    def _CreateTestStorageWriter(self):
        """Creates a storage writer for testing purposes.

        Returns:
          StorageWriter: storage writer.
        """
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        return storage_writer

    def testCollectFromFileSystem(self):
        """Tests the CollectFromFileSystem function."""
        registry = self._CreateTestArtifactsRegistry()

        file_system = self._CreateLinuxFileSystem()
        mount_point = fake_path_spec.FakePathSpec(location="/")
        searcher = file_system_searcher.FileSystemSearcher(file_system, mount_point)

        storage_writer = self._CreateTestStorageWriter()
        test_mediator = mediator.PreprocessMediator(storage_writer)

        manager.PreprocessPluginsManager.CollectFromFileSystem(
            registry, test_mediator, searcher, file_system
        )

        self.assertEqual(test_mediator.hostname.name, "plaso.kiddaland.net")

        system_product = test_mediator.GetValue("operating_system_product")
        self.assertEqual(system_product, "Fedora release 26 (Twenty Six)")

        # Test with an artifact definitions registry without definitions.
        registry = artifacts_registry.ArtifactDefinitionsRegistry()
        test_mediator = mediator.PreprocessMediator(storage_writer)

        with self.assertLogs("preprocessors", level="WARNING") as log_context:
            manager.PreprocessPluginsManager.CollectFromFileSystem(
                registry, test_mediator, searcher, file_system
            )

        self.assertIn(
            "WARNING:preprocessors:Missing artifact definition: LinuxHostnameFile",
            log_context.output,
        )
        self.assertIsNone(test_mediator.hostname)
        self.assertIsNone(test_mediator.GetValue("operating_system_product"))

    def testCollectFromWindowsRegistry(self):
        """Tests the CollectFromWindowsRegistry function."""
        registry = self._CreateTestArtifactsRegistry()

        key_path_prefix = "HKEY_LOCAL_MACHINE\\Software"

        microsoft_key = dfwinreg_fake.FakeWinRegistryKey(
            "Microsoft", key_path_prefix=key_path_prefix, relative_key_path="Microsoft"
        )
        windows_nt_key = dfwinreg_fake.FakeWinRegistryKey(
            "Windows NT",
            key_path_prefix=key_path_prefix,
            relative_key_path="Microsoft\\Windows NT",
        )
        current_version_key = dfwinreg_fake.FakeWinRegistryKey(
            "CurrentVersion",
            key_path_prefix=key_path_prefix,
            relative_key_path="Microsoft\\Windows NT\\CurrentVersion",
        )
        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "ProductName",
            data="Windows 7 Ultimate".encode("utf-16-le"),
            data_type=dfwinreg_definitions.REG_SZ,
        )
        current_version_key.AddValue(registry_value)

        windows_nt_key.AddSubkey(current_version_key.name, current_version_key)
        microsoft_key.AddSubkey(windows_nt_key.name, windows_nt_key)

        registry_file = dfwinreg_fake.FakeWinRegistryFile(
            key_path_prefix=key_path_prefix
        )
        registry_file.AddKeyByPath("\\", microsoft_key)

        win_registry = dfwinreg_registry.WinRegistry()
        win_registry.MapFile(key_path_prefix, registry_file)

        searcher = registry_searcher.WinRegistrySearcher(win_registry)

        storage_writer = self._CreateTestStorageWriter()
        test_mediator = mediator.PreprocessMediator(storage_writer)

        manager.PreprocessPluginsManager.CollectFromWindowsRegistry(
            registry, test_mediator, searcher
        )

        system_product = test_mediator.GetValue("operating_system_product")
        self.assertEqual(system_product, "Windows 7 Ultimate")

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "preprocessing_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test with an artifact definitions registry without definitions.
        registry = artifacts_registry.ArtifactDefinitionsRegistry()
        test_mediator = mediator.PreprocessMediator(storage_writer)

        with self.assertLogs("preprocessors", level="WARNING") as log_context:
            manager.PreprocessPluginsManager.CollectFromWindowsRegistry(
                registry, test_mediator, searcher
            )

        self.assertIn(
            "WARNING:preprocessors:Missing artifact definition: WindowsProductName",
            log_context.output,
        )
        self.assertIsNone(test_mediator.GetValue("operating_system_product"))

    def testGetNames(self):
        """Tests the GetNames function."""
        names = manager.PreprocessPluginsManager.GetNames()
        self.assertIn("LinuxHostnameFile", names)
        self.assertIn("WindowsComputerName", names)
        self.assertNotIn("TestArtifactDefinition", names)

        manager.PreprocessPluginsManager.RegisterPlugin(TestArtifactPreprocessorPlugin)

        try:
            names = manager.PreprocessPluginsManager.GetNames()
            self.assertIn("TestArtifactDefinition", names)

        finally:
            manager.PreprocessPluginsManager.DeregisterPlugin(
                TestArtifactPreprocessorPlugin
            )

        names = manager.PreprocessPluginsManager.GetNames()
        self.assertNotIn("TestArtifactDefinition", names)

    def testRegistrationPlugin(self):
        """Tests RegisterPlugin and DeregisterPlugin functions."""
        number_of_plugins = len(manager.PreprocessPluginsManager._plugins)

        manager.PreprocessPluginsManager.RegisterPlugin(TestArtifactPreprocessorPlugin)
        self.assertEqual(
            len(manager.PreprocessPluginsManager._plugins), number_of_plugins + 1
        )

        with self.assertRaises(KeyError):
            manager.PreprocessPluginsManager.RegisterPlugin(
                TestArtifactPreprocessorPlugin
            )

        manager.PreprocessPluginsManager.DeregisterPlugin(
            TestArtifactPreprocessorPlugin
        )
        self.assertEqual(
            len(manager.PreprocessPluginsManager._plugins), number_of_plugins
        )

    def testRegisterPlugins(self):
        """Tests the RegisterPlugins function."""
        number_of_plugins = len(manager.PreprocessPluginsManager._plugins)

        plugin_classes = [
            TestArtifactPreprocessorPlugin,
            SecondTestArtifactPreprocessorPlugin,
        ]
        manager.PreprocessPluginsManager.RegisterPlugins(plugin_classes)

        try:
            self.assertEqual(
                len(manager.PreprocessPluginsManager._plugins), number_of_plugins + 2
            )
            self.assertIn(
                "testartifactdefinition", manager.PreprocessPluginsManager._plugins
            )
            self.assertIn(
                "secondtestartifactdefinition",
                manager.PreprocessPluginsManager._plugins,
            )

            with self.assertRaises(KeyError):
                manager.PreprocessPluginsManager.RegisterPlugins(
                    [TestArtifactPreprocessorPlugin]
                )

        finally:
            for plugin_class in plugin_classes:
                manager.PreprocessPluginsManager.DeregisterPlugin(plugin_class)

        self.assertEqual(
            len(manager.PreprocessPluginsManager._plugins), number_of_plugins
        )

    def testRunPlugins(self):
        """Tests the RunPlugins function."""
        registry = self._CreateTestArtifactsRegistry()

        file_system = self._CreateLinuxFileSystem()
        mount_point = fake_path_spec.FakePathSpec(location="/")

        storage_writer = self._CreateTestStorageWriter()
        test_mediator = mediator.PreprocessMediator(storage_writer)

        manager.PreprocessPluginsManager.RunPlugins(
            registry, file_system, mount_point, test_mediator
        )

        self.assertEqual(test_mediator.hostname.name, "plaso.kiddaland.net")

        system_product = test_mediator.GetValue("operating_system_product")
        self.assertEqual(system_product, "Fedora release 26 (Twenty Six)")

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "preprocessing_warning"
        )
        self.assertEqual(number_of_warnings, 0)


if __name__ == "__main__":
    unittest.main()
