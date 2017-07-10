#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the serializer object implementation using JSON."""

import collections
import json
import time
import unittest
import uuid

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import fake_path_spec
from dfvfs.path import factory as path_spec_factory

import plaso
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.serializer import json_serializer

from tests import test_lib as shared_test_lib


class JSONSerializerTestCase(shared_test_lib.BaseTestCase):
  """Tests for a JSON serializer object."""

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

    expected_analysis_report = reports.AnalysisReport(
        plugin_name=u'chrome_extension_test', text=expected_report_text)
    expected_analysis_report.report_dict = expected_report_dict
    expected_analysis_report.time_compiled = 1431978243000000

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
        u'plugin_name': u'chrome_extension_test',
        u'report_dict': expected_report_dict,
        u'text': expected_report_text,
        u'time_compiled': 1431978243000000}

    analysis_report_dict = analysis_report.CopyToDict()
    self.assertEqual(
        sorted(analysis_report_dict.items()),
        sorted(expected_analysis_report_dict.items()))

  # TODO: add ExtractionError tests.

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

  def testReadAndWriteSerializedEventSource(self):
    """Test ReadSerialized and WriteSerialized of EventSource."""
    test_path_spec = fake_path_spec.FakePathSpec(location=u'/opt/plaso.txt')

    expected_event_source = event_sources.EventSource(path_spec=test_path_spec)

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_event_source))

    self.assertIsNotNone(json_string)

    event_source = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(event_source)
    self.assertIsInstance(event_source, event_sources.EventSource)

    expected_event_source_dict = {
        u'path_spec': test_path_spec.comparable,
    }

    event_source_dict = event_source.CopyToDict()
    path_spec = event_source_dict.get(u'path_spec', None)
    if path_spec:
      event_source_dict[u'path_spec'] = path_spec.comparable

    self.assertEqual(
        sorted(event_source_dict.items()),
        sorted(expected_event_source_dict.items()))

  def testReadAndWriteSerializedEventTag(self):
    """Test ReadSerialized and WriteSerialized of EventTag."""
    expected_event_tag = events.EventTag(comment=u'My first comment.')
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
    }

    event_tag_dict = event_tag.CopyToDict()
    self.assertEqual(
        sorted(event_tag_dict.items()),
        sorted(expected_event_tag_dict.items()))

  def testReadAndWriteSerializedSession(self):
    """Test ReadSerialized and WriteSerialized of Session."""
    parsers_counter = collections.Counter()
    parsers_counter[u'filestat'] = 3
    parsers_counter[u'total'] = 3

    expected_session = sessions.Session()
    expected_session.product_name = u'plaso'
    expected_session.product_version = plaso.__version__
    expected_session.parsers_counter = parsers_counter

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_session))

    self.assertIsNotNone(json_string)

    session = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(session)
    self.assertIsInstance(session, sessions.Session)

    expected_session_dict = {
        u'aborted': False,
        u'analysis_reports_counter': session.analysis_reports_counter,
        u'debug_mode': False,
        u'event_labels_counter': session.event_labels_counter,
        u'identifier': session.identifier,
        u'parsers_counter': parsers_counter,
        u'preferred_encoding': u'utf-8',
        u'preferred_time_zone': u'UTC',
        u'product_name': u'plaso',
        u'product_version': plaso.__version__,
        u'start_time': session.start_time
    }

    session_dict = session.CopyToDict()
    self.assertEqual(
        sorted(session_dict.items()), sorted(expected_session_dict.items()))

  def testReadAndWriteSerializedSessionCompletion(self):
    """Test ReadSerialized and WriteSerialized of SessionCompletion."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())

    parsers_counter = collections.Counter()
    parsers_counter[u'filestat'] = 3
    parsers_counter[u'total'] = 3

    expected_session_completion = sessions.SessionCompletion(
        identifier=session_identifier)
    expected_session_completion.timestamp = timestamp
    expected_session_completion.parsers_counter = parsers_counter

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_session_completion))

    self.assertIsNotNone(json_string)

    session_completion = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(session_completion)
    self.assertIsInstance(session_completion, sessions.SessionCompletion)

    expected_session_completion_dict = {
        u'aborted': False,
        u'identifier': session_identifier,
        u'parsers_counter': parsers_counter,
        u'timestamp': timestamp
    }

    session_completion_dict = session_completion.CopyToDict()
    self.assertEqual(
        sorted(session_completion_dict.items()),
        sorted(expected_session_completion_dict.items()))

  def testReadAndWriteSerializedSessionStart(self):
    """Test ReadSerialized and WriteSerialized of SessionStart."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())

    expected_session_start = sessions.SessionStart(
        identifier=session_identifier)
    expected_session_start.timestamp = timestamp
    expected_session_start.product_name = u'plaso'
    expected_session_start.product_version = plaso.__version__

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_session_start))

    self.assertIsNotNone(json_string)

    session_start = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(session_start)
    self.assertIsInstance(session_start, sessions.SessionStart)

    expected_session_start_dict = {
        u'debug_mode': False,
        u'identifier': session_identifier,
        u'product_name': u'plaso',
        u'product_version': plaso.__version__,
        u'timestamp': timestamp
    }

    session_start_dict = session_start.CopyToDict()
    self.assertEqual(
        sorted(session_start_dict.items()),
        sorted(expected_session_start_dict.items()))

  def testReadAndWriteSerializedTask(self):
    """Test ReadSerialized and WriteSerialized of Task."""
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())

    expected_task = tasks.Task(session_identifier=session_identifier)

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_task))

    self.assertIsNotNone(json_string)

    task = json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
        json_string)

    self.assertIsNotNone(task)
    self.assertIsInstance(task, tasks.Task)

    expected_task_dict = {
        u'aborted': False,
        u'identifier': task.identifier,
        u'retried': False,
        u'session_identifier': session_identifier,
        u'start_time': task.start_time
    }

    task_dict = task.CopyToDict()
    self.assertEqual(
        sorted(task_dict.items()), sorted(expected_task_dict.items()))

  def testReadAndWriteSerializedTaskCompletion(self):
    """Test ReadSerialized and WriteSerialized of TaskCompletion."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    task_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())

    expected_task_completion = tasks.TaskCompletion(
        identifier=task_identifier, session_identifier=session_identifier)
    expected_task_completion.timestamp = timestamp

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_task_completion))

    self.assertIsNotNone(json_string)

    task_completion = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(task_completion)
    self.assertIsInstance(task_completion, tasks.TaskCompletion)

    expected_task_completion_dict = {
        u'aborted': False,
        u'identifier': task_identifier,
        u'session_identifier': session_identifier,
        u'timestamp': timestamp
    }

    task_completion_dict = task_completion.CopyToDict()
    self.assertEqual(
        sorted(task_completion_dict.items()),
        sorted(expected_task_completion_dict.items()))

  def testReadAndWriteSerializedTaskStart(self):
    """Test ReadSerialized and WriteSerialized of TaskStart."""
    timestamp = int(time.time() * 1000000)
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    task_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())

    expected_task_start = tasks.TaskStart(
        identifier=task_identifier, session_identifier=session_identifier)
    expected_task_start.timestamp = timestamp

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_task_start))

    self.assertIsNotNone(json_string)

    task_start = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(task_start)
    self.assertIsInstance(task_start, tasks.TaskStart)

    expected_task_start_dict = {
        u'identifier': task_identifier,
        u'session_identifier': session_identifier,
        u'timestamp': timestamp
    }

    task_start_dict = task_start.CopyToDict()
    self.assertEqual(
        sorted(task_start_dict.items()),
        sorted(expected_task_start_dict.items()))



if __name__ == '__main__':
  unittest.main()
