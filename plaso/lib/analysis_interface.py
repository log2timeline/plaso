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
import time

from plaso.lib import event
from plaso.lib import registry
from plaso.proto import plaso_storage_pb2


class AnalysisPlugin(object):
  """Analysis plugin gets a copy of each read event for analysis."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # The URLS should contain a list of URL's with additional information about
  # this analysis plugin.
  URLS = []

  # A flag indicating whether or not this is a "heavy" plugin. What defines
  # is something that is perhaps too computationally heavy to be run during
  # event extraction and should rather be run during post-processing.
  # Since most plugins should perhaps rather be run during post-processing
  # this is set to True by default and needs to be overwritten if the plugin
  # should be able to run during the extraction phase.
  HEAVY = True

  # All the possible report types.
  TYPE_ANOMALY = 1
  TYPE_STATISTICS = 2
  TYPE_TAG = 3

  def __init__(self, pre_obj, incoming_queue):
    """Constructor for a registry plugin.

    Args:
      pre_obj: The pre-processing object that contains information gathered
      during preprocessing of data.
      incoming_queue: A queue that is used to listen to incoming events.
    """
    self._config = pre_obj
    self._queue = incoming_queue

    # An AnalysisReport object.
    self._report = AnalysisReport()
    self._report.plugin_name = self.plugin_name

    self.plugin_type = self.TYPE_STATISTICS

    # A list of of all discovered EventAnomaly objects.
    # TODO: Implement the EventAnomaly object.
    self._anomalies = []
    # A list of all discovered EventTag objects.
    self._tags = []

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.__class__.__name__

  @abc.abstractmethod
  def ExamineEvent(self, event_object):
    """Take an EventObject and send it through analysis."""

  def ExamineSerializedEvent(self, serialized_event):
    """Take a serialized event and send it through analysis."""
    event_object = event.EventObject()
    event_object.FromProtoString(serialized_event)

    self.ExamineEvent(event_object)

  def RunPlugin(self):
    """For each item in the queue send the read event to analysis."""
    for item in self._queue.PopItems():
      self.ExamineEvent(item)

  def GetReport(self):
    """Return a report object back from the plugin."""
    self._report.time_compiled = int(time.time() * 1e6)
    return self._report

  def GetAnomalies(self):
    """Return a list of anomalies produced by the plugin."""
    return self._anomalies

  def GetTags(self):
    """Return a list of tags produced by the plugin."""
    return self._tags


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

  # TODO: Implement a __str__ function or some sort of textual
  # representation of the analysis report. Even a HTML output function
  # that would take into consideration the images tag, etc.
