#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the serializer object implementation using protobuf."""

import collections
import unittest

from plaso.lib import event
from plaso.proto import plaso_storage_pb2
from plaso.serializer import protobuf_serializer
from plaso.storage import collection

import pytz


class ProtobufSerializerTestCase(unittest.TestCase):
  """Tests for a protobuf serializer object."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _DebugWriteSerialized(
      self, serializer, unserialized_object, expected_proto_object):
    """Debug the write serialized functionality.

    Args:
      serializer_object: the protobuf serializer object.
      unserialized_object: the unserialized object.
      expected_proto_object: the expected protobuf object.
    """
    proto_object = serializer.WriteSerializedObject(unserialized_object)

    # We turn the proto objects into string for a better diff.
    expected_proto_object_string = u'{0!s}'.format(expected_proto_object)
    proto_object_string = u'{0!s}'.format(proto_object)
    self.assertEqual(proto_object_string, expected_proto_object_string)

  def _TestWriteSerialized(
      self, serializer, unserialized_object, expected_proto_string):
    """Tests the write serialized functionality.

    Args:
      serializer_object: the protobuf serializer object.
      unserialized_object: the unserialized object.
      expected_proto_string: the expected protobuf string.
    """
    proto_string = serializer.WriteSerialized(unserialized_object)
    self.assertEqual(proto_string, expected_proto_string)


class ProtobufAnalysisReportSerializerTest(ProtobufSerializerTestCase):
  """Tests for the protobuf analysis report serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
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

    attribute_serializer = protobuf_serializer.ProtobufEventAttributeSerializer

    proto = plaso_storage_pb2.AnalysisReport()

    dict_proto = plaso_storage_pb2.Dict()
    for key, value in iter(self._report_dict.items()):
      sub_proto = dict_proto.attributes.add()
      attribute_serializer.WriteSerializedObject(sub_proto, key, value)
    proto.report_dict.MergeFrom(dict_proto)

    # TODO: add report_array, _anomalies and _tags tests.

    proto.plugin_name = u'chrome_extension_test'
    proto.text = self._report_text
    proto.time_compiled = 1431978243000000

    self._proto_string = proto.SerializeToString()
    self._serializer = protobuf_serializer.ProtobufAnalysisReportSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    analysis_report = self._serializer.ReadSerialized(self._proto_string)

    self.assertEqual(analysis_report.plugin_name, u'chrome_extension_test')
    self.assertEqual(analysis_report.report_dict, self._report_dict)
    self.assertEqual(analysis_report.text, self._report_text)
    self.assertEqual(analysis_report.time_compiled, 1431978243000000)

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""
    analysis_report = event.AnalysisReport(u'chrome_extension_test')

    analysis_report.report_dict = self._report_dict
    analysis_report.text = self._report_text
    analysis_report.time_compiled = 1431978243000000
    self._TestWriteSerialized(
        self._serializer, analysis_report, self._proto_string)


class ProtobufEventObjectSerializerTest(ProtobufSerializerTestCase):
  """Tests for the protobuf event object serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    proto = plaso_storage_pb2.EventObject()

    proto.data_type = u'test:event2'
    proto.timestamp = 1234124
    proto.timestamp_desc = u'Written'

    attribute_serializer = protobuf_serializer.ProtobufEventAttributeSerializer

    proto_attribute = proto.attributes.add()
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'zero_integer', 0)

    proto_attribute = proto.attributes.add()
    dict_object = {
        u'a': u'not b', u'c': 34, u'list': [u'sf', 234], u'an': [234, 32]}
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'my_dict', dict_object)

    proto_attribute = proto.attributes.add()
    tuple_object = (
        u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35)
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'a_tuple', tuple_object)

    proto_attribute = proto.attributes.add()
    list_object = [u'asf', 4234, 2, 54, u'asf']
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'my_list', list_object)

    proto_attribute = proto.attributes.add()
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'unicode_string', u'And I\'m a unicorn.')

    proto_attribute = proto.attributes.add()
    attribute_serializer.WriteSerializedObject(proto_attribute, u'integer', 34)

    proto_attribute = proto.attributes.add()
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'string', u'Normal string')

    proto.uuid = u'5a78777006de4ddb8d7bbe12ab92ccf8'

    self._proto_string = proto.SerializeToString()
    self._serializer = protobuf_serializer.ProtobufEventObjectSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    event_object = self._serializer.ReadSerialized(self._proto_string)

    # An integer value containing 0 should get stored.
    self.assertTrue(hasattr(event_object, u'zero_integer'))

    attribute_value = getattr(event_object, u'integer', 0)
    self.assertEqual(attribute_value, 34)

    attribute_value = getattr(event_object, u'my_list', [])
    self.assertEqual(len(attribute_value), 5)

    attribute_value = getattr(event_object, u'string', u'')
    self.assertEqual(attribute_value, u'Normal string')

    attribute_value = getattr(event_object, u'unicode_string', u'')
    self.assertEqual(attribute_value, u'And I\'m a unicorn.')

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

    event_object.empty_string = u''
    event_object.zero_integer = 0
    event_object.integer = 34
    event_object.string = u'Normal string'
    event_object.unicode_string = u'And I\'m a unicorn.'
    event_object.my_list = [u'asf', 4234, 2, 54, u'asf']
    event_object.my_dict = {
        u'a': u'not b', u'c': 34, u'list': [u'sf', 234], u'an': [234, 32]}
    event_object.a_tuple = (
        u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35)
    event_object.null_value = None

    proto_string = self._serializer.WriteSerialized(event_object)
    self.assertEqual(proto_string, self._proto_string)

    event_object = self._serializer.ReadSerialized(proto_string)

    # An empty string should not get stored.
    self.assertFalse(hasattr(event_object, u'empty_string'))

    # A None (or Null) value should not get stored.
    self.assertFalse(hasattr(event_object, u'null_value'))


class ProtobufEventTagSerializerTest(ProtobufSerializerTestCase):
  """Tests for the protobuf event tag serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    proto = plaso_storage_pb2.EventTagging()
    proto.store_number = 234
    proto.store_index = 18
    proto.comment = u'My first comment.'
    proto.color = u'Red'
    proto_tag = proto.tags.add()
    proto_tag.value = u'Malware'
    proto_tag = proto.tags.add()
    proto_tag.value = u'Common'

    self._proto_string = proto.SerializeToString()
    self._serializer = protobuf_serializer.ProtobufEventTagSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    event_tag = self._serializer.ReadSerialized(self._proto_string)

    self.assertEqual(event_tag.color, u'Red')
    self.assertEqual(event_tag.comment, u'My first comment.')
    self.assertEqual(event_tag.store_index, 18)
    self.assertEqual(len(event_tag.tags), 2)
    self.assertEqual(event_tag.tags, [u'Malware', u'Common'])

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""
    event_tag = event.EventTag()

    event_tag.store_number = 234
    event_tag.store_index = 18
    event_tag.comment = u'My first comment.'
    event_tag.color = u'Red'
    event_tag.tags = [u'Malware', u'Common']

    self._TestWriteSerialized(self._serializer, event_tag, self._proto_string)


class ProtobufPreprocessObjectSerializerTest(ProtobufSerializerTestCase):
  """Tests for the protobuf preprocess object serializer object."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    parsers = [
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

    self._collection_information = {
        u'cmd_line': (
            u'/usr/bin/log2timeline.py pinfo_test.out tsk_volume_system.raw'),
        u'configured_zone': u'UTC',
        u'debug': False,
        u'file_processed': u'/tmp/tsk_volume_system.raw',
        u'image_offset': 180224,
        u'method': u'imaged processed',
        u'os_detected': u'N/A',
        u'output_file': u'pinfo_test.out',
        u'parser_selection': u'(no list set)',
        u'parsers': parsers,
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

    self._counter = collections.Counter()
    self._counter[u'filestat'] = 3
    self._counter[u'total'] = 3

    self._plugin_counter = collections.Counter()

    attribute_serializer = protobuf_serializer.ProtobufEventAttributeSerializer

    # Warning the order in which the attributes are added to the protobuf
    # matters for the test.
    proto = plaso_storage_pb2.PreProcess()

    attribute_serializer.WriteSerializedDictObject(
        proto, u'collection_information', self._collection_information)

    attribute_serializer.WriteSerializedDictObject(
        proto, u'counter', self._counter)

    proto_attribute = proto.attributes.add()
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'guessed_os', u'None')

    attribute_serializer.WriteSerializedDictObject(
        proto, u'plugin_counter', self._plugin_counter)

    # Add the store_range attribute.
    range_proto = plaso_storage_pb2.Array()
    range_start = range_proto.values.add()
    range_start.integer = 1
    range_end = range_proto.values.add()
    range_end.integer = 1
    proto.store_range.MergeFrom(range_proto)

    proto_attribute = proto.attributes.add()
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'zone', u'{0!s}'.format(pytz.UTC))

    proto_attribute = proto.attributes.add()
    attribute_serializer.WriteSerializedObject(
        proto_attribute, u'stores', self._stores)

    self._proto_object = proto
    self._proto_string = proto.SerializeToString()

    self._serializer = protobuf_serializer.ProtobufPreprocessObjectSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    preprocess_object = self._serializer.ReadSerialized(self._proto_string)

    self.assertEqual(
        preprocess_object.collection_information, self._collection_information)
    self.assertEqual(preprocess_object.counter, self._counter)
    self.assertEqual(preprocess_object.guessed_os, u'None')
    self.assertEqual(preprocess_object.plugin_counter, self._plugin_counter)
    self.assertEqual(preprocess_object.store_range, (1, 1))
    self.assertEqual(preprocess_object.stores, self._stores)
    self.assertEqual(preprocess_object.zone, pytz.UTC)

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""
    preprocess_object = event.PreprocessObject()
    preprocess_object.collection_information = self._collection_information
    preprocess_object.counter = self._counter
    preprocess_object.guessed_os = u'None'
    preprocess_object.plugin_counter = self._plugin_counter
    preprocess_object.store_range = (1, 1)
    preprocess_object.stores = self._stores
    preprocess_object.zone = pytz.UTC

    self._TestWriteSerialized(
        self._serializer, preprocess_object, self._proto_string)


class ProtobufCollectionInformationObjectSerializerTest(
    ProtobufSerializerTestCase):
  """Tests for the collection information object protobuf serializer."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._collection_object = collection.CollectionInformation()
    self._collection_object.AddCounter(u'foobar')
    self._collection_object.IncrementCounter(
        u'foobar', u'random', value=532)
    self._collection_object.IncrementCounter(
        u'foobar', u'hat', value=12)
    self._collection_object.SetValue(u'foo', u'bar')
    self._collection_object.SetValue(u'bar', u'vitleysa')

    self._proto_string = (
        b'\n\n\n\x03foo\x12\x03bar\n\x0f\n\x03bar\x12\x08vitleysa\n2\n\x0c'
        b'__COUNTERS__*"\n \n\x06foobar*\x16\n\x0b\n\x06random'
        b'\x18\x94\x04\n\x07\n\x03hat\x18\x0c')

    # Rename the protobuf serializer import in order to fit in a single line.
    module = protobuf_serializer
    self._serializer = module.ProtobufCollectionInformationObjectSerializer

  def testReadSerialized(self):
    """Tests the ReadSerialized function."""
    collection_object = self._serializer.ReadSerialized(self._proto_string)

    for identifier, counter in collection_object.GetCounters():
      compare_counter = self._collection_object.GetCounter(identifier)
      for key, value in counter.iteritems():
        self.assertEqual(value, compare_counter[key])

    for identifier, value in collection_object.GetValueDict().iteritems():
      self.assertEqual(value, self._collection_object.GetValue(identifier))

  def testWriteSerialized(self):
    """Tests the WriteSerialized function."""
    self._TestWriteSerialized(
        self._serializer, self._collection_object, self._proto_string)

    proto = self._serializer.WriteSerializedObject(self._collection_object)
    attribute_serializer = protobuf_serializer.ProtobufEventAttributeSerializer
    for attribute in proto.attributes:
      if attribute.key == self._collection_object.RESERVED_COUNTER_KEYWORD:
        _, value = attribute_serializer.ReadSerializedObject(attribute)
        for identifier, value_dict in value.iteritems():
          self.assertEqual(set(value_dict.items()), set(
              self._collection_object.GetCounter(identifier).items()))

      else:
        _, value = attribute_serializer.ReadSerializedObject(attribute)
        self.assertEqual(value, self._collection_object.GetValue(
            attribute.key))


if __name__ == '__main__':
  unittest.main()
