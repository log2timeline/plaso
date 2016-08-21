# -*- coding: utf-8 -*-
"""A plugin to enable quick triage of Windows Services."""

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
  COMPARE_EXCLUDE = frozenset([u'sources'])

  _REGISTRY_KEY_PATH_SEPARATOR = u'\\'

  # YAML attributes
  yaml_tag = u'!WindowsService'
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
        raise TypeError(u'Source arguments must be tuple of length 2.')
      # A service may be found in multiple Control Sets or Registry hives,
      # hence the list.
      self.sources = [source]
    else:
      raise TypeError(u'Source argument must be a tuple.')

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
  def FromEvent(cls, service_event):
    """Creates a service object from an event.

    Args:
      service_event (EventObject): event to create a new service object from.

    Returns:
      WindowsService: service.
    """
    _, _, name = service_event.key_path.rpartition(
        WindowsService._REGISTRY_KEY_PATH_SEPARATOR)
    service_type = service_event.regvalue.get(u'Type')
    image_path = service_event.regvalue.get(u'ImagePath')
    start_type = service_event.regvalue.get(u'Start')
    service_dll = service_event.regvalue.get(u'ServiceDll', u'')
    object_name = service_event.regvalue.get(u'ObjectName', u'')

    if service_event.pathspec:
      source = (service_event.pathspec.location, service_event.key_path)
    else:
      source = (u'Unknown', u'Unknown')
    return cls(
        name=name, service_type=service_type, image_path=image_path,
        start_type=start_type, object_name=object_name,
        source=source, service_dll=service_dll)

  def HumanReadableType(self):
    """Return a human readable string describing the type value.

    Returns:
      str: human readable description of the type value.
    """
    if isinstance(self.service_type, py2to3.STRING_TYPES):
      return self.service_type
    return human_readable_service_enums.SERVICE_ENUMS[u'Type'].get(
        self.service_type, u'{0:d}'.format(self.service_type))

  def HumanReadableStartType(self):
    """Return a human readable string describing the start type value.

    Returns:
      str: human readable description of the start type value.
    """
    if isinstance(self.start_type, py2to3.STRING_TYPES):
      return self.start_type
    return human_readable_service_enums.SERVICE_ENUMS[u'Start'].get(
        self.start_type, u'{0:d}'.format(self.start_type))


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

  NAME = u'windows_services'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  def __init__(self):
    """Initializes the Windows Services plugin."""
    super(WindowsServicesAnalysisPlugin, self).__init__()
    self._output_format = u'text'
    self._service_collection = WindowsServiceCollection()

  def _FormatServiceText(self, service):
    """Produces a human readable multi-line string representing the service.

    Args:
      service (WindowsService):  service to format.

    Returns:
      str: human readable representation of a Windows Service.
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
    if self._output_format == u'yaml':
      lines_of_text.append(
          yaml.safe_dump_all(self._service_collection.services))
    else:
      lines_of_text.append(u'Listing Windows Services')
      for service in self._service_collection.services:
        lines_of_text.append(self._FormatServiceText(service))
        lines_of_text.append(u'')

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)

  def ExamineEvent(self, mediator, event):
    """Analyzes an event and creates Windows Services as required.

      At present, this method only handles events extracted from the Registry.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
    """
    # TODO: Handle event log entries here also (ie, event id 4697).
    if getattr(event, u'data_type', None) != u'windows:registry:service':
      return
    else:
      # Create and store the service.
      service = WindowsService.FromEvent(event)
      self._service_collection.AddService(service)

  def SetOutputFormat(self, output_format):
    """Sets the output format of the generated report.

    Args:
      output_format: The format the the plugin should used to produce its
                     output, as a string.
    """
    self._output_format = output_format


manager.AnalysisPluginManager.RegisterPlugin(WindowsServicesAnalysisPlugin)
