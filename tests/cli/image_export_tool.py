#!/usr/bin/env python3
"""Tests for the image export CLI tool."""

import json
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import vshadow_path_spec
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.cli import image_export_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class TestImageExportTool(image_export_tool.ImageExportTool):
    """Image export tool for testing.

    Attributes:
      sanitized_destination (tuple[str, str]): destination directory and
          filename returned by _CreateSanitizedDestination.
    """

    def __init__(self, sanitized_destination):
        """Initializes an image export tool for testing.

        Args:
          sanitized_destination (tuple[str, str]): destination directory and
              filename to return from _CreateSanitizedDestination.
        """
        super().__init__()
        self.sanitized_destination = sanitized_destination

    # pylint: disable=unused-argument
    def _CreateSanitizedDestination(
        self,
        source_file_entry,
        file_system_path_spec,
        source_data_stream_name,
        destination_path,
    ):
        """Creates a sanitized path of both destination directory and filename.

        Args:
          source_file_entry (dfvfs.FileEntry): file entry of the source file.
          file_system_path_spec (dfvfs.PathSpec): path specifications of the source
              file system to process.
          source_data_stream_name (str): name of the data stream of the source file
              entry.
          destination_path (str): path of the destination directory.

        Returns:
          tuple[str, str]: destination directory and filename.
        """
        return self.sanitized_destination


class TestFakeFileSystem:
    """A minimal fake file system for testing path splitting."""

    def __init__(self, path_segments=None):
        """Initializes a fake file system.

        Args:
          path_segments (Optional[list[str]]): pre-defined path segments.
        """
        super().__init__()
        self._path_segments = path_segments

    def SplitPath(self, path):
        """Splits a path into path segments.

        Args:
          path (str): path to split.

        Returns:
          list[str]: path segments.
        """
        if self._path_segments is not None:
            return list(self._path_segments)

        return [
            path_segment for path_segment in (path or "").split("/") if path_segment
        ]


class TestFakeFileEntry:
    """A minimal file entry for testing.

    Attributes:
      path_spec (PathSpec): path specification of the file entry.
    """

    def __init__(self, path_spec, path_segments=None):
        """Initializes a fake file entry.

        Args:
          path_spec (PathSpec): path specification of the file entry.
          path_segments (Optional[list[str]]): path segments to return for the
              location of the path specification, where None indicates that
              the location should be split on "/".
        """
        super().__init__()
        self._path_segments = path_segments
        self.path_spec = path_spec

    def GetFileSystem(self):
        """Retrieves a file system.

        Returns:
          TestFakeFileSystem: file system that splits paths.
        """
        return TestFakeFileSystem(path_segments=self._path_segments)


class ImageExportToolTest(test_lib.CLIToolTestCase):
    """Tests for the image export CLI tool."""

    # pylint: disable=protected-access

    _FILTER_FILE_DATA = "\n".join(
        [
            "description: Test filter.",
            "type: include",
            "path_separator: '/'",
            "paths: ['/a_directory/.+_file']",
            "",
        ]
    )

    def _GetTestScanNode(self, scan_context):
        """Retrieves the scan node for testing.

        Retrieves the first scan node, from the root upwards, with more or less
        than 1 sub node.

        Args:
          scan_context (dfvfs.SourceScanContext): scan context.

        Returns:
          dfvfs.SourceScanNode: scan node.
        """
        scan_node = scan_context.GetRootScanNode()
        while len(scan_node.sub_nodes) == 1:
            scan_node = scan_node.sub_nodes[0]

        return scan_node

    def _RecursiveList(self, path):
        """Recursively lists a file or directory.

        Args:
          path (str): path of the file or directory to list.

        Returns:
          list[str]: names of files and sub directories within the path.
        """
        results = []
        for sub_path, _, files in os.walk(path):
            if sub_path != path:
                results.append(sub_path)

            for file_entry in files:
                results.append(os.path.join(sub_path, file_entry))

        return results

    def testCalculateDigestHash(self):
        """Tests the _CalculateDigestHash function."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
        digest_hash = test_tool._CalculateDigestHash(file_entry, "")
        expected_digest_hash = (
            "c7fbc0e821c0871805a99584c6a384533909f68a6bbe9a2a687d28d9f3b10c16"
        )
        self.assertEqual(digest_hash, expected_digest_hash)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=12,
            location="/a_directory",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
        with self.assertRaises(dfvfs_errors.BackEndError):
            test_tool._CalculateDigestHash(file_entry, "")

    def testCreateSanitizedDestination(self):
        """Tests the _CreateSanitizedDestination function."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

        with shared_test_lib.TempDirectory() as temp_directory:
            target_directory, target_filename = test_tool._CreateSanitizedDestination(
                file_entry, tsk_path_spec, "", temp_directory
            )
            self.assertEqual(
                target_directory, os.path.join(temp_directory, "a_directory")
            )
            self.assertEqual(target_filename, "another_file")

            # Test with a data stream name that contains path separators.
            target_directory, target_filename = test_tool._CreateSanitizedDestination(
                file_entry, tsk_path_spec, "end/../../escaped.txt", temp_directory
            )
            self.assertEqual(
                target_directory, os.path.join(temp_directory, "a_directory")
            )
            self.assertEqual(target_filename, "another_file_end_.._.._escaped.txt")

            _, target_filename = test_tool._CreateSanitizedDestination(
                file_entry, tsk_path_spec, "end\\..\\..\\escaped.txt", temp_directory
            )
            self.assertEqual(target_filename, "another_file_end_.._.._escaped.txt")

    def testCreateSanitizedDestination_PathTraversal(self):
        """Tests _CreateSanitizedDestination for path traversal segments."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )

        # Test with a file system location that contains "." and ".." path
        # segments, such as those that can be found in crafted source files.
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/../../../../../escaped.txt",
            parent=os_path_spec,
        )
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

        with shared_test_lib.TempDirectory() as temp_directory:
            target_directory, target_filename = test_tool._CreateSanitizedDestination(
                file_entry, tsk_path_spec, "", temp_directory
            )
            self.assertEqual(
                target_directory,
                os.path.join(temp_directory, "_", "_", "_", "_", "_"),
            )
            self.assertEqual(target_filename, "escaped.txt")

            # The export destination must resolve to a path within the
            # destination directory.
            final_path = os.path.realpath(
                os.path.join(target_directory, target_filename)
            )
            self.assertEqual(
                os.path.commonpath([os.path.realpath(temp_directory), final_path]),
                os.path.realpath(temp_directory),
            )

        # Test with a VSS (vshadow) location that contains path separators and
        # ".." path segments. Such a location is read from the source and
        # therefore cannot be trusted.
        vshadow_spec = vshadow_path_spec.VShadowPathSpec(
            location="..\\..\\escaped",
            parent=os_path_spec,
        )
        top_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/another_file",
            parent=vshadow_spec,
        )
        file_entry = TestFakeFileEntry(top_path_spec)

        with shared_test_lib.TempDirectory() as temp_directory:
            target_directory, target_filename = test_tool._CreateSanitizedDestination(
                file_entry, top_path_spec, "", temp_directory
            )
            self.assertEqual(
                target_directory, os.path.join(temp_directory, "_", "_", "escaped")
            )
            self.assertEqual(target_filename, "another_file")

        # Test with a file system that does not return any path segments.
        file_entry = TestFakeFileEntry(os_path_spec, path_segments=[])

        with shared_test_lib.TempDirectory() as temp_directory:
            target_directory, target_filename = test_tool._CreateSanitizedDestination(
                file_entry, os_path_spec, "", temp_directory
            )
            self.assertEqual(target_directory, temp_directory)
            self.assertIsNone(target_filename)

    def testCreateDirectoryPath(self):
        """Tests the _CreateDirectoryPath function."""
        test_tool = image_export_tool.ImageExportTool()

        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "export")
            os.mkdir(destination_path)

            target_directory = os.path.join(destination_path, "a_directory", "b")
            test_tool._CreateDirectoryPath(destination_path, target_directory)

            self.assertTrue(os.path.isdir(target_directory))
            self.assertFalse(os.path.islink(target_directory))

    def testCreateDirectoryPathWithSymlinkedComponent(self):
        """Tests _CreateDirectoryPath does not create directories through a
        symbolic link.

        A symbolic link within the destination directory, that points outside
        of the destination directory, must not be used to create directories
        outside of the destination directory.
        """
        test_tool = image_export_tool.ImageExportTool()

        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "export")
            os.mkdir(destination_path)

            outside_path = os.path.join(temp_directory, "outside")
            os.mkdir(outside_path)

            symlink_path = os.path.join(destination_path, "a_symlink")
            try:
                os.symlink(outside_path, symlink_path)
            except OSError as exception:
                self.skipTest(f"Cannot create symlink: {exception!s}")

            with self.assertRaises(OSError):
                test_tool._CreateDirectoryPath(
                    destination_path, os.path.join(symlink_path, "sub")
                )

            # The directory must not have been created through the symbolic
            # link and the symbolic link must not have been replaced.
            self.assertTrue(os.path.islink(symlink_path))
            self.assertFalse(os.path.exists(os.path.join(outside_path, "sub")))

            # A path component that is a file must also be refused.
            blocking_path = os.path.join(destination_path, "a_file")
            with open(blocking_path, "wb") as file_object:
                file_object.write(b"a file\n")

            with self.assertRaises(OSError):
                test_tool._CreateDirectoryPath(
                    destination_path, os.path.join(blocking_path, "sub")
                )

            self.assertTrue(os.path.isfile(blocking_path))
            self.assertFalse(os.path.exists(os.path.join(blocking_path, "sub")))

    # TODO: add tests for _Extract.

    def testExtractDataStream(self):
        """Tests the _ExtractDataStream function."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
        with shared_test_lib.TempDirectory() as temp_directory:
            test_tool._ExtractDataStream(file_entry, "", temp_directory)

        # Test that a destination outside the destination path is not written.
        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "export")
            os.mkdir(destination_path)

            test_tool = TestImageExportTool(
                (destination_path, os.path.join("..", "escaped"))
            )
            test_tool._ExtractDataStream(file_entry, "", destination_path)

            self.assertFalse(os.path.exists(os.path.join(temp_directory, "escaped")))

    def testExtractDataStreamWithPathTraversal(self):
        """Tests _ExtractDataStream with path traversal segments."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/../../../../../escaped.txt",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "export")
            os.mkdir(destination_path)

            test_tool._ExtractDataStream(file_entry, "", destination_path)

            # The file is exported within the destination directory, not at
            # the location the file entry suggests.
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        destination_path, "_", "_", "_", "_", "_", "escaped.txt"
                    )
                )
            )
            self.assertFalse(
                os.path.exists(os.path.join(temp_directory, "escaped.txt"))
            )

    def testExtractDataStreamWithCollidingExportedFile(self):
        """Tests _ExtractDataStream with a destination under an exported file.

        A source file can map to an export destination below a path that is
        already exported as a file, for example due to a name collision.
        """
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "export")
            os.mkdir(destination_path)

            # Pre-create a file where a destination directory is expected.
            blocking_path = os.path.join(destination_path, "a")
            with open(blocking_path, "wb") as file_object:
                file_object.write(b"an existing file\n")

            test_tool = TestImageExportTool(
                (os.path.join(destination_path, "a", "b"), "c")
            )

            # The collision should not abort the extraction run.
            test_tool._ExtractDataStream(file_entry, "", destination_path)

            self.assertTrue(os.path.isfile(blocking_path))
            self.assertFalse(os.path.exists(os.path.join(destination_path, "a", "b")))

    def testExtractDataStreamWithPrePlantedSymlink(self):
        """Tests _ExtractDataStream with a pre-planted symlink in the destination.

        A symlink within the destination directory, that points outside of the
        destination directory, must not be used to write to a path outside of
        the destination directory.
        """
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "export")
            os.mkdir(destination_path)

            outside_path = os.path.join(temp_directory, "escaped")
            symlink_path = os.path.join(destination_path, "a_symlink")
            try:
                os.symlink(outside_path, symlink_path)
            except OSError as exception:
                self.skipTest(f"Cannot create symlink: {exception!s}")

            test_tool = TestImageExportTool((destination_path, "a_symlink"))
            test_tool._ExtractDataStream(file_entry, "", destination_path)

            self.assertFalse(os.path.exists(outside_path))
            self.assertTrue(os.path.islink(symlink_path))

    def testExtractFileEntry(self):
        """Tests the _ExtractFileEntry function."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        with shared_test_lib.TempDirectory() as temp_directory:
            file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
            test_tool._ExtractFileEntry(file_entry, temp_directory, output_writer)

    # TODO: add tests for _ExtractWithFilter.
    # TODO: add tests for _GetSourceFileSystem.

    def testParseExtensionsString(self):
        """Tests the _ParseExtensionsString function."""
        test_tool = image_export_tool.ImageExportTool()

        test_tool._ParseExtensionsString("txt")

    # TODO: add tests for _ParseFilterOptions.

    def testParseNamesString(self):
        """Tests the _ParseNamesString function."""
        test_tool = image_export_tool.ImageExportTool()

        test_tool._ParseNamesString("another_file")

    def testParseSignatureIdentifiers(self):
        """Tests the _ParseSignatureIdentifiers function."""
        test_tool = image_export_tool.ImageExportTool()

        test_tool._ParseSignatureIdentifiers(shared_test_lib.DATA_PATH, "gzip")

        with self.assertRaises(ValueError):
            test_tool._ParseSignatureIdentifiers(None, "gzip")

        with self.assertRaises(OSError):
            test_path = os.path.join(os.sep, "bogus")
            test_tool._ParseSignatureIdentifiers(test_path, "gzip")

    # TODO: add tests for _Preprocess.
    # TODO: add tests for _ReadSpecificationFile.

    def testWriteFileEntry(self):
        """Tests the _WriteFileEntry function."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)
        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "another_file")
            test_tool._WriteFileEntry(file_entry, "", destination_path)

    def testWriteFileEntryWithSymlinkedDestination(self):
        """Tests _WriteFileEntry does not write through a symbolic link.

        A symbolic link at the destination path, whether dangling or pointing
        to a file outside of the destination, must neither be followed as the
        destination of the exported contents nor replaced.
        """
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        test_tool = image_export_tool.ImageExportTool()

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK,
            inode=16,
            location="/a_directory/another_file",
            parent=os_path_spec,
        )

        file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

        with shared_test_lib.TempDirectory() as temp_directory:
            outside_path = os.path.join(temp_directory, "outside")
            with open(outside_path, "wb") as file_object:
                file_object.write(b"outside contents\n")

            symbolic_links = []
            for link_name, link_target in [
                ("symlink", outside_path),
                ("dangling_symlink", os.path.join(temp_directory, "missing")),
            ]:
                symlink_path = os.path.join(temp_directory, link_name)
                try:
                    os.symlink(link_target, symlink_path)
                except OSError as exception:
                    self.skipTest(f"Cannot create symlink: {exception!s}")

                test_tool._WriteFileEntry(file_entry, "", symlink_path)

                symbolic_links.append(symlink_path)

            # The symbolic links must not have been followed or replaced.
            for symlink_path in symbolic_links:
                self.assertTrue(os.path.islink(symlink_path))

            # The file the symbolic link points to must be unchanged.
            with open(outside_path, "rb") as file_object:
                self.assertEqual(file_object.read(), b"outside contents\n")

    # TODO: add tests for AddFilterOptions.

    def testListSignatureIdentifiers(self):
        """Tests the ListSignatureIdentifiers function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        test_tool._data_location = shared_test_lib.TEST_DATA_PATH

        test_tool.ListSignatureIdentifiers()

        expected_output = (
            "Available signature identifiers:\n7z, bzip2, elf, esedb, evt, evtx, "
            "ewf_e01, ewf_l01, exe_mz, gzip, lnk, msiecf,\nnk2, olecf, olecf_beta, "
            "pdf, pff, qcow, rar, regf, tar, tar_old, vhdi_footer,\nvhdi_header, "
            "wtcdb_cache, wtcdb_index, zip\n\n"
        )

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output.split("\n"))

        test_tool._data_location = self._GetTestFilePath(["tmp"])

        with self.assertRaises(errors.BadConfigOption):
            test_tool.ListSignatureIdentifiers()

    def testParseArguments(self):
        """Tests the ParseArguments function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        result = test_tool.ParseArguments([])
        self.assertFalse(result)

        # TODO: check output.
        # TODO: improve test coverage.

    def testParseOptions(self):
        """Tests the ParseOptions function."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path

        test_tool.ParseOptions(options)

        options = test_lib.TestOptions()

        with self.assertRaises(errors.BadConfigOption):
            test_tool.ParseOptions(options)

        # TODO: improve test coverage.

    def testPrintFilterCollection(self):
        """Tests the PrintFilterCollection function."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.date_filters = ["ctime,2012-05-25 15:59:00,2012-05-25 15:59:20"]
        options.image = test_file_path
        options.quiet = True

        test_tool.ParseOptions(options)

        test_tool.PrintFilterCollection()

        expected_output = "\n".join(
            [
                "Filters:",
                (
                    "\tctime between 2012-05-25 15:59:00.000000 and "
                    "2012-05-25 15:59:20.000000"
                ),
                "",
            ]
        )
        output = output_writer.ReadOutput()
        self.assertEqual(output, expected_output)

    def testProcessSourceWithImage(self):
        """Tests the ProcessSource function on a single partition image."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = self._GetTestFilePath(["ímynd.dd"])
        options.quiet = True

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_output = "\n".join(
                [
                    "Export started.",
                    f"Destination directory: {os.path.realpath(temp_directory):s}",
                    "Extracting file entries.",
                    "Export completed.",
                    "",
                    "",
                ]
            )

            output = output_writer.ReadOutput()
            self.assertEqual(output, expected_output)

    def testProcessSourceWithSymlinkedDestination(self):
        """Tests ProcessSource refuses a symbolic linked destination directory.

        A symbolic link as the destination directory must be refused, such
        that the exported contents are not written to the directory the
        symbolic link points to.
        """
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True

        with shared_test_lib.TempDirectory() as temp_directory:
            real_directory = os.path.join(temp_directory, "real")
            os.mkdir(real_directory)

            symlink_path = os.path.join(temp_directory, "symlink")
            try:
                os.symlink(real_directory, symlink_path)
            except OSError as exception:
                self.skipTest(f"Cannot create symlink: {exception!s}")

            options.path = symlink_path

            test_tool.ParseOptions(options)

            with self.assertRaises(errors.BadConfigOption):
                test_tool.ProcessSource()

            self.assertEqual(output_writer.ReadOutput(), "")

            # The directory the symbolic link points to must remain empty.
            self.assertEqual(os.listdir(real_directory), [])

    def testProcessSourceWithIntermediateSymlinkedDestination(self):
        """Tests ProcessSource accepts a destination below an intermediate symbolic
        link.

        Only the destination directory itself must not be a symbolic link, an
        intermediate symbolic link, for example /tmp which is commonly a
        symbolic link, must remain a valid part of the destination path.
        """
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True

        with shared_test_lib.TempDirectory() as temp_directory:
            real_directory = os.path.join(temp_directory, "real")
            os.mkdir(real_directory)

            symlink_path = os.path.join(temp_directory, "symlink")
            try:
                os.symlink(real_directory, symlink_path)
            except OSError as exception:
                self.skipTest(f"Cannot create symlink: {exception!s}")

            destination_path = os.path.join(symlink_path, "export")
            options.path = destination_path

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_output = "\n".join(
                [
                    "Export started.",
                    (
                        "Destination directory: "
                        f"{os.path.realpath(destination_path):s}"
                    ),
                    "Extracting file entries.",
                    "Export completed.",
                    "",
                    "",
                ]
            )

            output = output_writer.ReadOutput()
            self.assertEqual(output, expected_output)

            # The exported contents must be below the directory the symbolic
            # link points to.
            real_destination_path = os.path.join(real_directory, "export")
            self.assertGreater(len(self._RecursiveList(real_destination_path)), 1)

    def testProcessSourceWithSymlinkedHashesFile(self):
        """Tests ProcessSource does not write hashes.json through a symbolic link.

        A pre-planted symbolic link for the hashes file within the destination
        directory, pointing to a path outside of the destination directory,
        must not be followed when the hashes file is written.
        """
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True

        with shared_test_lib.TempDirectory() as temp_directory:
            destination_path = os.path.join(temp_directory, "export")
            os.mkdir(destination_path)

            outside_path = os.path.join(temp_directory, "outside_hashes")
            symlink_path = os.path.join(destination_path, "hashes.json")
            try:
                os.symlink(outside_path, symlink_path)
            except OSError as exception:
                self.skipTest(f"Cannot create symlink: {exception!s}")

            options.path = destination_path

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            # The exported contents must be within the destination directory.
            self.assertGreater(len(self._RecursiveList(destination_path)), 1)

            # The symbolic link must not have been followed or replaced and
            # the path it points to must not have been written.
            self.assertTrue(os.path.islink(symlink_path))
            self.assertFalse(os.path.exists(outside_path))

    def testProcessSourceExtractWithDateTimeFilter(self):
        """Tests the ProcessSource function with a date time filter."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.date_filters = ["ctime,2012-05-25 15:59:00,2012-05-25 15:59:20"]
        options.image = test_file_path
        options.quiet = True

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "a_directory"),
                    os.path.join(temp_directory, "a_directory", "a_file"),
                    os.path.join(temp_directory, "hashes.json"),
                ]
            )

            extracted_files = self._RecursiveList(temp_directory)
            self.assertEqual(sorted(extracted_files), expected_extracted_files)

    def testProcessSourceExtractWithExtensionsFilter(self):
        """Tests the ProcessSource function with an extensions filter."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.extensions_string = "txt"
        options.image = test_file_path
        options.quiet = True

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "passwords.txt"),
                    os.path.join(temp_directory, "hashes.json"),
                ]
            )

            extracted_files = self._RecursiveList(temp_directory)
            self.assertEqual(sorted(extracted_files), expected_extracted_files)

    def testProcessSourceExtractWithNamesFilter(self):
        """Tests the ProcessSource function with a names filter."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.names_string = "another_file"
        options.quiet = False

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "a_directory"),
                    os.path.join(temp_directory, "a_directory", "another_file"),
                    os.path.join(temp_directory, "hashes.json"),
                ]
            )

            extracted_files = self._RecursiveList(temp_directory)

            self.assertEqual(sorted(extracted_files), expected_extracted_files)

    def testProcessSourceExtractWithFilter(self):
        """Tests the ProcessSource function with a filter file."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True

        with shared_test_lib.TempDirectory() as temp_directory:
            filter_file = os.path.join(temp_directory, "filter_file.yaml")
            with open(filter_file, "wt", encoding="utf-8") as file_object:
                file_object.write(self._FILTER_FILE_DATA)

            options.file_filter = filter_file
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "a_directory"),
                    os.path.join(temp_directory, "a_directory", "another_file"),
                    os.path.join(temp_directory, "a_directory", "a_file"),
                    os.path.join(temp_directory, "filter_file.yaml"),
                    os.path.join(temp_directory, "hashes.json"),
                ]
            )

            extracted_files = self._RecursiveList(temp_directory)

        self.assertEqual(sorted(extracted_files), expected_extracted_files)

    def testProcessSourceExtractWithArtifactsFilter(self):
        """Tests the ProcessSource function with a artifacts filter file."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True
        options.artifact_filter_string = "TestFilesImageExport"

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "a_directory"),
                    os.path.join(temp_directory, "a_directory", "another_file"),
                    os.path.join(temp_directory, "a_directory", "a_file"),
                    os.path.join(temp_directory, "hashes.json"),
                ]
            )

            extracted_files = self._RecursiveList(temp_directory)

        self.assertEqual(sorted(extracted_files), expected_extracted_files)

    def testProcessSourceExtractWithArtifactsGroupFilter(self):
        """Tests the ProcessSource function with a group artifacts filter file."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True
        options.artifact_filter_string = "TestGroupExport"

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "a_directory"),
                    os.path.join(temp_directory, "a_directory", "another_file"),
                    os.path.join(temp_directory, "a_directory", "a_file"),
                    os.path.join(temp_directory, "passwords.txt"),
                    os.path.join(temp_directory, "hashes.json"),
                ]
            )

            extracted_files = self._RecursiveList(temp_directory)

        self.assertEqual(sorted(extracted_files), expected_extracted_files)

    def testProcessSourceExtractWithSignaturesFilter(self):
        """Tests the ProcessSource function with a signatures filter."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["syslog_image.dd"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True
        options.signature_identifiers = "gzip"

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "logs"),
                    os.path.join(temp_directory, "logs", "sys.tgz"),
                    os.path.join(temp_directory, "hashes.json"),
                ]
            )

            extracted_files = self._RecursiveList(temp_directory)

            self.assertEqual(sorted(extracted_files), expected_extracted_files)

    def testOutputJsonFile(self):
        """Tests the content of the output JSON file."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["ext4_with_binaries.dd"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.signature_identifiers = "elf"

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_json_data = [
                {
                    "sha256": (
                        "553c231c45eda751710eabb479d08668f70464c14e60064190a7ec206f26b5"
                        "f5"
                    ),
                    "paths": [os.path.join("bin", "bzcat")],
                },
                {
                    "sha256": (
                        "a106276270db8d3fe80a96dbb52f14f23f42a29bea12c68ac0f88d2e916471"
                        "af"
                    ),
                    "paths": [
                        os.path.join("bin", "echo"),
                        os.path.join("home", "echo"),
                    ],
                },
                {
                    "sha256": (
                        "e21de6c5af94fa9d4e7f3295c8d25b93ab3d2d65982f5ef53c801669cc82dc"
                        "47"
                    ),
                    "paths": [os.path.join("sbin", "visudo")],
                },
                {
                    "sha256": (
                        "129f4d0e36b38742fdfa8f1ea9a014818e4ce5c41d4a889435aecee58a1c7c"
                        "39"
                    ),
                    "paths": [os.path.join("sbin", "tune2fs")],
                },
            ]
            hashes_file_path = os.path.join(temp_directory, "hashes.json")
            with open(hashes_file_path, "r", encoding="utf-8") as file_object:
                json_data = json.load(file_object)

            json_data.sort(key=lambda digest: digest["sha256"])
            expected_json_data.sort(key=lambda digest: digest["sha256"])
            self.assertEqual(json_data, expected_json_data)

    def testProcessSourceEnableArtifactsMap(self):
        """Tests the ProcessSource function with artifacts map enabled.

        This test uses plaso/test_data/image.qcow2 which has directories matching
        artifact filters: [TestGroupExport, TestFiles3, TestFiles4,
        TestFilesImageExport] in plaso/test_data/artifacts/artifacts_filters.yaml

        plaso/test_data/image.qcow2 files and directories:
          ├── a_directory/
          │   ├── a_file
          │   └── another_file
          ├── lost+found/
          └── passwords.txt
        """
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True
        options.artifact_filter_string = "TestGroupExport"
        options.enable_artifacts_map = True

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            expected_extracted_files = sorted(
                [
                    os.path.join(temp_directory, "a_directory"),
                    os.path.join(temp_directory, "a_directory", "another_file"),
                    os.path.join(temp_directory, "a_directory", "a_file"),
                    os.path.join(temp_directory, "passwords.txt"),
                    os.path.join(temp_directory, "hashes.json"),
                    os.path.join(temp_directory, "artifacts_map.json"),
                ]
            )
            expected_json_data = {
                "TestFiles3": [
                    f"a_directory{os.sep}another_file",
                    f"a_directory{os.sep}a_file",
                ],
                "TestFiles4": [f"a_directory{os.sep}another_file", "passwords.txt"],
            }

            extracted_files = self._RecursiveList(temp_directory)
            self.assertEqual(sorted(extracted_files), expected_extracted_files)

            # Verify content of artifacts_map.json
            artifacts_map_file_path = os.path.join(temp_directory, "artifacts_map.json")
            with open(artifacts_map_file_path, "r", encoding="utf-8") as file_object:
                artifacts_map = json.load(file_object)

            self.assertTrue(isinstance(artifacts_map, dict))
            self.assertEqual(expected_json_data, artifacts_map)

    def testProcessSourceEnableArtifactsMap_NonMatchingPaths(self):
        """Tests ProcessSource with artifacts map enabled and no matching paths.

        This test uses plaso/test_data/image.qcow2 which has directories matching
        artifact filters: [TestGroupExport, TestFiles3, TestFiles4,
        TestFilesImageExport] in plaso/test_data/artifacts/artifacts_filters.yaml

        plaso/test_data/image.qcow2 files and directories:
          ├── a_directory/
          │   ├── a_file
          │   └── another_file
          ├── lost+found/
          └── passwords.txt
        """
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True
        # Use a valid artifact that will not match anything in the test image.
        options.artifact_filter_string = "TestGroupExtract"
        options.enable_artifacts_map = True

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            # Verify that no files were extracted.
            # Only artifacts_map.json and hashes.json should exist.
            self.assertEqual(
                sorted(os.listdir(temp_directory)),
                sorted(["hashes.json", "artifacts_map.json"]),
            )

            # Verify that the trie has no matching paths for image.qcow2.
            self.assertIsNotNone(test_tool._filter_collection._artifacts_trie)
            self.assertNotIn(
                "a_directory",
                test_tool._filter_collection._artifacts_trie.root.children[
                    os.sep
                ].children,
            )

            # Verify that artifacts_map.json is created but empty
            artifacts_map_file_path = os.path.join(temp_directory, "artifacts_map.json")
            with open(artifacts_map_file_path, "r", encoding="utf-8") as file_object:
                artifacts_map = json.load(file_object)

            self.assertEqual(artifacts_map, {})

    def testProcessSourceEnableArtifactsMap_EmptyFilter(self):
        """Tests ProcessSource with artifacts map enabled and an empty filter."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["image.qcow2"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True
        options.artifact_filter_string = ""  # Empty filter
        options.enable_artifacts_map = True

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)

            test_tool.ProcessSource()

            # Verify that artifacts_map.json is created but empty
            artifacts_map_file_path = os.path.join(temp_directory, "artifacts_map.json")
            with open(artifacts_map_file_path, "r", encoding="utf-8") as file_object:
                artifacts_map = json.load(file_object)

            self.assertEqual(artifacts_map, {})

    def testProcessSourceWithFile(self):
        """Tests the ProcessSource function with Registry files."""
        test_artifacts_path = self._GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_file_path = self._GetTestFilePath(["SYSTEM"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.artifact_definitions_path = test_artifacts_path
        options.image = test_file_path
        options.quiet = True
        options.artifact_filter_string = "TestRegistry"

        with shared_test_lib.TempDirectory() as temp_directory:
            options.path = temp_directory

            test_tool.ParseOptions(options)
            test_tool.ProcessSource()

            output = output_writer.ReadOutput()
            source_types = ", ".join(test_tool._SOURCE_TYPES_TO_PREPROCESS)
            message = (
                f'Input must be one of "{source_types:s}", type: "file" is not '
                f"supported.\n"
            )
            self.assertEqual(output, message)


if __name__ == "__main__":
    unittest.main()
