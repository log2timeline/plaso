#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""A plugin to enable quick triage of Windows Services."""

import yaml

from plaso.analysis import interface
from plaso.lib import event
from plaso.winnt import human_readable_service_enums


class WindowsService(yaml.YAMLObject):
  """Class to represent a Windows Service."""
  # This is used for comparison operations and defines attributes that should
  # not be used during evaluation of whether two services are the same.
  COMPARE_EXCLUDE = frozenset(['sources'])

  KEY_PATH_SEPARATOR = u'\\'

  # YAML attributes
  yaml_tag = u'!WindowsService'
  yaml_loader = yaml.SafeLoader
  yaml_dumper = yaml.SafeDumper


  def __init__(self, name, service_type, image_path, start_type, object_name,
               source, service_dll=None):
    """Initializes a new Windows service object.

    Args:
      name: The name of the service
      service_type: The value of the Type value of the service key.
      image_path: The value of the ImagePath value of the service key.
      start_type: The value of the Start value of the service key.
      object_name: The value of the ObjectName value of the service key.
      source: A tuple of (pathspec, Registry key) describing where the
          service was found
      service_dll: Optional string value of the ServiceDll value in the
          service's Parameters subkey. The default is None.

    Raises:
      TypeError: If a tuple with two elements is not passed as the 'source'
      argument.
    """
    self.name = name
    self.service_type = service_type
    self.image_path = image_path
    self.start_type = start_type
    self.service_dll = service_dll
    self.object_name = object_name
    if isinstance(source, tuple):
      if len(source) != 2:
        raise TypeError(u'Source arguments must be tuple of length 2.')
      # A service may be found in multiple Control Sets or Registry hives,
      # hence the list.
      self.sources = [source]
    else:
      raise TypeError(u'Source argument must be a tuple.')
    self.anomalies = []

  @classmethod
  def FromEvent(cls, service_event):
    """Creates a Service object from an plaso event.

    Args:
      service_event: The event object (instance of EventObject) to create a new
          Service object from.

    """
    _, _, name = service_event.keyname.rpartition(
        WindowsService.KEY_PATH_SEPARATOR)
    service_type = service_event.regvalue.get('Type')
    image_path = service_event.regvalue.get('ImagePath')
    start_type = service_event.regvalue.get('Start')
    service_dll = service_event.regvalue.get('ServiceDll', u'')
    object_name = service_event.regvalue.get('ObjectName', u'')
    if service_event.pathspec:
      source = (service_event.pathspec.location, service_event.keyname)
    else:
      source = (u'Unknown', u'Unknown')
    return cls(
        name=name, service_type=service_type, image_path=image_path,
        start_type=start_type, object_name=object_name,
        source=source, service_dll=service_dll)

  def HumanReadableType(self):
    """Return a human readable string describing the type value."""
    return human_readable_service_enums.SERVICE_ENUMS['Type'].get(
        self.service_type, u'{0:d}'.format(self.service_type))

  def HumanReadableStartType(self):
    """Return a human readable string describing the start_type value."""
    return human_readable_service_enums.SERVICE_ENUMS['Start'].get(
        self.start_type, u'{0:d}'.format(self.start_type))

  def __eq__(self, other_service):
    """Custom equality method so that we match near-duplicates.

    Compares two service objects together and evaluates if they are
    the same or close enough to be considered to represent the same service.

    For two service objects to be considered the same they need to
    have the the same set of attributes and same values for all their
    attributes, other than those enumerated as reserved in the
    COMPARE_EXCLUDE constant.

    Args:
      other_service: The service (instance of WindowsService) we are testing
      for equality.

    Returns:
      A boolean value to indicate whether the services are equal.

    """
    if not isinstance(other_service, WindowsService):
      return False

    attributes = set(self.__dict__.keys())
    other_attributes = set(self.__dict__.keys())

    if attributes != other_attributes:
      return False

    # We compare the values for all attributes, other than those specifically
    # enumerated as not relevant for equality comparisons.
    for attribute in attributes.difference(self.COMPARE_EXCLUDE):
      if getattr(self, attribute, None) != getattr(
          other_service, attribute, None):
        return False

    return True


class WindowsServiceCollection(object):
  """Class to hold and de-duplicate Windows Services."""

  def __init__(self):
    """Initialize a collection that holds Windows Service."""
    self._services = []

  def AddService(self, new_service):
    """Add a new service to the list of ones we know about.

    Args:
      new_service: The service (instance of WindowsService) to add.
    """
    for service in self._services:
      if new_service == service:
        # If this service is the same as one we already know about, we
        # just want to add where it came from.
        service.sources.append(new_service.sources[0])
        return
    # We only add a new object to our list if we don't have
    # an identical one already.
    self._services.append(new_service)

  @property
  def services(self):
    """Get the services in this collection."""
    return self._services


class AnalyzeWindowsServicesPlugin(interface.AnalysisPlugin):
  """Provides a single list of for Windows services found in the Registry."""

  NAME = 'windows_services'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  ARGUMENTS = [
      ('--windows-services-output', {
          'dest': 'windows-services-output',
          'type': unicode,
          'help': 'Specify how the results should be displayed. Options are '
                  'text and yaml.',
          'action': 'store',
          'default': u'text',
          'choices': [u'text', u'yaml']}),]

  def __init__(self, incoming_queue, options=None):
    """Initializes the Windows Services plugin

    Args:
      incoming_queue: A queue to read events from.
      options: Optional command line arguments (instance of
      argparse.Namespace). The default is None.
    """
    super(AnalyzeWindowsServicesPlugin, self).__init__(incoming_queue)
    self._service_collection = WindowsServiceCollection()
    self.plugin_type = interface.AnalysisPlugin.TYPE_REPORT
    self._output_mode = getattr(options, 'windows-services-output', u'text')

  def ExamineEvent(self, analysis_context, event_object, **kwargs):
    """Analyzes an event_object and creates Windows Services as required.

      At present, this method only handles events extracted from the Registry.

    Args:
      analysis_context: The context object analysis plugins.
      event_object: The event object (instance of EventObject) to examine.
    """
    # TODO: Handle event log entries here also (ie, event id 4697).
    if getattr(event_object, 'data_type', None) != 'windows:registry:service':
      return
    else:
      # Create and store the service.
      service = WindowsService.FromEvent(event_object)
      self._service_collection.AddService(service)

  def _FormatServiceText(self, service):
    """Produces a human readable multi-line string representing the service.

    Args:
      service: The service (instance of WindowsService) to format.
    """
    string_segments = [
        service.name,
        u'\tImage Path    = {0:s}'.format(service.image_path),
        u'\tService Type  = {0:s}'.format(service.HumanReadableType()),
        u'\tStart Type    = {0:s}'.format(service.HumanReadableStartType()),
        u'\tService Dll   = {0:s}'.format(service.service_dll),
        u'\tObject Name   = {0:s}'.format(service.object_name),
        u'\tSources:']
    for source in service.sources:
      string_segments.append(u'\t\t{0:s}:{1:s}'.format(source[0], source[1]))
    return u'\n'.join(string_segments)

  def CompileReport(self):
    """Compiles a report of the analysis.

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report = event.AnalysisReport()

    if self._output_mode == 'yaml':
      lines_of_text = []
      lines_of_text.append(
          yaml.safe_dump_all(self._service_collection.services))
    else:
      lines_of_text = ['Listing Windows Services']
      for service in self._service_collection.services:
        lines_of_text.append(self._FormatServiceText(service))
        # Separate services with a blank line.
        lines_of_text.append(u'')

    report.SetText(lines_of_text)

    return report
