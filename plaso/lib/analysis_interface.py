#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains basic interface for analysis plugins."""
import abc
import construct
import logging
import time

from plaso.lib import event
from plaso.lib import putils
from plaso.lib import registry
from plaso.proto import plaso_storage_pb2

# Constants representing the type of mesages the report deals with.
MESSAGE_REPORT = 1
MESSAGE_TAG = 2
MESSAGE_ANOMALY = 3

MESSAGE_STRUCT = construct.ULInt8('type')


class AnalysisPlugin(object):
  """Analysis plugin gets a copy of each read event for analysis."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # The URLS should contain a list of URL's with additional information about
  # this analysis plugin.
  URLS = []

  # The name of the plugin. This is the name that is matced against when
  # loading plugins, so it is important that this name is short, concise and
  # explains the nature of the plugin easily. It also needs to be unique.
  NAME = 'Plugin'

  # A flag indicating whether or not this plugin should be run during extraction
  # phase or reserved entirely for post processing stage.
  # Typically this would mean that the plugin is perhaps too computationally
  # heavy to be run during event extraction and should rather be run during
  # post-processing.
  # Since most plugins should perhaps rather be run during post-processing
  # this is set to False by default and needs to be overwritten if the plugin
  # should be able to run during the extraction phase.
  ENABLE_IN_EXTRACTION = False

  # All the possible report types.
  TYPE_ANOMALY = 1    # Plugin that is inspecting events for anomalies.
  TYPE_STATISTICS = 2   # Statistical calculations.
  TYPE_ANNOTATION = 3    # Inspecting events with the primary purpose of
                         # annotating or tagging them.
  TYPE_REPORT = 4    # Inspecting events to provide a summary information.

  # Optional arguments to be added to the argument parser.
  # An example would be:
  #   ARGUMENTS = [('--myparameter', {
  #       'action': 'store',
  #       'help': 'This is my parameter help',
  #       'dest': 'myparameter',
  #       'default': '',
  #       'type': 'unicode'})]
  #
  # Where all arguments into the dict object have a direct translation
  # into the argparse parser.
  ARGUMENTS = []

  def __init__(self, pre_obj, incoming_queue, outgoing_queue):
    """Constructor for a registry plugin.

    Args:
      pre_obj: The pre-processing object that contains information gathered
      during preprocessing of data.
      incoming_queue: A queue that is used to listen to incoming events.
      outgoing_queue: The queue used to send back reports, tags and anomaly
                      related events.
    """
    self._config = pre_obj
    self._queue = incoming_queue
    self._outgoing_queue = outgoing_queue

    # An AnalysisReport object.
    self._report = AnalysisReport()
    self._report.plugin_name = self.plugin_name

    self.plugin_type = self.TYPE_REPORT

    # A list of of all discovered EventAnomaly objects.
    # TODO: Implement the EventAnomaly object.
    self._anomalies = []
    # A list of all discovered EventTag objects.
    self._tags = []

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.NAME

  @abc.abstractmethod
  def ExamineEvent(self, event_object):
    """Take an EventObject and send it through analysis."""

  @abc.abstractmethod
  def CompileReport(self):
    """Compile a report object based on gathered information.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.
    """

  def ExamineSerializedEvent(self, serialized_event):
    """Take a serialized event and send it through analysis."""
    event_object = event.EventObject()
    try:
      event_object.FromJson(serialized_event)
    except ValueError as error_message:
      logging.warning(u'Unable to deserialize an event. Error: {}'.format(
          error_message))
      return

    self.ExamineEvent(event_object)

  def RunPlugin(self):
    """For each item in the queue send the read event to analysis."""
    for item in self._queue.PopItems():
      self.ExamineSerializedEvent(item)

    self.CompileReport()
    self._report.time_compiled = int(time.time() * 1e6)
    self._outgoing_queue.Queue(
        MESSAGE_STRUCT.build(MESSAGE_REPORT) + self._report.ToProtoString())

    for tag in self._tags:
      self._outgoing_queue.Queue(
          MESSAGE_STRUCT.build(MESSAGE_TAG) + tag.ToProtoString())

    # TODO: Add anomalies into the queue (need to implement anomalies
    # first).


class AnalysisReport(object):
  """An analysis report object, used as a placeholder for reports."""

  def ToProto(self):
    """Return a serialized protobuf for the analysis report."""
    proto = plaso_storage_pb2.AnalysisReport()
    proto.time_compiled = getattr(self, 'time_compiled', 0)
    plugin_name = getattr(self, 'plugin_name', None)

    if plugin_name:
      proto.plugin_name = plugin_name

    proto.text = getattr(self, 'text', 'N/A')

    for image in getattr(self, 'images', []):
      proto.images.append(image)

    if hasattr(self, 'report_dict'):
      dict_proto = plaso_storage_pb2.Dict()
      for key, value in getattr(self, 'report_dict', {}).iteritems():
        sub_proto = dict_proto.attributes.add()
        event.AttributeToProto(sub_proto, key, value)
      proto.report_dict.MergeFrom(dict_proto)

    if hasattr(self, 'report_array'):
      list_proto = plaso_storage_pb2.Array()
      for value in getattr(self, 'report_array', []):
        sub_proto = list_proto.values.add()
        event.AttributeToProto(sub_proto, '', value)

      proto.report_array.MergeFrom(list_proto)

    return proto

  def FromProto(self, proto):
    """Create an AnlysisReport object from a serialized protobuf."""
    if not isinstance(proto, plaso_storage_pb2.AnalysisReport):
      raise RuntimeError('Unsupported proto')

    for proto_attribute, value in proto.ListFields():
      if proto_attribute.name == 'report_dict':
        new_value = {}
        for proto_dict in proto.report_dict.attributes:
          dict_key, dict_value = event.AttributeFromProto(proto_dict)
          new_value[dict_key] = dict_value
        setattr(self, proto_attribute.name, new_value)
      elif proto_attribute.name == 'report_array':
        new_value = []

        for proto_array in proto.report_array.values:
          _, list_value = event.AttributeFromProto(proto_array)
          new_value.append(list_value)
        setattr(self, proto_attribute.name, new_value)
      else:
        setattr(self, proto_attribute.name, value)

  def ToProtoString(self):
    """Serialize the object into a string."""
    proto = self.ToProto()

    return proto.SerializeToString()

  def FromProtoString(self, proto_string):
    """Unserializes the AnalysisReport from a serialized protobuf."""
    proto = plaso_storage_pb2.AnalysisReport()
    proto.ParseFromString(proto_string)
    self.FromProto(proto)

  def String(self):
    """Return an unicode string representation of the report."""
    return unicode(self)

  def __unicode__(self):
    """Return an unicode string representation of the report."""
    # TODO: Make this a more complete function that includes images
    # and the option of saving as a full fledged HTML document.
    string_list = []
    string_list.append(u'Report generated from: {}'.format(self.plugin_name))
    if getattr(self, 'time_compiled', 0):
      string_list.append(u'Generated on: {}'.format(
          putils.PrintTimestamp(self.time_compiled)))
    if getattr(self, 'filter_string', ''):
      string_list.append(u'Filter String: {}'.format(
          getattr(self, 'filter_string', '')))
    string_list.append(u'')
    string_list.append(u'Report text:')
    string_list.append(self.text)

    return u'\n'.join(string_list)
