#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the helper for parser and plugin filter expressions."""

import unittest

from plaso.filters import parser_filter
from plaso.parsers import presets as parsers_presets

from tests.filters import test_lib


class ParserFilterExpressionHelperTest(test_lib.FilterTestCase):
  """Tests for the helper for parser and plugin filter expressions."""

  # pylint: disable=protected-access

  def testGetParserAndPluginsList(self):
    """Tests the _GetParserAndPluginsList function."""
    test_helper = parser_filter.ParserFilterExpressionHelper()

    expression = test_helper._GetParserAndPluginsList(
        {'excluded': set(['*', 'plugin1'])})
    self.assertEqual(expression, ['excluded', 'excluded/plugin1'])

  def testJoinExpression(self):
    """Tests the _JoinExpression function."""
    test_helper = parser_filter.ParserFilterExpressionHelper()

    expression = test_helper._JoinExpression({'excluded': set(['*'])}, {})
    self.assertEqual(expression, '!excluded')

    expression = test_helper._JoinExpression(
        {'excluded': set(['plugin1'])}, {'excluded': set(['*'])})
    self.assertEqual(expression, '!excluded/plugin1,excluded')

    expression = test_helper._JoinExpression(
        {'excluded': set(['plugin1', 'plugin2'])}, {'excluded': set(['*'])})
    self.assertEqual(expression, '!excluded/plugin1,!excluded/plugin2,excluded')

    expression = test_helper._JoinExpression({}, {'included': set(['*'])})
    self.assertEqual(expression, 'included')

    expression = test_helper._JoinExpression(
        {}, {'included': set(['*', 'plugin1'])})
    self.assertEqual(expression, 'included,included/plugin1')

    expression = test_helper._JoinExpression(
        {}, {'included': set(['plugin1', 'plugin2'])})
    self.assertEqual(expression, 'included/plugin1,included/plugin2')

    expression = test_helper._JoinExpression(
        {'excluded': set(['plugin1'])},
        {'excluded': set(['*']), 'included': set(['plugin2'])})
    self.assertEqual(expression, '!excluded/plugin1,excluded,included/plugin2')

    with self.assertRaises(RuntimeError):
      test_helper._JoinExpression(
          {'excluded': set(['plugin1'])}, {'included': set(['plugin1'])})

    with self.assertRaises(RuntimeError):
      test_helper._JoinExpression({'excluded': set(['plugin1'])}, {})

  def testExpandPreset(self):
    """Tests the _ExpandPreset function."""
    presets_file = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(presets_file)

    presets_manager = parsers_presets.ParserPresetsManager()
    presets_manager.ReadFromFile(presets_file)

    test_helper = parser_filter.ParserFilterExpressionHelper()

    parsers_and_plugins = {'win_gen': set(['*'])}
    test_helper._ExpandPreset(presets_manager, 'win_gen', parsers_and_plugins)

    expected_parsers_and_plugins = {
        'bencode': set(['*']),
        'czip': set(['oxml']),
        'filestat': set(['*']),
        'gdrive_synclog': set(['*']),
        'java_idx': set(['*']),
        'lnk': set(['*']),
        'mcafee_protection': set(['*']),
        'olecf': set(['*']),
        'pe': set(['*']),
        'prefetch': set(['*']),
        'sccm': set(['*']),
        'skydrive_log': set(['*']),
        'skydrive_log_old': set(['*']),
        'sqlite': set(['google_drive', 'skype']),
        'symantec_scanlog': set(['*']),
        'usnjrnl': set(['*']),
        'webhist': set(['*']),
        'winfirewall': set(['*']),
        'winjob': set(['*']),
        'winreg': set(['*'])}

    self.assertEqual(parsers_and_plugins, expected_parsers_and_plugins)

  def testExpandPresets(self):
    """Tests the ExpandPresets function."""
    presets_file = self._GetTestFilePath(['presets.yaml'])
    self._SkipIfPathNotExists(presets_file)

    presets_manager = parsers_presets.ParserPresetsManager()
    presets_manager.ReadFromFile(presets_file)

    test_helper = parser_filter.ParserFilterExpressionHelper()

    expected_parser_filter_expression = ','.join(sorted([
        '!utmp',
        'bencode',
        'binary_cookies',
        'chrome_cache',
        'chrome_preferences',
        'czip/oxml',
        'esedb/msie_webcache',
        'filestat',
        'firefox_cache',
        'gdrive_synclog',
        'java_idx',
        'lnk',
        'mcafee_protection',
        'msiecf',
        'olecf',
        'opera_global',
        'opera_typed_history',
        'pe',
        'plist/safari_history',
        'prefetch',
        'sccm',
        'skydrive_log',
        'skydrive_log_old',
        'sqlite/chrome_27_history',
        'sqlite/chrome_8_history',
        'sqlite/chrome_autofill',
        'sqlite/chrome_cookies',
        'sqlite/chrome_extension_activity',
        'sqlite/firefox_cookies',
        'sqlite/firefox_downloads',
        'sqlite/firefox_history',
        'sqlite/google_drive',
        'sqlite/skype',
        'symantec_scanlog',
        'usnjrnl',
        'winfirewall',
        'winjob',
        'winreg']))

    parser_filter_expression = test_helper.ExpandPresets(
        presets_manager, 'win_gen,!utmp')
    self.assertEqual(
        parser_filter_expression, expected_parser_filter_expression)

    expected_parser_filter_expression = ','.join(sorted([
        '!sccm',
        'bencode',
        'binary_cookies',
        'chrome_cache',
        'chrome_preferences',
        'czip/oxml',
        'esedb/msie_webcache',
        'filestat',
        'firefox_cache',
        'gdrive_synclog',
        'java_idx',
        'lnk',
        'mcafee_protection',
        'msiecf',
        'olecf',
        'opera_global',
        'opera_typed_history',
        'pe',
        'plist/safari_history',
        'prefetch',
        'skydrive_log',
        'skydrive_log_old',
        'sqlite/chrome_27_history',
        'sqlite/chrome_8_history',
        'sqlite/chrome_autofill',
        'sqlite/chrome_cookies',
        'sqlite/chrome_extension_activity',
        'sqlite/firefox_cookies',
        'sqlite/firefox_downloads',
        'sqlite/firefox_history',
        'sqlite/google_drive',
        'sqlite/skype',
        'symantec_scanlog',
        'usnjrnl',
        'winfirewall',
        'winjob',
        'winreg']))

    parser_filter_expression = test_helper.ExpandPresets(
        presets_manager, 'win_gen,!sccm')
    self.assertEqual(
        parser_filter_expression, expected_parser_filter_expression)

    parser_filter_expression = test_helper.ExpandPresets(
        presets_manager, 'olecf,!utmp')
    self.assertEqual(parser_filter_expression, '!utmp,olecf')

    parser_filter_expression = test_helper.ExpandPresets(presets_manager, '')
    self.assertIsNone(parser_filter_expression)

  def testSplitExpression(self):
    """Tests the SplitExpression function."""
    test_helper = parser_filter.ParserFilterExpressionHelper()

    excludes, includes = test_helper.SplitExpression('!excluded')
    self.assertEqual(excludes, {'excluded': set(['*'])})
    self.assertEqual(includes, {})

    excludes, includes = test_helper.SplitExpression(
        '!excluded,!excluded/plugin1,')
    self.assertEqual(excludes, {'excluded': set(['*', 'plugin1'])})
    self.assertEqual(includes, {})

    excludes, includes = test_helper.SplitExpression(
        '!excluded/plugin1,!excluded/plugin2,')
    self.assertEqual(excludes, {'excluded': set(['plugin1', 'plugin2'])})
    self.assertEqual(includes, {})

    excludes, includes = test_helper.SplitExpression('included')
    self.assertEqual(excludes, {})
    self.assertEqual(includes, {'included': set(['*'])})

    excludes, includes = test_helper.SplitExpression(
        'included,included/plugin1')
    self.assertEqual(excludes, {})
    self.assertEqual(includes, {'included': set(['*', 'plugin1'])})

    excludes, includes = test_helper.SplitExpression(
        'included/plugin1,included/plugin2')
    self.assertEqual(excludes, {})
    self.assertEqual(includes, {'included': set(['plugin1', 'plugin2'])})

    excludes, includes = test_helper.SplitExpression(
        '!excluded/plugin1,included/plugin2')
    self.assertEqual(excludes, {'excluded': set(['plugin1'])})
    self.assertEqual(includes, {'included': set(['plugin2'])})


if __name__ == '__main__':
  unittest.main()
