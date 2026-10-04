#!/usr/bin/env python3
"""Tests for the tagging file."""

import unittest

from plaso.engine import tagging_file
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class TaggingFileTestCase(shared_test_lib.BaseTestCase):
    """Tests for the tagging file."""

    def testGetEventTaggingRules(self):
        """Tests the GetEventTaggingRules function."""
        test_file_path = self._GetTestFilePath(["tagging_file", "valid.txt"])
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        tagging_rules = tag_file.GetEventTaggingRules()
        self.assertEqual(len(tagging_rules), 5)

    def testGetEventTaggingRulesInvalidSyntax(self):
        """Tests the GetEventTaggingRules function on a file with invalid syntax."""
        test_file_path = self._GetTestFilePath(["tagging_file", "invalid_syntax.txt"])
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        with self.assertRaises(errors.TaggingFileError):
            tag_file.GetEventTaggingRules()

    def testValidate(self):
        """Tests the Validate function."""
        test_file_path = self._GetTestFilePath(["tagging_file", "valid.txt"])
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        findings = tag_file.Validate()
        self.assertEqual(findings, [])

    def testValidateDuplicateLabel(self):
        """Tests the Validate function on a file with a label defined twice."""
        test_file_path = self._GetTestFilePath(["tagging_file", "duplicate_label.txt"])
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        findings = tag_file.Validate()
        expected_findings = [(7, "Label defined more than once: application_execution")]
        self.assertEqual(findings, expected_findings)

    def testValidateInvalidEncoding(self):
        """Tests the Validate function on a file that is not UTF-8 encoded."""
        test_file_path = self._GetTestFilePath(["tagging_file", "invalid_encoding.txt"])
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        findings = tag_file.Validate()
        expected_findings = [
            (
                1,
                "Unable to decode line as UTF-8 with error: 'utf-8' codec can't decode "
                "byte 0xff in position 16: invalid start byte",
            )
        ]
        self.assertEqual(findings, expected_findings)

    def testValidateInvalidSyntax(self):
        """Tests the Validate function on a file with invalid syntax."""
        test_file_path = self._GetTestFilePath(["tagging_file", "invalid_syntax.txt"])
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        findings = tag_file.Validate()
        expected_findings = [
            (
                1,
                'Unsupported label: "Application Execution". A label must only consist '
                "of alphanumeric characters or underscores.",
            ),
            (
                4,
                'Unsupported label: "Invalid Tag". A label must only consist '
                "of alphanumeric characters or underscores.",
            ),
            (
                5,
                "Unable to compile rule: some text here with error: No token match "
                "for parser state: ARGUMENT at position 10: some text  <---> here",
            ),
            (
                7,
                'Unsupported label: "Partially Valid Tag". A label must only consist '
                "of alphanumeric characters or underscores.",
            ),
            (
                9,
                "Unable to compile rule: some other invalid text. with error: No "
                "token match for parser state: ARGUMENT at position 11: some other  "
                "<---> invalid text.",
            ),
        ]
        self.assertEqual(findings, expected_findings)

    def testValidateLabelWithoutRules(self):
        """Tests the Validate function on a file with labels without rules."""
        test_file_path = self._GetTestFilePath(
            ["tagging_file", "label_without_rules.txt"]
        )
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        findings = tag_file.Validate()
        expected_findings = [
            (1, "Label without rules: application_execution"),
            (6, "Label without rules: login_attempt"),
            (9, "Label without rules: security_event"),
        ]
        self.assertEqual(findings, expected_findings)

    def testValidateRuleWithoutLabel(self):
        """Tests the Validate function on a file with rules not attached to a label."""
        test_file_path = self._GetTestFilePath(
            ["tagging_file", "rule_without_label.txt"]
        )
        self._SkipIfPathNotExists(test_file_path)

        tag_file = tagging_file.TaggingFile(test_file_path)

        findings = tag_file.Validate()
        expected_findings = [
            (1, "Rule not attached to a label: data_type is 'fish:history:command'"),
            (5, "Rule not attached to a label: data_type is 'windows:lnk:link'"),
        ]
        self.assertEqual(findings, expected_findings)


if __name__ == "__main__":
    unittest.main()
