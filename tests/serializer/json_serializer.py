#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the serializer object implementation using JSON."""

from __future__ import unicode_literals

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
      serializer_object (JSONSerializer): the JSON serializer object.
      json_dict (dict[str, object]): one or more JSON serialized values

    Returns:
      object: unserialized object.
    """
    # We use json.dumps to make sure the dict does not serialize into
    # an invalid JSON string such as one that contains Python string prefixes
    # like b'' or u''.
    json_string = json.dumps(json_dict)
    unserialized_object = serializer_object.ReadSerialized(json_string)

    self.assertIsNotNone(unserialized_object)
    return unserialized_object

  def _TestWriteSerialized(
      self, serializer_object, unserialized_object, expected_json_dict):
    """Tests the WriteSerialized function.

    Args:
      serializer_object (JSONSerializer): the JSON serializer object.
      unserialized_object (object): the unserialized object.
      expected_json_dict (dict[str, object]): one or more expected JSON
          serialized values.

    Returns:
      str: serialized JSON string.
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
        'dude': [
            ['Google Keep - notes and lists',
             'hmjkmjkepdijhoojdojkdfohbdgmmhki']
        ],
        'frank': [
            ['YouTube', 'blpcfgokakmgnkcojhhkbfbldkacnbeo'],
            ['Google Play Music', 'icppfcnhkcmnfdhfhphakoifcfokfdhg']
        ]
    }
    expected_report_text = (
        ' == USER: dude ==\n'
        '  Google Keep - notes and lists [hmjkmjkepdijhoojdojkdfohbdgmmhki]\n'
        '\n'
        ' == USER: frank ==\n'
        '  Google Play Music [icppfcnhkcmnfdhfhphakoifcfokfdhg]\n'
        '  YouTube [blpcfgokakmgnkcojhhkbfbldkacnbeo]\n'
        '\n')

    expected_analysis_report = reports.AnalysisReport(
        plugin_name='chrome_extension_test', text=expected_report_text)
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
        'plugin_name': 'chrome_extension_test',
        'report_dict': expected_report_dict,
        'text': expected_report_text,
        'time_compiled': 1431978243000000}

    analysis_report_dict = analysis_report.CopyToDict()
    self.assertEqual(
        sorted(analysis_report_dict.items()),
        sorted(expected_analysis_report_dict.items()))

  # TODO: add ExtractionWarning tests.

  def testReadAndWriteSerializedEventObject(self):
    """Test ReadSerialized and WriteSerialized of EventObject."""
    test_file = self._GetTestFilePath(['ímynd.dd'])

    volume_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=volume_path_spec)

    expected_event = events.EventObject()
    expected_event.data_type = 'test:event2'
    expected_event.pathspec = path_spec
    expected_event.timestamp = 1234124
    expected_event.timestamp_desc = 'Written'

    expected_event.binary_string = b'\xc0\x90\x90binary'
    expected_event.empty_string = ''
    expected_event.zero_integer = 0
    expected_event.integer = 34
    expected_event.float = -122.082203542683
    expected_event.string = 'Normal string'
    expected_event.unicode_string = 'And I am a unicorn.'
    expected_event.my_list = ['asf', 4234, 2, 54, 'asf']
    expected_event.my_dict = {
        'a': 'not b', 'c': 34, 'list': ['sf', 234], 'an': [234, 32]}
    expected_event.a_tuple = (
        'some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35)
    expected_event.null_value = None

    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            expected_event))

    self.assertIsNotNone(json_string)

    event = (
        json_serializer.JSONAttributeContainerSerializer.ReadSerialized(
            json_string))

    self.assertIsNotNone(event)
    self.assertIsInstance(event, events.EventObject)

    expected_event_dict = {
        'a_tuple': (
            'some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35),
        'binary_string': b'\xc0\x90\x90binary',
        'data_type': 'test:event2',
        'empty_string': '',
        'integer': 34,
        'float': -122.082203542683,
        'my_dict': {
            'a': 'not b',
            'an': [234, 32],
            'c': 34,
            'list': ['sf', 234]
        },
        'my_list': ['asf', 4234, 2, 54, 'asf'],
        'pathspec': path_spec.comparable,
        'string': 'Normal string',
        'timestamp_desc': 'Written',
        'timestamp': 1234124,
        'unicode_string': 'And I am a unicorn.',
        'zero_integer': 0
    }

    event_dict = event.CopyToDict()
    path_spec = event_dict.get('pathspec', None)
    if path_spec:
      event_dict['pathspec'] = path_spec.comparable

    self.assertEqual(
        sorted(event_dict.items()),
        sorted(expected_event_dict.items()))

  def testReadAndWriteSerializedEventSource(self):
    """Test ReadSerialized and WriteSerialized of EventSource."""
    test_path_spec = fake_path_spec.FakePathSpec(location='/opt/plaso.txt')

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
        'path_spec': test_path_spec.comparable,
    }

    event_source_dict = event_source.CopyToDict()
    path_spec = event_source_dict.get('path_spec', None)
    if path_spec:
      event_source_dict['path_spec'] = path_spec.comparable

    self.assertEqual(
        sorted(event_source_dict.items()),
        sorted(expected_event_source_dict.items()))

  def testReadAndWriteSerializedEventTag(self):
    """Test ReadSerialized and WriteSerialized of EventTag."""
    expected_event_tag = events.EventTag(comment='My first comment.')
    expected_event_tag.AddLabels(['Malware', 'Common'])

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
        'comment': 'My first comment.',
        'labels': ['Malware', 'Common'],
    }

    event_tag_dict = event_tag.CopyToDict()
    self.assertEqual(
        sorted(event_tag_dict.items()),
        sorted(expected_event_tag_dict.items()))

  def testReadAndWriteSerializedSession(self):
    """Test ReadSerialized and WriteSerialized of Session."""
    parsers_counter = collections.Counter()
    parsers_counter['filestat'] = 3
    parsers_counter['total'] = 3

    expected_session = sessions.Session()
    expected_session.product_name = 'plaso'
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
        'aborted': False,
        'analysis_reports_counter': session.analysis_reports_counter,
        'debug_mode': False,
        'event_labels_counter': session.event_labels_counter,
        'identifier': session.identifier,
        'parsers_counter': parsers_counter,
        'preferred_encoding': 'utf-8',
        'preferred_time_zone': 'UTC',
        'product_name': 'plaso',
        'product_version': plaso.__version__,
        'start_time': session.start_time
    }

    session_dict = session.CopyToDict()
    self.assertEqual(
        sorted(session_dict.items()), sorted(expected_session_dict.items()))

  def testReadAndWriteSerializedSessionCompletion(self):
    """Test ReadSerialized and WriteSerialized of SessionCompletion."""
    timestamp = int(time.time() * 1000000)
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)

    parsers_counter = collections.Counter()
    parsers_counter['filestat'] = 3
    parsers_counter['total'] = 3

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
        'aborted': False,
        'identifier': session_identifier,
        'parsers_counter': parsers_counter,
        'timestamp': timestamp
    }

    session_completion_dict = session_completion.CopyToDict()
    self.assertEqual(
        sorted(session_completion_dict.items()),
        sorted(expected_session_completion_dict.items()))

  def testReadAndWriteSerializedSessionStart(self):
    """Test ReadSerialized and WriteSerialized of SessionStart."""
    timestamp = int(time.time() * 1000000)
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)

    expected_session_start = sessions.SessionStart(
        identifier=session_identifier)
    expected_session_start.timestamp = timestamp
    expected_session_start.product_name = 'plaso'
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
        'debug_mode': False,
        'identifier': session_identifier,
        'product_name': 'plaso',
        'product_version': plaso.__version__,
        'timestamp': timestamp
    }

    session_start_dict = session_start.CopyToDict()
    self.assertEqual(
        sorted(session_start_dict.items()),
        sorted(expected_session_start_dict.items()))

  def testReadAndWriteSerializedTask(self):
    """Test ReadSerialized and WriteSerialized of Task."""
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)

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
        'aborted': False,
        'has_retry': False,
        'identifier': task.identifier,
        'session_identifier': session_identifier,
        'start_time': task.start_time
    }

    task_dict = task.CopyToDict()
    self.assertEqual(
        sorted(task_dict.items()), sorted(expected_task_dict.items()))

  def testReadAndWriteSerializedTaskCompletion(self):
    """Test ReadSerialized and WriteSerialized of TaskCompletion."""
    timestamp = int(time.time() * 1000000)
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task_identifier = '{0:s}'.format(uuid.uuid4().hex)

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
        'aborted': False,
        'identifier': task_identifier,
        'session_identifier': session_identifier,
        'timestamp': timestamp
    }

    task_completion_dict = task_completion.CopyToDict()
    self.assertEqual(
        sorted(task_completion_dict.items()),
        sorted(expected_task_completion_dict.items()))

  def testReadAndWriteSerializedTaskStart(self):
    """Test ReadSerialized and WriteSerialized of TaskStart."""
    timestamp = int(time.time() * 1000000)
    session_identifier = '{0:s}'.format(uuid.uuid4().hex)
    task_identifier = '{0:s}'.format(uuid.uuid4().hex)

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
        'identifier': task_identifier,
        'session_identifier': session_identifier,
        'timestamp': timestamp
    }

    task_start_dict = task_start.CopyToDict()
    self.assertEqual(
        sorted(task_start_dict.items()),
        sorted(expected_task_start_dict.items()))



if __name__ == '__main__':
  unittest.main()
