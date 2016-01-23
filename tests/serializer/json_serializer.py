#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the serializer object implementation using JSON."""

import collections
import json
import unittest

from plaso.lib import event
from plaso.serializer import json_serializer
from plaso.storage import collection

import pytz


class JSONSerializerTestCase(unittest.TestCase):
  """Tests for a JSON serializer object."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _TestReadSerialized(self, serializer_object, json_dict):
    """Tests the ReadSerialized function.

    Args:
      serializer_object: the JSON serializer object.
      json_dict: the JSON dict.

    Returns:
      The unserialized object.
    """
    # We use json.dumps to make sure the dict does not serialize into
    # an invalid JSON string e.g. one that contains string prefixes
    # like b'' or u''.
    json_string = json.dumps(json_dict)
    unserialized_object = serializer_object.ReadSerialized(json_string)

    self.assertIsNotNone(unserialized_object)
    return unserialized_object

  def _TestWriteSerialized(
      self, serializer_object, unserialized_object, expected_json_dict):
    """Tests the WriteSerialized function.

    Args:
      serializer_object: the JSON serializer object.
      unserialized_object: the unserialized object.
      expected_json_dict: the expected JSON dict.

    Returns:
      The serialized JSON string.
    """
    json_string = serializer_object.WriteSerialized(unserialized_object)

    # We use json.loads here to compare dicts since we cannot pre-determine
    # the actual order of values in the JSON string.
    json_dict = json.loads(json_string)
    self.assertEqual(json_dict, expected_json_dict)

    return json_string


class JSONAnalysisReportSerializerTest(JSONSerializerTestCase):
  """Tests for the JSON analysis report serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    # TODO: preserve the tuples in the report dict.
    self._report_dict = {
        u'dude': [
            [u'Google Keep - notes and lists',
             u'hmjkmjkepdijhoojdojkdfohbdgmmhki']
        ],
        u'frank': [
            [u'YouTube', u'blpcfgokakmgnkcojhhkbfbldkacnbeo'],
            [u'Google Play Music', u'icppfcnhkcmnfdhfhphakoifcfokfdhg']
        ]
    }

    self._report_text = (
        u' == USER: dude ==\n'
        u'  Google Keep - notes and lists [hmjkmjkepdijhoojdojkdfohbdgmmhki]\n'
        u'\n'
        u' == USER: frank ==\n'
        u'  Google Play Music [icppfcnhkcmnfdhfhphakoifcfokfdhg]\n'
        u'  YouTube [blpcfgokakmgnkcojhhkbfbldkacnbeo]\n'
        u'\n')

    # TODO: add report_array and _anomalies tests.

    self._json_dict = {
        u'__type__': u'AnalysisReport',
        u'_anomalies': [],
        u'_tags': [{
            u'__type__': u'EventTag',
            u'_tags': [u'This is a test.', u'Also a test.'],
            u'comment': u'This is a test event tag.',
            u'event_uuid': u'403818f93dce467bac497ef0f263fde8'
        }],
        u'plugin_name': u'chrome_extension_test',
        u'report_dict': self._report_dict,
        u'text': self._report_text,
        u'time_compiled': 1431978243000000}

    self._serializer = json_serializer.JSONAnalysisReportSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    self._TestReadSerialized(self._serializer, self._json_dict)

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""

    event_tag = event.EventTag()

    event_tag.event_uuid = u'403818f93dce467bac497ef0f263fde8'
    event_tag.comment = u'This is a test event tag.'
    event_tag._tags = [u'This is a test.', u'Also a test.']

    self.assertTrue(event_tag.IsValidForSerialization())
    analysis_report = event.AnalysisReport(u'chrome_extension_test')

    analysis_report.report_dict = self._report_dict
    analysis_report.text = self._report_text
    analysis_report.time_compiled = 1431978243000000
    analysis_report.SetTags([event_tag])

    self._TestWriteSerialized(
        self._serializer, analysis_report, self._json_dict)


class JSONEventObjectSerializerTest(JSONSerializerTestCase):
  """Tests for the JSON event object serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._json_dict = {
        u'__type__': u'EventObject',
        u'a_tuple': [
            u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35],
        u'binary_string': {
            u'__type__': u'bytes',
            u'stream': u'=C0=90=90binary'},
        u'data_type': u'test:event2',
        u'empty_string': u'',
        u'integer': 34,
        u'my_dict': {
            u'a': u'not b',
            u'an': [234, 32],
            u'c': 34,
            u'list': [u'sf', 234]
        },
        u'my_list': [u'asf', 4234, 2, 54, u'asf'],
        u'string': u'Normal string',
        u'timestamp_desc': u'Written',
        u'timestamp': 1234124,
        u'uuid': u'5a78777006de4ddb8d7bbe12ab92ccf8',
        u'unicode_string': u'And I am a unicorn.',
        u'zero_integer': 0
    }

    self._serializer = json_serializer.JSONEventObjectSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    event_object = self._TestReadSerialized(self._serializer, self._json_dict)

    # An integer value containing 0 should get stored.
    self.assertTrue(hasattr(event_object, u'zero_integer'))

    attribute_value = getattr(event_object, u'integer', 0)
    self.assertEqual(attribute_value, 34)

    attribute_value = getattr(event_object, u'my_list', [])
    self.assertEqual(len(attribute_value), 5)

    attribute_value = getattr(event_object, u'string', u'')
    self.assertEqual(attribute_value, u'Normal string')

    attribute_value = getattr(event_object, u'unicode_string', u'')
    self.assertEqual(attribute_value, u'And I am a unicorn.')

    attribute_value = getattr(event_object, u'a_tuple', ())
    self.assertEqual(len(attribute_value), 4)

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""
    event_object = event.EventObject()

    event_object.data_type = u'test:event2'
    event_object.timestamp = 1234124
    event_object.timestamp_desc = u'Written'
    # Prevent the event object for generating its own UUID.
    event_object.uuid = u'5a78777006de4ddb8d7bbe12ab92ccf8'

    event_object.binary_string = b'\xc0\x90\x90binary'
    event_object.empty_string = u''
    event_object.zero_integer = 0
    event_object.integer = 34
    event_object.string = u'Normal string'
    event_object.unicode_string = u'And I am a unicorn.'
    event_object.my_list = [u'asf', 4234, 2, 54, u'asf']
    event_object.my_dict = {
        u'a': u'not b', u'c': 34, u'list': [u'sf', 234], u'an': [234, 32]}
    event_object.a_tuple = (
        u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35)
    event_object.null_value = None

    json_string = self._TestWriteSerialized(
        self._serializer, event_object, self._json_dict)

    event_object = self._serializer.ReadSerialized(json_string)

    # TODO: fix this.
    # An empty string should not get stored.
    # self.assertFalse(hasattr(event_object, u'empty_string'))

    # A None (or Null) value should not get stored.
    # self.assertFalse(hasattr(event_object, u'null_value'))


class JSONEventTagSerializerTest(JSONSerializerTestCase):
  """Test for the JSON Event Tag serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._event_uuid = u'403818f93dce467bac497ef0f263fde8'
    self._json_dict = {
        u'event_uuid': self._event_uuid,
        u'comment': u'This is a test event tag.',
        u'_tags':  [u'This is a test.', u'Also a test.'],
    }

    self._serializer = json_serializer.JSONEventTagSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    self._TestReadSerialized(self._serializer, self._json_dict)

  def testWriteSerializer(self):
    """Tests the WriteSerialized function."""
    event_tag = event.EventTag()

    event_tag.event_uuid = self._event_uuid
    event_tag.comment = u'This is a test event tag.'
    event_tag._tags = [u'This is a test.', u'Also a test.']
    self.assertTrue(event_tag.IsValidForSerialization())
    self._TestWriteSerialized(self._serializer, event_tag, self._json_dict)


class JSONPreprocessObjectSerializerTest(JSONSerializerTestCase):
  """Tests for the JSON preprocessing object serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parsers = [
        u'esedb', u'chrome_preferences', u'winfirewall', u'android_app_usage',
        u'selinux', u'recycle_bin', u'pls_recall', u'filestat', u'sqlite',
        u'cups_ipp', u'winiis', u'lnk', u'rplog', u'symantec_scanlog',
        u'recycle_bin_info2', u'winevtx', u'plist', u'bsm_log', u'mac_keychain',
        u'pcap', u'mac_securityd', u'utmp', u'pe', u'asl_log', u'opera_global',
        u'custom_destinations', u'chrome_cache', u'popularity_contest',
        u'prefetch', u'winreg', u'msiecf', u'bencode', u'skydrive_log',
        u'openxml', u'xchatscrollback', u'utmpx', u'binary_cookies', u'syslog',
        u'hachoir', u'opera_typed_history', u'winevt', u'mac_appfirewall_log',
        u'winjob', u'olecf', u'xchatlog', u'macwifi', u'mactime', u'java_idx',
        u'firefox_cache', u'mcafee_protection', u'skydrive_log_error']

    self._stores = {
        u'Number': 1,
        u'Store 1': {
            u'count': 3,
            u'data_type': [u'fs:stat'],
            u'parsers': [u'filestat'],
            u'range': [1387891912000000, 1387891912000000],
            u'type_count': [[u'fs:stat', 3]],
            u'version': 1
        }
    }

    self._json_dict = {
        u'__type__': u'PreprocessObject',
        u'collection_information': {
            u'cmd_line': (
                u'/usr/bin/log2timeline.py pinfo_test.out '
                u'tsk_volume_system.raw'),
            u'configured_zone': {
                u'__type__': u'timezone',
                u'zone': u'UTC'
            },
            u'debug': False,
            u'file_processed': u'/tmp/tsk_volume_system.raw',
            u'image_offset': 180224,
            u'method': u'imaged processed',
            u'os_detected': u'N/A',
            u'output_file': u'pinfo_test.out',
            u'parser_selection': u'(no list set)',
            u'parsers': self._parsers,
            u'preferred_encoding': u'utf-8',
            u'preprocess': True,
            u'protobuf_size': 0,
            u'recursive': False,
            u'runtime': u'multi process mode',
            u'time_of_run': 1430290411000000,
            u'version': u'1.2.1_20150424',
            u'vss parsing': False,
            u'workers': 0
        },
        u'counter': {
            u'__type__': u'collections.Counter',
            u'filestat': 3,
            u'total': 3
        },
        u'guessed_os': u'None',
        u'plugin_counter': {
            u'__type__': u'collections.Counter',
        },
        u'store_range': {
            u'__type__': u'range',
            u'end': 1,
            u'start': 1
        },
        u'stores': self._stores,
        u'zone': {
            u'__type__': u'timezone',
            u'zone': u'UTC'
        }
    }

    self._counter = collections.Counter()
    self._counter[u'filestat'] = 3
    self._counter[u'total'] = 3

    self._plugin_counter = collections.Counter()

    self._serializer = json_serializer.JSONPreprocessObjectSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    pre_obj = self._TestReadSerialized(self._serializer, self._json_dict)
    counter = pre_obj.counter

    for key, value in iter(counter.items()):
      self.assertEquals(self._counter[key], value)

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""
    preprocess_object = event.PreprocessObject()
    preprocess_object.collection_information = {
        u'cmd_line': (
            u'/usr/bin/log2timeline.py pinfo_test.out tsk_volume_system.raw'),
        u'configured_zone': pytz.UTC,
        u'debug': False,
        u'file_processed': u'/tmp/tsk_volume_system.raw',
        u'image_offset': 180224,
        u'method': u'imaged processed',
        u'os_detected': u'N/A',
        u'output_file': u'pinfo_test.out',
        u'parser_selection': u'(no list set)',
        u'parsers': self._parsers,
        u'preferred_encoding': u'utf-8',
        u'preprocess': True,
        u'protobuf_size': 0,
        u'recursive': False,
        u'runtime': u'multi process mode',
        u'time_of_run': 1430290411000000,
        u'version': u'1.2.1_20150424',
        u'vss parsing': False,
        u'workers': 0
    }

    preprocess_object.counter = self._counter
    preprocess_object.guessed_os = u'None'
    preprocess_object.plugin_counter = self._plugin_counter
    preprocess_object.store_range = (1, 1)
    preprocess_object.stores = self._stores
    preprocess_object.zone = pytz.UTC

    self._TestWriteSerialized(
        self._serializer, preprocess_object, self._json_dict)


class JSONCollectionInformationSerializerTest(JSONSerializerTestCase):
  """Tests for the JSON preprocessing collection information object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._json_dict = {
        u'__COUNTERS__': {
            u'foobar': {
                u'stuff': 1245
            }
        },
        u'foo': u'bar',
        u'foo2': u'randombar'
    }

    self._collection_information_object = collection.CollectionInformation()
    self._collection_information_object.AddCounter(u'foobar')
    self._collection_information_object.IncrementCounter(
        u'foobar', u'stuff', value=1245)
    self._collection_information_object.SetValue(u'foo', u'bar')
    self._collection_information_object.SetValue(u'foo2', u'randombar')

    self._serializer = json_serializer.JSONCollectionInformationObjectSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    collection_object = self._TestReadSerialized(
        self._serializer, self._json_dict)

    for key, value in collection_object.GetValueDict().iteritems():
      self.assertEqual(
          value, self._collection_information_object.GetValue(key))

    for identifier, counter in collection_object.GetCounters():
      compare_counter = self._collection_information_object.GetCounter(
          identifier)

      for key, value in counter.iteritems():
        self.assertEqual(value, compare_counter[key])

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""
    self._TestWriteSerialized(
        self._serializer, self._collection_information_object, self._json_dict)


if __name__ == '__main__':
  unittest.main()
