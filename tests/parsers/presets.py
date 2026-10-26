#!/usr/bin/env python3
"""Tests for parser and parser plugin presets."""

import io
import unittest

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.parsers import presets

from tests import test_lib as shared_test_lib


class ParserPresetTest(shared_test_lib.BaseTestCase):
    """Tests for the parser and parser plugin preset."""

    def testInitialize(self):
        """Tests the __init__ function."""
        test_definition = presets.ParserPreset("test", ["parser1", "parser2"])
        self.assertIsNotNone(test_definition)


class ParserPresetsManagerTest(shared_test_lib.BaseTestCase):
    """Tests for the parser and parser plugin presets manager."""

    _LINUX_PARSERS = [
        "bash_history",
        "bencode",
        "czip/oxml",
        "dockerjson",
        "dpkg",
        "filestat",
        "gdrive_synclog",
        "olecf",
        "pls_recall",
        "popularity_contest",
        "selinux",
        "sqlite/google_drive",
        "sqlite/skype",
        "sqlite/zeitgeist",
        "syslog",
        "systemd_journal",
        "utmp",
        "vsftpd",
        "webhist",
        "xchatlog",
        "xchatscrollback",
        "zsh_extended_history",
    ]

    _MACOS_PARSERS = [
        "asl_log",
        "bash_history",
        "bencode",
        "bsm_log",
        "cups_ipp",
        "czip/oxml",
        "filestat",
        "fseventsd",
        "gdrive_synclog",
        "mac_appfirewall_log",
        "mac_keychain",
        "mac_securityd",
        "macwifi",
        "olecf",
        "plist",
        "sqlite/appusage",
        "sqlite/google_drive",
        "sqlite/imessage",
        "sqlite/ls_quarantine",
        "sqlite/mac_document_versions",
        "sqlite/mackeeper_cache",
        "sqlite/skype",
        "syslog",
        "utmpx",
        "webhist",
        "zsh_extended_history",
    ]

    _PRESETS_YAML_DATA = "\n".join(
        [
            "name: first",
            "parsers:",
            "- parser1",
            "- parser2/plugin1",
            "---",
            "name: second",
            "deprecated: true",
            "operating_systems:",
            "- family: Linux",
            "parsers:",
            "- parser3",
            "",
        ]
    )

    # pylint: disable=protected-access

    def testReadParserPresetValues(self):
        """Tests the _ReadParserPresetValues function."""
        test_manager = presets.ParserPresetsManager()

        preset_definition_values = {
            "name": "test",
            "operating_systems": [{"family": "MacOS"}],
            "parsers": ["parser1", "parser2/plugin1"],
        }
        test_preset = test_manager._ReadParserPresetValues(preset_definition_values)
        self.assertEqual(test_preset.name, "test")
        self.assertEqual(test_preset.parsers, ["parser1", "parser2/plugin1"])
        self.assertFalse(test_preset.deprecated)
        self.assertEqual(len(test_preset.operating_systems), 1)
        self.assertEqual(test_preset.operating_systems[0].family, "MacOS")

        preset_definition_values = {
            "deprecated": True,
            "name": "test",
            "parsers": ["parser1"],
        }
        test_preset = test_manager._ReadParserPresetValues(preset_definition_values)
        self.assertTrue(test_preset.deprecated)
        self.assertEqual(test_preset.operating_systems, [])

        with self.assertRaises(errors.MalformedPresetError):
            test_manager._ReadParserPresetValues(None)

        with self.assertRaises(errors.MalformedPresetError):
            test_manager._ReadParserPresetValues({"parsers": ["parser1"]})

        with self.assertRaises(errors.MalformedPresetError):
            test_manager._ReadParserPresetValues({"name": "test"})

        with self.assertRaises(errors.MalformedPresetError):
            test_manager._ReadParserPresetValues({"name": "test", "parsers": []})

        preset_definition_values = {
            "name": "test",
            "operating_systems": [{"version": "1"}],
            "parsers": ["parser1"],
        }
        with self.assertRaises(errors.MalformedPresetError):
            test_manager._ReadParserPresetValues(preset_definition_values)

    def testReadPresetsFromFileObject(self):
        """Tests the _ReadPresetsFromFileObject function."""
        test_manager = presets.ParserPresetsManager()

        file_object = io.StringIO(self._PRESETS_YAML_DATA)
        test_presets = list(test_manager._ReadPresetsFromFileObject(file_object))

        self.assertEqual(len(test_presets), 2)

        self.assertEqual(test_presets[0].name, "first")
        self.assertEqual(test_presets[0].parsers, ["parser1", "parser2/plugin1"])
        self.assertFalse(test_presets[0].deprecated)
        self.assertEqual(test_presets[0].operating_systems, [])

        self.assertEqual(test_presets[1].name, "second")
        self.assertEqual(test_presets[1].parsers, ["parser3"])
        self.assertTrue(test_presets[1].deprecated)
        self.assertEqual(len(test_presets[1].operating_systems), 1)
        self.assertEqual(test_presets[1].operating_systems[0].family, "Linux")

        # Test with a malformed first preset definition.
        file_object = io.StringIO("name: first\n")
        with self.assertRaisesRegex(errors.MalformedPresetError, "^At start "):
            list(test_manager._ReadPresetsFromFileObject(file_object))

        # Test with a malformed second preset definition.
        file_object = io.StringIO("name: first\nparsers:\n- parser1\n---\nname: x\n")
        with self.assertRaisesRegex(errors.MalformedPresetError, "^After: first "):
            list(test_manager._ReadPresetsFromFileObject(file_object))

    def testGetNames(self):
        """Tests the GetNames function."""
        test_file_path = self._GetTestFilePath(["presets.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        test_manager = presets.ParserPresetsManager()
        test_manager.ReadFromFile(test_file_path)

        test_names = list(test_manager.GetNames())
        self.assertEqual(len(test_names), 7)

        expected_names = sorted(
            ["android", "linux", "macos", "webhist", "win7", "win_gen", "winxp"]
        )
        self.assertEqual(test_names, expected_names)

    def testGetParsersByPreset(self):
        """Tests the GetParsersByPreset function."""
        test_file_path = self._GetTestFilePath(["presets.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        test_manager = presets.ParserPresetsManager()
        test_manager.ReadFromFile(test_file_path)

        parser_names = test_manager.GetParsersByPreset("linux")
        self.assertEqual(parser_names, self._LINUX_PARSERS)

        with self.assertRaises(KeyError):
            test_manager.GetParsersByPreset("bogus")

    def testGetPresetByName(self):
        """Tests the GetPresetByName function."""
        test_file_path = self._GetTestFilePath(["presets.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        test_manager = presets.ParserPresetsManager()
        test_manager.ReadFromFile(test_file_path)

        test_preset = test_manager.GetPresetByName("linux")
        self.assertIsNotNone(test_preset)
        self.assertEqual(test_preset.name, "linux")

        self.assertEqual(test_preset.parsers, self._LINUX_PARSERS)

        test_preset = test_manager.GetPresetByName("bogus")
        self.assertIsNone(test_preset)

    def testGetPresetsByOperatingSystem(self):
        """Tests the GetPresetsByOperatingSystem function."""
        test_file_path = self._GetTestFilePath(["presets.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        test_manager = presets.ParserPresetsManager()
        test_manager.ReadFromFile(test_file_path)

        operating_system = artifacts.OperatingSystemArtifact(family="MacOS")

        test_presets = test_manager.GetPresetsByOperatingSystem(operating_system)
        self.assertEqual(len(test_presets), 1)
        self.assertEqual(test_presets[0].name, "macos")

        self.assertEqual(test_presets[0].parsers, self._MACOS_PARSERS)

        operating_system = artifacts.OperatingSystemArtifact(family="bogus")

        test_presets = test_manager.GetPresetsByOperatingSystem(operating_system)
        self.assertEqual(len(test_presets), 0)

    def testGetPresetsInformation(self):
        """Tests the GetPresetsInformation function."""
        test_file_path = self._GetTestFilePath(["presets.yaml"])
        self._SkipIfPathNotExists(test_file_path)

        test_manager = presets.ParserPresetsManager()
        test_manager.ReadFromFile(test_file_path)

        parser_presets_information = test_manager.GetPresetsInformation()
        self.assertGreaterEqual(len(parser_presets_information), 1)

        available_parser_names = [name for name, _ in parser_presets_information]
        self.assertIn("linux", available_parser_names)

    # TODO add tests for ReadFromFile


if __name__ == "__main__":
    unittest.main()
