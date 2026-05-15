#!/usr/bin/env python3
"""Tests that all parsers and plugins are imported correctly."""

import glob
import os
import unittest

from tests import test_lib


class ParserImportTest(test_lib.ImportCheckTestCase):
    """Tests that parser classes are imported correctly."""

    _IGNORABLE_FILES = frozenset(
        [
            "dtfabric_parser.py",
            "dtfabric_plugin.py",
            "interface.py",
            "logger.py",
            "manager.py",
            "mediator.py",
            "plugins.py",
            "presets.py",
        ]
    )

    def testParsersImported(self):
        """Tests that all parsers are imported."""
        self._AssertFilesImportedInInit(test_lib.PARSERS_PATH, self._IGNORABLE_FILES)

    def testPluginsImported(self):
        """Tests that all plugins are imported."""
        for plugin_directory in glob.glob(f"{test_lib.PARSERS_PATH:s}/*_plugins/"):
            plugin_directory_path = os.path.join(
                test_lib.PARSERS_PATH, plugin_directory
            )
            self._AssertFilesImportedInInit(
                plugin_directory_path, self._IGNORABLE_FILES
            )


if __name__ == "__main__":
    unittest.main()
