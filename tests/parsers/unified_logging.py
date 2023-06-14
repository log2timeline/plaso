#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple Unified Logging (AUL) tracev3 file parser."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.parsers import unified_logging

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class FormatStringOperatorTest(shared_test_lib.BaseTestCase):
  """Format string operator tests."""

  def testGetPythonFormatString(self):
    """Tests the GetPythonFormatString function."""
    format_string_operator = unified_logging.FormatStringOperator(specifier='a')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:f}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='A')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:f}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='c')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:c}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='C')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:c}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='d')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:d}')

    format_string_operator = unified_logging.FormatStringOperator(
        flags='-', specifier='d', width='5')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:<5d}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.3', specifier='d', width='3')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:03d}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='D')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:d}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='e')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:e}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='E')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:E}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='f')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:f}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.', specifier='f')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:.0f}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.2', specifier='f')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:.2f}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.*', specifier='f')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:f}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='F')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:F}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='g')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:g}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='G')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:G}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='i')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:d}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='o')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:o}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='O')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:o}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='p')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '0x{0:x}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='P')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:s}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.16', specifier='P')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:s}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='s')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:s}')

    format_string_operator = unified_logging.FormatStringOperator(
        specifier='s', width='6')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:>6s}')

    format_string_operator = unified_logging.FormatStringOperator(
        flags='-', specifier='s', width='6')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:<6s}')

    format_string_operator = unified_logging.FormatStringOperator(
        specifier='s', width='6')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:>6s}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.', specifier='s')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:s}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.0', specifier='s')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:s}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.16', specifier='s')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:.16s}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.*', specifier='s')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:s}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='S')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:s}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='u')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:d}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='U')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:d}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='x')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:x}')

    format_string_operator = unified_logging.FormatStringOperator(
        flags='#', specifier='x')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:#x}')

    format_string_operator = unified_logging.FormatStringOperator(
        flags='0', specifier='x', width='2')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:02x}')

    format_string_operator = unified_logging.FormatStringOperator(
        precision='.2', specifier='x', width='2')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:2x}')

    format_string_operator = unified_logging.FormatStringOperator(specifier='X')

    format_string = format_string_operator.GetPythonFormatString()
    self.assertEqual(format_string, '{0:X}')


class StringFormatterTest(shared_test_lib.BaseTestCase):
  """String formatter tests."""

  # pylint: disable=protected-access

  def testParseFormatString(self):
    """Tests the ParseFormatString function."""
    test_formatter = unified_logging.StringFormatter()

    test_formatter.ParseFormatString(None)
    self.assertEqual(test_formatter._decoders, [])
    self.assertIsNone(test_formatter._format_string)
    self.assertEqual(len(test_formatter._operators), 0)

    test_formatter.ParseFormatString('text')
    self.assertEqual(test_formatter._decoders, [])
    self.assertEqual(test_formatter._format_string, 'text')
    self.assertEqual(len(test_formatter._operators), 0)

    test_formatter.ParseFormatString('{text}')
    self.assertEqual(test_formatter._decoders, [])
    self.assertEqual(test_formatter._format_string, '{text}')
    self.assertEqual(len(test_formatter._operators), 0)

    test_formatter.ParseFormatString('%%')
    self.assertEqual(test_formatter._decoders, [])
    self.assertEqual(test_formatter._format_string, '%')
    self.assertEqual(len(test_formatter._operators), 0)

    test_formatter.ParseFormatString('%c')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%d')
    self.assertEqual(test_formatter._decoders, [['internal:i']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%3.3d')
    self.assertEqual(test_formatter._decoders, [['internal:i']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('{text: %d}')
    self.assertEqual(test_formatter._decoders, [['internal:i']])
    self.assertEqual(test_formatter._format_string, '{{text: {0:s}}}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString((
        '%{public,signpost.telemetry:number1,'
        'name=SOSSignpostNameSOSCCEnsurePeerRegistration}d'))
    self.assertEqual(test_formatter._decoders, [['signpost.telemetry:number1']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%D')
    self.assertEqual(test_formatter._decoders, [['internal:i']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%i')
    self.assertEqual(test_formatter._decoders, [['internal:i']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%o')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%O')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%p')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%u')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString(
        '%{signpost.description:attribute,public}llu')
    self.assertEqual(test_formatter._decoders, [
        ['signpost.description:attribute']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%U')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%x')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%#llx')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('0x%lx')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '0x{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('0x%2.2x')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '0x{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('0x%02x')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '0x{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%X')
    self.assertEqual(test_formatter._decoders, [['internal:u']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%e')
    self.assertEqual(test_formatter._decoders, [['internal:f']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%E')
    self.assertEqual(test_formatter._decoders, [['internal:f']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%f')
    self.assertEqual(test_formatter._decoders, [['internal:f']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%.f')
    self.assertEqual(test_formatter._decoders, [['internal:f']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%{signpost.telemetry:number2,public}.2f')
    self.assertEqual(test_formatter._decoders, [['signpost.telemetry:number2']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%F')
    self.assertEqual(test_formatter._decoders, [['internal:f']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%g')
    self.assertEqual(test_formatter._decoders, [['internal:f']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%G')
    self.assertEqual(test_formatter._decoders, [['internal:f']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%s')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%-6s')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%.*s')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%{public}s')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%{public}@')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%@')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%m')
    self.assertEqual(test_formatter._decoders, [['internal:m']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%.16P')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%{public,uuid_t}.16P')
    self.assertEqual(test_formatter._decoders, [['uuid_t']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%32s:%-5d')
    self.assertEqual(test_formatter._decoders, [['internal:s'], ['internal:i']])
    self.assertEqual(test_formatter._format_string, '{0:s}:{1:s}')
    self.assertEqual(len(test_formatter._operators), 2)

    format_string = test_formatter._operators[0].GetPythonFormatString()
    self.assertEqual(format_string, '{0:>32s}')

    format_string = test_formatter._operators[1].GetPythonFormatString()
    self.assertEqual(format_string, '{0:<5d}')

    test_formatter.ParseFormatString('"msg%{public}.0s"')
    self.assertEqual(test_formatter._decoders, [['internal:s']])
    self.assertEqual(test_formatter._format_string, '"msg{0:s}"')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString('%{public, location:escape_only}s')
    self.assertEqual(test_formatter._decoders, [['location:escape_only']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString(
        '%{private, mask.hash, mdnsresponder:ip_addr}.20P')
    self.assertEqual(test_formatter._decoders, [[
        'mask.hash', 'mdnsresponder:ip_addr']])
    self.assertEqual(test_formatter._format_string, '{0:s}')
    self.assertEqual(len(test_formatter._operators), 1)

    test_formatter.ParseFormatString((
        'Transform Manager cache hits: %d / %ld (%.2f%%). Size = %zu entries '
        '(events), %zu transforms, %zu bytes'))
    self.assertEqual(test_formatter._decoders, [
        ['internal:i'], ['internal:i'], ['internal:f'], ['internal:u'],
        ['internal:u'], ['internal:u']])
    self.assertEqual(test_formatter._format_string, (
        'Transform Manager cache hits: {0:s} / {1:s} ({2:s}%). Size = {3:s} '
        'entries (events), {4:s} transforms, {5:s} bytes'))
    self.assertEqual(len(test_formatter._operators), 6)

    test_formatter.ParseFormatString((
        '#%08x [%s] resolveDNSRecords -> public addresses: [%ld]%{private}@, '
        'favored servers: [%ld]%@, validityInterval %.f'))
    self.assertEqual(test_formatter._decoders, [
        ['internal:u'], ['internal:s'], ['internal:i'], ['internal:s'],
        ['internal:i'], ['internal:s'], ['internal:f']])
    self.assertEqual(test_formatter._format_string, (
        '#{0:s} [{1:s}] resolveDNSRecords -> public addresses: [{2:s}]{3:s}, '
        'favored servers: [{4:s}]{5:s}, validityInterval {6:s}'))
    self.assertEqual(len(test_formatter._operators), 7)


class BooleanFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Boolean value format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.BooleanFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x01\x00\x00\x00')
    self.assertEqual(formatted_value, 'true')

    formatted_value = test_decoder.FormatValue(b'\x00\x00\x00\x00')
    self.assertEqual(formatted_value, 'false')


class DateTimeInSecondsFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Date and time value in seconds format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.DateTimeInSecondsFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x78\x9b\x69\x64')
    self.assertEqual(formatted_value, '2023-05-21 04:18:00')


class ErrorCodeFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Error code format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.ErrorCodeFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x16\x00\x00\x00')
    self.assertEqual(formatted_value, 'Invalid argument')


class ExtendedErrorCodeFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Extended error code format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.ExtendedErrorCodeFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x02\x00\x00\x00')
    self.assertEqual(formatted_value, '[2: No such file or directory]')


class FileModeFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """File mode format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.FileModeFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\xc0\x01\x00\x00')
    self.assertEqual(formatted_value, '-rwx------')


class FloatingPointFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Floating-point format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.FloatingPointFormatStringDecoder()

    format_string_operator = unified_logging.FormatStringOperator(specifier='f')

    formatted_value = test_decoder.FormatValue(
        b'\xa4\x70\x45\x41', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '12.340000')

    formatted_value = test_decoder.FormatValue(
        b'\xec\x51\xb8\x1e\x45\x1a\xb3\x40',
        format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '4890.270000')


class IPv4FormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """IPv4 value format string decoder tests."""

  _VALUE_DATA = bytes(bytearray([0xc0, 0xa8, 0xcc, 0x62]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.IPv4FormatStringDecoder()

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA)
    self.assertEqual(formatted_value, '192.168.204.98')


class IPv6FormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """IPv6 value format string decoder tests."""

  _VALUE_DATA = bytes(bytearray([
      0x20, 0x01, 0x0d, 0xb8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00,
      0x00, 0x42, 0x83, 0x29]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.IPv6FormatStringDecoder()

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA)
    self.assertEqual(formatted_value, '2001:0db8:0000:0000:0000:ff00:0042:8329')


class LocationClientAuthorizationStatusFormatStringDecoder(
    shared_test_lib.BaseTestCase):
  """Location client authorization status format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.LocationClientAuthorizationStatusFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(b'\x02\x00\x00\x00')
    self.assertEqual(formatted_value, '"Denied"')


class LocationClientManagerStateFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Location client manager state value format string decoder tests."""

  _VALUE_DATA = bytes(bytearray([
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.LocationClientManagerStateFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA)
    self.assertEqual(formatted_value, (
        '{"locationRestricted":false,"locationServicesEnabledStatus":0}'))


class LocationLocationManagerStateFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Location location manager state value format string decoder tests."""

  _VALUE_DATA_V1 = bytes(bytearray([
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0xbf, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x59, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0x3f, 0x01, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00]))

  _VALUE_DATA_V2 = bytes(bytearray([
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0xbf, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x59, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0x3f, 0x01, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.LocationLocationManagerStateFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA_V1)
    self.assertEqual(formatted_value, (
        '{"previousAuthorizationStatusValid":false,"paused":false,'
        '"requestingLocation":false,"desiredAccuracy":100,'
        '"allowsBackgroundLocationUpdates":false,'
        '"dynamicAccuracyReductionEnabled":false,"distanceFilter":-1,'
        '"allowsLocationPrompts":true,"activityType":72057594037927937,'
        '"pausesLocationUpdatesAutomatially":0,'
        '"showsBackgroundLocationIndicator":false,"updatingLocation":false,'
        '"requestingRanging":false,"updatingHeading":false,'
        '"previousAuthorizationStatus":0,"allowsMapCorrection":false,'
        '"allowsAlteredAccessoryLoctions":false,"updatingRanging":false,'
        '"limitsPrecision":false,"headingFilter":1}'))

    test_decoder = (
        unified_logging.LocationLocationManagerStateFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA_V2)
    self.assertEqual(formatted_value, (
        '{"previousAuthorizationStatusValid":false,"paused":false,'
        '"requestingLocation":false,"updatingVehicleSpeed":false,'
        '"desiredAccuracy":100,"allowsBackgroundLocationUpdates":false,'
        '"dynamicAccuracyReductionEnabled":false,"distanceFilter":-1,'
        '"allowsLocationPrompts":true,"activityType":0,'
        '"groundAltitudeEnabled":false,"pausesLocationUpdatesAutomatially":1,'
        '"fusionInfoEnabled":false,"isAuthorizedForWidgetUpdates":false,'
        '"updatingVehicleHeading":false,"batchingLocation":false,'
        '"showsBackgroundLocationIndicator":false,"updatingLocation":false,'
        '"requestingRanging":false,"updatingHeading":false,'
        '"previousAuthorizationStatus":0,"allowsMapCorrection":true,'
        '"matchInfoEnabled":false,"allowsAlteredAccessoryLoctions":false,'
        '"updatingRanging":false,"limitsPrecision":false,'
        '"courtesyPromptNeeded":false,"headingFilter":1}'))


class LocationEscapeOnlyFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Location escape only format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.LocationEscapeOnlyFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'')
    self.assertEqual(formatted_value, '""')

    formatted_value = test_decoder.FormatValue(
        b'NSBundle </System/Library/LocationBundles/TimeZone.bundle>')
    self.assertEqual(formatted_value, (
        '"NSBundle <\\/System\\/Library\\/LocationBundles\\/TimeZone.bundle>"'))


class LocationSQLiteResultFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Location SQLite result format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.LocationSQLiteResultFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x00\x00\x00\x00')
    self.assertEqual(formatted_value, '"SQLITE_OK"')


class MaskHashFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Mask hash format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.MaskHashFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(
        b'\x1d\x1f\xd3\xfb\xe9\xa6Fj\xb72\x7f\xb6\x98a\x02\xb2')
    self.assertEqual(formatted_value, (
        '<mask.hash: \'HR/T++mmRmq3Mn+2mGECsg==\'>'))

    formatted_value = test_decoder.FormatValue(b'')
    self.assertEqual(formatted_value, '<mask.hash: (null)>')


class MDNSDNSCountersFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """mDNS DNS counters format string decoder tests."""

  _VALUE_DATA = bytes(bytearray([
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.MDNSDNSCountersFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA)
    self.assertEqual(formatted_value, '1/0/0/0')


class MDNSDNSHeaderFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """mDNS DNS header format string decoder tests."""

  _VALUE_DATA = bytes(bytearray([
      0x00, 0x00, 0x81, 0x80, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.MDNSDNSHeaderFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA)
    self.assertEqual(formatted_value, (
        'id: 0x0000 (0), flags: 0x8180 (R/Query, RD, RA, NoError), '
        'counts: 1/0/0/0'))


class MDNSDNSIdentifierAndFlagsFormatStringDecoder(
    shared_test_lib.BaseTestCase):
  """mDNS DNS header format string decoder tests."""

  _VALUE_DATA = bytes(bytearray([
      0x00, 0x01, 0xe9, 0x62, 0x00, 0x00, 0x00, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.MDNSDNSIdentifierAndFlagsFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA)
    self.assertEqual(formatted_value, (
        'id: 0x62E9 (25321), flags: 0x0100 (Q/Query, RD, NoError)'))


class MDNSProtocolFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """mDNS protocol format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.MDNSProtocolFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x01\x00\x00\x00')
    self.assertEqual(formatted_value, 'UDP')


class MDNSReasonFormatStringDecoder(shared_test_lib.BaseTestCase):
  """mDNS reason format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.MDNSReasonFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x03\x00\x00\x00')
    self.assertEqual(formatted_value, 'query-suppressed')


class MDNSResourceRecordTypeFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """mDNS resource record type format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.MDNSResourceRecordTypeFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x01\x00\x00\x00')
    self.assertEqual(formatted_value, 'A')


class OpenDirectoryErrorFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Open Directory error format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.OpenDirectoryErrorFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'\x00\x00\x00\x00')
    self.assertEqual(formatted_value, 'ODNoError')


class OpenDirectoryMembershipDetailsFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Open Directory membership details format string decoder tests."""

  _VALUE_DATA1 = bytes(bytearray([
      0x23, 0x58, 0x00, 0x00, 0x00, 0x2f, 0x4c, 0x6f, 0x63, 0x61, 0x6c, 0x2f,
      0x44, 0x65, 0x66, 0x61, 0x75, 0x6c, 0x74, 0x00]))

  _VALUE_DATA2 = bytes(bytearray([
      0x44, 0x77, 0x68, 0x65, 0x65, 0x6c, 0x00, 0x2f, 0x4c, 0x6f, 0x63, 0x61,
      0x6c, 0x2f, 0x44, 0x65, 0x66, 0x61, 0x75, 0x6c, 0x74, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.OpenDirectoryMembershipDetailsFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA1)
    self.assertEqual(formatted_value, 'user: 88@/Local/Default')

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA2)
    self.assertEqual(formatted_value, 'group: wheel@/Local/Default')


class OpenDirectoryMembershipTypeFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Open Directory membership type format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.OpenDirectoryMembershipTypeFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(b'\x06\x00\x00\x00')
    self.assertEqual(formatted_value, 'UUID')


class SignedIntegerFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Signed integer format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.SignedIntegerFormatStringDecoder()

    format_string_operator = unified_logging.FormatStringOperator(specifier='d')

    formatted_value = test_decoder.FormatValue(
        b'\x01', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '1')

    formatted_value = test_decoder.FormatValue(
        b'\x02\x01', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '258')

    formatted_value = test_decoder.FormatValue(
        b'\x04\x03\x02\x01', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '16909060')

    formatted_value = test_decoder.FormatValue(
        b'\x08\x07\x06\x05\x04\x03\x02\x01',
        format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '72623859790382856')


class SignpostDescriptionAttributeFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Signpost description attribute value format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.SignpostDescriptionAttributeFormatStringDecoder())

    format_string_operator = unified_logging.FormatStringOperator(specifier='s')

    formatted_value = test_decoder.FormatValue(
        b'', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.description#____#attribute#_##_###__##'))

    formatted_value = test_decoder.FormatValue(
        b'efilogin-helper', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.description#____#attribute#_##_#efilogin-helper##__##'))

    format_string_operator = unified_logging.FormatStringOperator(specifier='d')

    formatted_value = test_decoder.FormatValue(
        b'\x1d\xc6\x00\x00', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.description#____#attribute#_##_#50717##__##'))

    format_string_operator = unified_logging.FormatStringOperator(specifier='f')

    formatted_value = test_decoder.FormatValue(
        b'\xff\xff\xff\xff\x91\xff\xb9\x3f',
        format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.description#____#attribute#_##_#'
        '0.1015559434890747##__##'))


class SignpostDescriptionTimeFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Signpost description time value format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.SignpostDescriptionTimeFormatStringDecoder(
        time='begin')

    formatted_value = test_decoder.FormatValue(
        b'\x9f\x3b\xa6\x1e\xea\x00\x00\x00')
    self.assertEqual(formatted_value, (
        '__##__signpost.description#____#begin_time#_##_#1005536557983##__##'))

    test_decoder = unified_logging.SignpostDescriptionTimeFormatStringDecoder(
        time='end')

    formatted_value = test_decoder.FormatValue(
        b'\x4f\x2f\xc4\x2b\xea\x00\x00\x00')
    self.assertEqual(formatted_value, (
        '__##__signpost.description#____#end_time#_##_#1005756624719##__##'))


class SignpostTelemetryNumberFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Signpost telemetry number value format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.SignpostTelemetryNumberFormatStringDecoder()

    format_string_operator = unified_logging.FormatStringOperator(specifier='d')

    formatted_value = test_decoder.FormatValue(
        b'\x09\x00\x00\x00', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.telemetry#____#number1#_##_#9##__##'))

    format_string_operator = unified_logging.FormatStringOperator(specifier='f')

    formatted_value = test_decoder.FormatValue(
        b'\x00\x60\xbc\x40', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.telemetry#____#number1#_##_#5.88671875##__##'))

    formatted_value = test_decoder.FormatValue(
        b'\x00\x80\xbb\x40', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.telemetry#____#number1#_##_#5.859375##__##'))

    test_decoder = unified_logging.SignpostTelemetryNumberFormatStringDecoder(
        number=2)

    format_string_operator = unified_logging.FormatStringOperator(specifier='d')

    formatted_value = test_decoder.FormatValue(
        b'\x09\x00\x00\x00', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, (
        '__##__signpost.telemetry#____#number2#_##_#9##__##'))


class SignpostTelemetryStringFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Signpost telemetry string value format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.SignpostTelemetryStringFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'executeQueryBegin')
    self.assertEqual(formatted_value, (
        '__##__signpost.telemetry#____#string1#_##_#executeQueryBegin##__##'))

    test_decoder = unified_logging.SignpostTelemetryStringFormatStringDecoder(
        number=2)

    formatted_value = test_decoder.FormatValue(b'executeQueryBegin')
    self.assertEqual(formatted_value, (
        '__##__signpost.telemetry#____#string2#_##_#executeQueryBegin##__##'))


class SocketAddressFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Socket address value format string decoder tests."""

  _VALUE_DATA1 = bytes(bytearray([
      0x10, 0x02, 0x00, 0x00, 0x17, 0x32, 0x62, 0x82, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00]))

  _VALUE_DATA2 = bytes(bytearray([
      0x1c, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.SocketAddressFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(b'')
    self.assertEqual(formatted_value, '<NULL>')

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA1)
    self.assertEqual(formatted_value, '23.50.98.130')

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA2)
    self.assertEqual(formatted_value, '::')


class StringFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """String format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.StringFormatStringDecoder()

    format_string_operator = unified_logging.FormatStringOperator(specifier='s')

    formatted_value = test_decoder.FormatValue(
        b'', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '(null)')

    formatted_value = test_decoder.FormatValue(
        b'test', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, 'test')


class UnsignedIntegerFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """Unsigned integer format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.UnsignedIntegerFormatStringDecoder()

    format_string_operator = unified_logging.FormatStringOperator(specifier='u')

    formatted_value = test_decoder.FormatValue(
        b'\x01', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '1')

    formatted_value = test_decoder.FormatValue(
        b'\x02\x01', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '258')

    formatted_value = test_decoder.FormatValue(
        b'\x04\x03\x02\x01', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '16909060')

    formatted_value = test_decoder.FormatValue(
        b'\x08\x07\x06\x05\x04\x03\x02\x01',
       format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '72623859790382856')

    format_string_operator = unified_logging.FormatStringOperator(
        flags='#', specifier='x')

    formatted_value = test_decoder.FormatValue(
        b'\x00\x00\x00\x00', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '0')

    formatted_value = test_decoder.FormatValue(
        b'\x01\x00\x00\x00', format_string_operator=format_string_operator)
    self.assertEqual(formatted_value, '0x1')


class UUIDFormatStringDecoderTest(shared_test_lib.BaseTestCase):
  """UUID value format string decoder tests."""

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = unified_logging.UUIDFormatStringDecoder()

    formatted_value = test_decoder.FormatValue(
        b'\x1d\x1f\xd3\xfb\xe9\xa6Fj\xb72\x7f\xb6\x98a\x02\xb2')
    self.assertEqual(formatted_value, '1D1FD3FB-E9A6-466A-B732-7FB6986102B2')


class WindowsNTSecurityIdentifierFormatStringDecoderTest(
    shared_test_lib.BaseTestCase):
  """Open Directory membership details format string decoder tests."""

  _VALUE_DATA = bytes(bytearray([
      0x01, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x15, 0x00, 0x00, 0x00,
      0x16, 0x00, 0x00, 0x00, 0x17, 0x00, 0x00, 0x00, 0x18, 0x00, 0x00, 0x00,
      0x19, 0x00, 0x00, 0x00]))

  def testFormatValue(self):
    """Tests the FormatValue function."""
    test_decoder = (
        unified_logging.WindowsNTSecurityIdentifierFormatStringDecoder())

    formatted_value = test_decoder.FormatValue(self._VALUE_DATA)
    self.assertEqual(formatted_value, 'S-1-5-21-22-23-24-25')


class DSCFileTest(shared_test_lib.BaseTestCase):
  """Shared-Cache Strings (dsc) file tests."""

  # pylint: disable=protected-access

  def setUp(self):
    """Makes preparations before running an individual test."""
    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'unified_logging1.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)
    self._parent_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER,
        parent=test_path_spec, volume_index=0)

  def testReadFileHeader(self):
    """Tests the _ReadFileHeader function."""
    test_file_path = (
        '/private/var/db/uuidtext/dsc/BE7FE6AD45603AE2883E432F78B45062')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)
    file_object = file_entry.GetFileObject()

    test_file = unified_logging.DSCFile()
    file_header = test_file._ReadFileHeader(file_object)

    self.assertEqual(file_header.signature, b'hcsd')
    self.assertEqual(file_header.major_format_version, 2)
    self.assertEqual(file_header.minor_format_version, 0)
    self.assertEqual(file_header.number_of_ranges, 3491)
    self.assertEqual(file_header.number_of_uuids, 2274)

  def testReadImagePath(self):
    """Tests the _ReadImagePath function."""
    test_file_path = (
        '/private/var/db/uuidtext/dsc/BE7FE6AD45603AE2883E432F78B45062')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)
    file_object = file_entry.GetFileObject()

    test_file = unified_logging.DSCFile()
    uuid_path = test_file._ReadImagePath(file_object, 265718)

    self.assertEqual(uuid_path, '/System/Library/FeatureFlags')

  def testReadRangeDescriptors(self):
    """Test the _ReadRangeDescriptors function."""
    test_file_path = (
        '/private/var/db/uuidtext/dsc/BE7FE6AD45603AE2883E432F78B45062')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)
    file_object = file_entry.GetFileObject()

    test_file = unified_logging.DSCFile()
    ranges = list(test_file._ReadRangeDescriptors(file_object, 16, 2, 263))

    self.assertEqual(len(ranges), 263)
    self.assertEqual(ranges[10].data_offset, 265718)
    self.assertEqual(ranges[10].range_offset, 2014632)
    self.assertEqual(ranges[10].range_size, 464)

  # TODO: add test for _ReadString

  def testReadUUIDDescriptors(self):
    """Test the _ReadUUIDDescriptors function."""
    test_file_path = (
        '/private/var/db/uuidtext/dsc/BE7FE6AD45603AE2883E432F78B45062')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)
    file_object = file_entry.GetFileObject()

    test_file = unified_logging.DSCFile()
    uuids = list(test_file._ReadUUIDDescriptors(file_object, 83800, 2, 2274))

    self.assertEqual(len(uuids), 2274)
    self.assertEqual(uuids[197].text_offset, 193908736)
    self.assertEqual(uuids[197].text_size, 36864)
    self.assertEqual(uuids[197].image_path, '/usr/lib/libIOReport.dylib')

  # TODO: add test for GetImageValues

  def testReadFileObject(self):
    """Tests the ReadFileObject function."""
    test_file_path = (
        '/private/var/db/uuidtext/dsc/BE7FE6AD45603AE2883E432F78B45062')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    test_file = unified_logging.DSCFile()
    test_file.Open(file_entry)
    test_file.Close()


class TimesyncDatabaseFileTest(shared_test_lib.BaseTestCase):
  """Tests for the timesync database file."""

  # pylint: disable=protected-access

  def setUp(self):
    """Makes preparations before running an individual test."""
    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'unified_logging1.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)
    self._parent_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER,
        parent=test_path_spec, volume_index=0)

  def testReadFileRecord(self):
    """Tests the _ReadRecord method."""
    test_file_path = (
        '/private/var/db/Diagnostics/timesync/0000000000000002.timesync')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    test_file = unified_logging.TimesyncDatabaseFile()
    file_object = file_entry.GetFileObject()

    # Boot record
    record, _ = test_file._ReadRecord(file_object, 0)

    self.assertEqual(record.signature, b'\xb0\xbb')
    self.assertEqual(record.record_size, 48)
    self.assertEqual(record.timebase_numerator, 125)
    self.assertEqual(record.timebase_denominator, 3)
    self.assertEqual(record.timestamp, 1673487330693054000)
    self.assertEqual(record.time_zone_offset, 480)
    self.assertEqual(record.daylight_saving_flag, 0)

    # sync record
    record, _ = test_file._ReadRecord(file_object, 48)

    self.assertEqual(record.signature, b'Ts')
    self.assertEqual(record.record_size, 32)
    self.assertEqual(record.kernel_time, 1442026097)
    self.assertEqual(record.timestamp, 1673487385699687000)
    self.assertEqual(record.time_zone_offset, 480)
    self.assertEqual(record.daylight_saving_flag, 0)

  def testReadFileObject(self):
    """Tests the ReadFileObject method."""
    test_file_path = (
        '/private/var/db/Diagnostics/timesync/0000000000000002.timesync')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    test_file = unified_logging.TimesyncDatabaseFile()
    test_file.Open(file_entry)
    test_file.Close()


# TODO: add tests for TraceV3File


class UUIDTextFileTest(shared_test_lib.BaseTestCase):
  """Apple Unified Logging and Activity Tracing (uuidtext) file tests."""

  # pylint: disable=protected-access

  def setUp(self):
    """Makes preparations before running an individual test."""
    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'unified_logging1.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)
    self._parent_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER,
        parent=test_path_spec, volume_index=0)

  def testReadFileFooter(self):
    """Tests the _ReadFileFooter function."""
    test_file_path = (
        '/private/var/db/uuidtext/22/3ED293DBE031C889F9F7689D86339D')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    file_object = file_entry.GetFileObject()

    test_file = unified_logging.UUIDTextFile()
    file_footer = test_file._ReadFileFooter(file_object, 0x000003e4)

    self.assertIsNotNone(file_footer)

    expected_image_path = (
        '/System/Library/Frameworks/CryptoTokenKit.framework/PlugIns/'
        'pivtoken.appex/Contents/MacOS/pivtoken')
    self.assertEqual(file_footer.image_path, expected_image_path)

  def testReadFileHeader(self):
    """Tests the _ReadFileHeader function."""
    test_file_path = (
        '/private/var/db/uuidtext/22/3ED293DBE031C889F9F7689D86339D')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    file_object = file_entry.GetFileObject()

    test_file = unified_logging.UUIDTextFile()
    file_header = test_file._ReadFileHeader(file_object)

    self.assertIsNotNone(file_header)
    self.assertEqual(file_header.major_format_version, 2)
    self.assertEqual(file_header.minor_format_version, 1)
    self.assertEqual(file_header.number_of_entries, 2)

  def testReadString(self):
    """Tests the _ReadString function."""
    test_file_path = (
        '/private/var/db/uuidtext/22/3ED293DBE031C889F9F7689D86339D')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    test_file = unified_logging.UUIDTextFile()
    test_file.Open(file_entry)

    try:
      string = test_file._ReadString(test_file._file_object, 32)
    finally:
      test_file.Close()

    self.assertEqual(string, 'PIN')

  def testGetImagePath(self):
    """Tests the GetImagePath function."""
    test_file_path = (
        '/private/var/db/uuidtext/22/3ED293DBE031C889F9F7689D86339D')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    test_file = unified_logging.UUIDTextFile()
    test_file.Open(file_entry)

    try:
      image_path = test_file.GetImagePath()
    finally:
      test_file.Close()

    expected_image_path = (
        '/System/Library/Frameworks/CryptoTokenKit.framework/PlugIns/'
        'pivtoken.appex/Contents/MacOS/pivtoken')
    self.assertEqual(image_path, expected_image_path)

  def testGetString(self):
    """Tests the GetString function."""
    test_file_path = (
        '/private/var/db/uuidtext/22/3ED293DBE031C889F9F7689D86339D')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    test_file = unified_logging.UUIDTextFile()
    test_file.Open(file_entry)

    try:
      string = test_file.GetString(0x000069c4)
    finally:
      test_file.Close()

    self.assertEqual(string, 'PIN')

  def testReadFileObject(self):
    """Tests the ReadFileObject function."""
    test_file_path = (
        '/private/var/db/uuidtext/22/3ED293DBE031C889F9F7689D86339D')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(test_path_spec)

    test_file = unified_logging.UUIDTextFile()
    test_file.Open(file_entry)
    test_file.Close()


class UnifiedLoggingParserTest(test_lib.ParserTestCase):
  """Tests for the Apple Unified Logging (AUL) tracev3 file parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    test_file_path = os.path.join(
        shared_test_lib.TEST_DATA_PATH, 'unified_logging1.dmg')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_MODI, parent=test_path_spec)
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GPT, location='/p1',
        parent=test_path_spec)
    self._parent_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS_CONTAINER,
        parent=test_path_spec, volume_index=0)

  def testParseWithPersistTraceV3(self):
    """Tests the Parse function with a Persist tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Persist/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 83000)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_identifier': 0,
        'boot_identifier': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        'event_message': (
            'initialize_screen: b=BE3A18000, w=00000280, h=00000470, '
            'r=00000A00, d=00000000\n'),
        'event_type': 'logEvent',
        'message_type': 'Default',
        'pid': 0,
        'process_image_identifier': 'D1CD0AAF-523E-312F-9299-6116B1D511FE',
        'process_image_path': '/kernel',
        # 'recorded_time': '2023-01-12T01:35:35.240424704+00:00',
        'recorded_time': '2023-01-12T01:35:35.240424708+00:00',
        'sender_image_identifier': 'D1CD0AAF-523E-312F-9299-6116B1D511FE',
        'sender_image_path': '/kernel',
        'thread_identifier': 0}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 27)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithSignpostTraceV3(self):
    """Tests the Parse function with a Signpost tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Signpost/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 2466)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_identifier': 0,
        'boot_identifier': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'category': 'Speed',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        'event_message': (
            'Kext com.apple.driver.KextExcludeList v17.0.0 in codeless kext '
            'bundle com.apple.driver.KextExcludeList at /Library/Apple/System/'
            'Library/Extensions/AppleKextExcludeList.kext: FS contents are '
            'valid'),
        'event_type': 'signpostEvent',
        'message_type': None,
        'pid': 50,
        'process_image_identifier': '5FCEBDDD-0174-3777-BB92-E98174383008',
        'process_image_path': '/usr/libexec/kernelmanagerd',
        # 'recorded_time': '2023-01-12T01:36:31.338352128+00:00',
        'recorded_time': '2023-01-12T01:36:31.338352250+00:00',
        'sender_image_identifier': '5FCEBDDD-0174-3777-BB92-E98174383008',
        'sender_image_path': '/usr/libexec/kernelmanagerd',
        'signpost_identifier': 0xeeeeb0b5b2b2eeee,
        'signpost_name': 'validateExtFilesystem(into:)',
        'thread_identifier': 0x7cb}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWithSpecialTraceV3(self):
    """Tests the Parse function with a Special tracev3 file."""
    test_file_path = (
        '/private/var/db/Diagnostics/Special/0000000000000001.tracev3')
    test_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_APFS, location=test_file_path,
        parent=self._parent_path_spec)

    parser = unified_logging.UnifiedLoggingParser()
    storage_writer = self._ParseFileByPathSpec(test_path_spec, parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_events, 12159)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'activity_identifier': 0,
        'boot_identifier': 'DCA6F382-13F5-4A21-BF2B-4F1BE8B136BD',
        'data_type': 'macos:unified_logging:event',
        # 'euid': 0,
        'event_message': (
            'Failed to look up the port for "com.apple.windowserver.active" '
            '(1102)'),
        'event_type': 'logEvent',
        'message_type': 'Default',
        'pid': 24,
        'process_image_identifier': '36B63A88-3FE7-30FC-B7BA-46C45DD6B7D8',
        'process_image_path': '/usr/libexec/UserEventAgent',
        # 'recorded_time': '2023-01-12T01:36:27.111432704+00:00',
        'recorded_time': '2023-01-12T01:36:27.111432708+00:00',
        'sender_image_identifier': 'C0FDF86C-F960-37A3-A380-DB8700D43801',
        'sender_image_path': (
            '/System/Library/PrivateFrameworks/'
            'SkyLight.framework/Versions/A/SkyLight'),
        'subsystem': 'com.apple.SkyLight',
        'thread_identifier': 0x7d1}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
