#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the serializer object implementation using JSON."""

import collections
import json
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.containers import reports
from plaso.lib import event
from plaso.serializer import json_serializer
from plaso.storage import collection

import pytz  # pylint: disable=wrong-import-order


class JSONSerializerTestCase(unittest.TestCase):
  """Tests for a JSON serializer object."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

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

    self.assertEqual(
        sorted(json_dict.items()), sorted(expected_json_dict.items()))

    return json_string


class JSONAttributeContainerSerializerTest(JSONSerializerTestCase):
  """Tests for the JSON attribute container serializer object."""

  def testReadAndWriteSerializedAnalysisReport(self):
    """Test ReadSerialized and WriteSerialized of AnalysisReport."""
    expected_comment = u'This is a test event tag.'
    expected_uuid = u'403818f93dce467bac497ef0f263fde8'
    expected_labels = [u'Test', u'AnotherTest']
    expected_report_dict = {
        u'dude': [
            [u'Google Keep - notes and lists',
             u'hmjkmjkepdijhoojdojkdfohbdgmmhki']
        ],
        u'frank': [
            [u'YouTube', u'blpcfgokakmgnkcojhhkbfbldkacnbeo'],
            [u'Google Play Music', u'icppfcnhkcmnfdhfhphakoifcfokfdhg']
        ]
    }
    expected_report_text = (
        u' == USER: dude ==\n'
        u'  Google Keep - notes and lists [hmjkmjkepdijhoojdojkdfohbdgmmhki]\n'
        u'\n'
        u' == USER: frank ==\n'
        u'  Google Play Music [icppfcnhkcmnfdhfhphakoifcfokfdhg]\n'
        u'  YouTube [blpcfgokakmgnkcojhhkbfbldkacnbeo]\n'
        u'\n')

    expected_event_tag = events.EventTag(
        comment=expected_comment, event_uuid=expected_uuid)
    expected_event_tag.AddLabels(expected_labels)

    self.assertTrue(expected_event_tag.IsValidForSerialization())

    expected_analysis_report = reports.AnalysisReport(
        plugin_name=u'chrome_extension_test', text=expected_report_text)
    expected_analysis_report.report_dict = expected_report_dict
    expected_analysis_report.time_compiled = 1431978243000000
    expected_analysis_report.SetTags([expected_event_tag])

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_analysis_report))

    self.assertIsNotNone(json_string)

    analysis_report = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(analysis_report)
    self.assertIsInstance(analysis_report, reports.AnalysisReport)

    # TODO: preserve the tuples in the report dict.
    # TODO: add report_array tests.

    expected_analysis_report_dict = {
        u'_event_tags': [{
            u'comment': expected_comment,
            u'event_uuid': expected_uuid,
            u'labels': expected_labels,
        }],
        u'plugin_name': u'chrome_extension_test',
        u'report_dict': expected_report_dict,
        u'text': expected_report_text,
        u'time_compiled': 1431978243000000}

    analysis_report_dict = analysis_report.CopyToDict()
    self.assertEqual(
        sorted(analysis_report_dict.items()),
        sorted(expected_analysis_report_dict.items()))

  def testReadAndWriteSerializedEventObject(self):
    """Test ReadSerialized and WriteSerialized of EventObject."""
    test_file = self._GetTestFilePath([u'ímynd.dd'])

    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    expected_event_object = events.EventObject()

    expected_event_object.data_type = u'test:event2'
    expected_event_object.pathspec = path_spec
    expected_event_object.timestamp = 1234124
    expected_event_object.timestamp_desc = u'Written'
    # Prevent the event object for generating its own UUID.
    expected_event_object.uuid = u'5a78777006de4ddb8d7bbe12ab92ccf8'

    expected_event_object.binary_string = b'\xc0\x90\x90binary'
    expected_event_object.empty_string = u''
    expected_event_object.zero_integer = 0
    expected_event_object.integer = 34
    expected_event_object.string = u'Normal string'
    expected_event_object.unicode_string = u'And I am a unicorn.'
    expected_event_object.my_list = [u'asf', 4234, 2, 54, u'asf']
    expected_event_object.my_dict = {
        u'a': u'not b', u'c': 34, u'list': [u'sf', 234], u'an': [234, 32]}
    expected_event_object.a_tuple = (
        u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35)
    expected_event_object.null_value = None

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_event_object))

    self.assertIsNotNone(json_string)

    event_object = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(event_object)
    self.assertIsInstance(event_object, events.EventObject)

    expected_event_object_dict = {
        u'a_tuple': (
            u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35),
        u'binary_string': b'\xc0\x90\x90binary',
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
        u'pathspec': path_spec.comparable,
        u'string': u'Normal string',
        u'timestamp_desc': u'Written',
        u'timestamp': 1234124,
        u'uuid': u'5a78777006de4ddb8d7bbe12ab92ccf8',
        u'unicode_string': u'And I am a unicorn.',
        u'zero_integer': 0
    }

    event_object_dict = event_object.CopyToDict()
    path_spec = event_object_dict.get(u'pathspec', None)
    if path_spec:
      event_object_dict[u'pathspec'] = path_spec.comparable

    self.assertEqual(
        sorted(event_object_dict.items()),
        sorted(expected_event_object_dict.items()))

  def testReadAndWriteSerializedEventTag(self):
    """Test ReadSerialized and WriteSerialized of EventTag."""
    expected_event_tag = events.EventTag(comment=u'My first comment.')
    expected_event_tag.store_number = 234
    expected_event_tag.store_index = 18
    expected_event_tag.AddLabels([u'Malware', u'Common'])

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_event_tag))

    self.assertIsNotNone(json_string)

    event_tag = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(event_tag)
    self.assertIsInstance(event_tag, events.EventTag)

    expected_event_tag_dict = {
        u'comment': u'My first comment.',
        u'labels': [u'Malware', u'Common'],
        u'store_index': 18,
        u'store_number': 234,
    }

    event_tag_dict = event_tag.CopyToDict()
    self.assertEqual(
        sorted(event_tag_dict.items()),
        sorted(expected_event_tag_dict.items()))


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

    self._json_dict = {
        u'__type__': u'PreprocessObject',
        u'collection_information': {
            u'cmd_line': (
                u'/usr/bin/log2timeline.py pinfo_test.json.plaso '
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
            u'output_file': u'pinfo_test.json.plaso',
            u'parser_selection': u'(no list set)',
            u'parsers': self._parsers,
            u'preferred_encoding': u'utf-8',
            u'preprocess': True,
            u'recursive': False,
            u'runtime': u'multi process mode',
            u'serialized_buffer_size': 0,
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
            u'/usr/bin/log2timeline.py pinfo_test.json.plaso '
            u'tsk_volume_system.raw'),
        u'configured_zone': pytz.UTC,
        u'debug': False,
        u'file_processed': u'/tmp/tsk_volume_system.raw',
        u'image_offset': 180224,
        u'method': u'imaged processed',
        u'os_detected': u'N/A',
        u'output_file': u'pinfo_test.json.plaso',
        u'parser_selection': u'(no list set)',
        u'parsers': self._parsers,
        u'preferred_encoding': u'utf-8',
        u'preprocess': True,
        u'recursive': False,
        u'runtime': u'multi process mode',
        u'serialized_buffer_size': 0,
        u'time_of_run': 1430290411000000,
        u'version': u'1.2.1_20150424',
        u'vss parsing': False,
        u'workers': 0
    }

    preprocess_object.counter = self._counter
    preprocess_object.guessed_os = u'None'
    preprocess_object.plugin_counter = self._plugin_counter
    preprocess_object.store_range = (1, 1)
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
