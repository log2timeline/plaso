# -*- coding: utf-8 -*-
"""A plugin to enable quick triage of Windows Services."""

from __future__ import unicode_literals

import yaml

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports
from plaso.lib import py2to3
from plaso.winnt import human_readable_service_enums


class WindowsService(yaml.YAMLObject):
  """Class to represent a Windows Service.

  Attributes:
    image_path (str): value of the ImagePath value of the service key.
    name (str): name of the service
    object_name (str): value of the ObjectName value of the service key.
    service_dll (str): value of the ServiceDll value in the service's Parameters
        subkey.
    service_type (int): value of the Type value of the service key.
    source (tuple[str, str]) : tuple containing the path and registry key
        describing where the service was found
    start_type (int):  value of the Start value of the service key.
    """
  # This is used for comparison operations and defines attributes that should
  # not be used during evaluation of whether two services are the same.
  COMPARE_EXCLUDE = frozenset(['sources'])

  _REGISTRY_KEY_PATH_SEPARATOR = '\\'

  # YAML attributes
  yaml_tag = '!WindowsService'
  yaml_loader = yaml.SafeLoader
  yaml_dumper = yaml.SafeDumper

  def __init__(
      self, name, service_type, image_path, start_type, object_name, source,
      service_dll=None):
    """Initializes a Windows service object.

    Args:
      name (str): name of the service
      service_type (int): value of the Type value of the service key.
      image_path (str): value of the ImagePath value of the service key.
      start_type (int):  value of the Start value of the service key.
      object_name (str): value of the ObjectName value of the service key.
      source (tuple[str, str]) : tuple containing the path and registry key
          describing where the service was found
      service_dll (Optional[str]): value of the ServiceDll value in the
          service's Parameters subkey.

    Raises:
      TypeError: If a tuple with two elements is not passed as the 'source'
                 argument.
    """
    super(WindowsService, self).__init__()
    self.anomalies = []
    self.image_path = image_path
    self.name = name
    self.object_name = object_name
    self.service_dll = service_dll
    self.service_type = service_type
    self.start_type = start_type

    if isinstance(source, tuple):
      if len(source) != 2:
        raise TypeError('Source arguments must be tuple of length 2.')
      # A service may be found in multiple Control Sets or Registry hives,
      # hence the list.
      self.sources = [source]
    else:
      raise TypeError('Source argument must be a tuple.')

  def __eq__(self, other_service):
    """Custom equality method so that we match near-duplicates.

    Compares two service objects together and evaluates if they are
    the same or close enough to be considered to represent the same service.

    For two service objects to be considered the same they need to
    have the the same set of attributes and same values for all their
    attributes, other than those enumerated as reserved in the
    COMPARE_EXCLUDE constant.

    Args:
      other_service (WindowsService): service we are testing for equality.

    Returns:
      bool: whether the services are equal.
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

  @classmethod
  def FromEventData(cls, event_data):
    """Creates a service object from event data.

    Args:
      event_data (EventData): event data.

    Returns:
      WindowsService: service.
    """
    if event_data.pathspec:
      source = (event_data.pathspec.location, event_data.key_path)
    else:
      source = ('Unknown', 'Unknown')

    return cls(
        event_data.name, event_data.service_type, event_data.image_path,
        event_data.start_type, event_data.object_name, source,
        service_dll=event_data.service_dll)

  def HumanReadableType(self):
    """Return a human readable string describing the type value.

    Returns:
      str: human readable description of the type value.
    """
    if isinstance(self.service_type, py2to3.STRING_TYPES):
      return self.service_type
    return human_readable_service_enums.SERVICE_ENUMS['Type'].get(
        self.service_type, '{0:d}'.format(self.service_type))

  def HumanReadableStartType(self):
    """Return a human readable string describing the start type value.

    Returns:
      str: human readable description of the start type value.
    """
    if isinstance(self.start_type, py2to3.STRING_TYPES):
      return self.start_type
    return human_readable_service_enums.SERVICE_ENUMS['Start'].get(
        self.start_type, '{0:d}'.format(self.start_type))


class WindowsServiceCollection(object):
  """Class to hold and de-duplicate Windows Services."""

  def __init__(self):
    """Initialize a collection that holds Windows Service."""
    super(WindowsServiceCollection, self).__init__()
    self._services = []

  def AddService(self, new_service):
    """Add a new service to the list of ones we know about.

    Args:
      new_service (WindowsService): the service to add.
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
    """list[WindowsService]: services in this collection."""
    return self._services


class WindowsServicesAnalysisPlugin(interface.AnalysisPlugin):
  """Provides a single list of for Windows services found in the Registry."""

  NAME = 'windows_services'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  _SUPPORTED_EVENT_DATA_TYPES = frozenset([
      'windows:registry:service'])

  def __init__(self):
    """Initializes the Windows Services plugin."""
    super(WindowsServicesAnalysisPlugin, self).__init__()
    self._output_format = 'text'
    self._service_collection = WindowsServiceCollection()

  def _FormatServiceText(self, service):
    """Produces a human readable multi-line string representing the service.

    Args:
      service (WindowsService):  service to format.

    Returns:
      str: human readable representation of a Windows Service.
    """
    service_type = service.HumanReadableType()
    start_type = service.HumanReadableStartType()

    string_segments = [
        service.name,
        '\tImage Path    = {0:s}'.format(service.image_path or ''),
        '\tService Type  = {0:s}'.format(service_type),
        '\tStart Type    = {0:s}'.format(start_type),
        '\tService Dll   = {0:s}'.format(service.service_dll or ''),
        '\tObject Name   = {0:s}'.format(service.object_name or ''),
        '\tSources:']

    string_segments.extend([
        '\t\t{0:s}:{1:s}'.format(source[0], source[1])
        for source in service.sources])
    return '\n'.join(string_segments)

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: report.
    """
    # TODO: move YAML representation out of plugin and into serialization.
    lines_of_text = []
    if self._output_format == 'yaml':
      lines_of_text.append(
          yaml.safe_dump_all(self._service_collection.services))
    else:
      lines_of_text.append('Listing Windows Services')
      for service in self._service_collection.services:
        lines_of_text.append(self._FormatServiceText(service))
        lines_of_text.append('')

    lines_of_text.append('')
    report_text = '\n'.join(lines_of_text)
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)

  # pylint: disable=unused-argument
  def ExamineEvent(self, mediator, event, event_data):
    """Analyzes an event and creates Windows Services as required.

    At present, this method only handles events extracted from the Registry.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
      event_data (EventData): event data.
    """
    if event_data.data_type not in self._SUPPORTED_EVENT_DATA_TYPES:
      return

    # TODO: Handle event log entries here also (ie, event id 4697).
    service = WindowsService.FromEventData(event_data)
    self._service_collection.AddService(service)

  def SetOutputFormat(self, output_format):
    """Sets the output format of the generated report.

    Args:
      output_format (str): format the plugin should used to produce its output.
    """
    self._output_format = output_format


manager.AnalysisPluginManager.RegisterPlugin(WindowsServicesAnalysisPlugin)
