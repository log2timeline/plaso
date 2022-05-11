# -*- coding: utf-8 -*-
"""IPS file plugin related functions and classes for testing."""

from plaso.parsers import ips_parser

from tests.parsers import test_lib


class IPSPluginTestCase(test_lib.ParserTestCase):
  """IPS parser plugin test case."""

  def _OpenIPSFile(self, path_segments):
    """Opens an IPS log file.

    Args:
      path_segments (list[str]): path segments inside the test data directory.

    Returns:
      tuple: containing:
          file_entry (dfvfs.FileEntry): file entry of the IPS log file.
          IPSFile: IPS log file.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    file_entry = self._GetTestFileEntry(path_segments)

    ips_file = ips_parser.IPSFile()
    file_object = file_entry.GetFileObject()

    ips_file.Open(file_object)

    return file_entry, ips_file
