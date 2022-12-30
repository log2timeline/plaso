# -*- coding: utf-8 -*-
"""An output module that writes event with geography data to a KML XML file.

The Keyhole Markup Language (KML) is an XML notation for expressing geographic
annotation and visualization within Internet-based, two-dimensional maps and
three-dimensional Earth browsers.
"""

import codecs

from xml.etree import ElementTree

from plaso.lib import definitions
from plaso.output import interface
from plaso.output import manager
from plaso.output import rawpy


class KMLOutputModule(interface.TextFileOutputModule):
  """Output module for a Keyhole Markup Language (KML) XML file."""

  NAME = 'kml'
  DESCRIPTION = 'Saves events with geography data into a KML format.'

  def __init__(self):
    """Initializes an output module."""
    event_formatting_helper = rawpy.NativePythonEventFormattingHelper()
    super(KMLOutputModule, self).__init__(event_formatting_helper)

  def WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    latitude = field_values.get('latitude', None)
    longitude = field_values.get('longitude', None)
    if None in (latitude, longitude):
      return

    # TODO: make description_text KML values.
    reserved_attributes = []
    additional_attributes = []

    for field_name, field_value in sorted(field_values.items()):
      if field_name in (
          '_event_identifier', '_event_tag_labels', '_timestamp', 'path_spec'):
        continue

      field_string = '  {{{0!s}}} {1!s}'.format(field_name, field_value)

      if field_name in definitions.RESERVED_VARIABLE_NAMES:
        reserved_attributes.append(field_string)
      else:
        additional_attributes.append(field_string)

    lines_of_text = [
        '+-' * 40,
        '[Timestamp]:',
        '  {0:s}'.format(field_values['_timestamp'])]

    path_specification = field_values.get('path_spec', None)
    if path_specification:
      lines_of_text.extend([
          '',
          '[Pathspec]:'])
      lines_of_text.extend([
          '  {0:s}'.format(line)
          for line in path_specification.comparable.split('\n')])

      # Remove additional empty line.
      lines_of_text.pop()

    lines_of_text.extend([
        '',
        '[Reserved attributes]:'])
    lines_of_text.extend(reserved_attributes)

    lines_of_text.extend([
        '',
        '[Additional attributes]:'])
    lines_of_text.extend(additional_attributes)

    event_tag_labels = field_values.get('_event_tag_labels', None)
    if event_tag_labels:
      labels = ', '.join([
          '\'{0:s}\''.format(label) for label in event_tag_labels])
      lines_of_text.extend([
          '',
          '[Tag]:',
          '  {{labels}} [{0:s}]'.format(labels)])

    lines_of_text.append('')

    description_text = '\n'.join(lines_of_text)

    placemark_xml_element = ElementTree.Element('Placemark')

    name_xml_element = ElementTree.SubElement(placemark_xml_element, 'name')
    name_xml_element.text = field_values['_event_identifier']

    description_xml_element = ElementTree.SubElement(
        placemark_xml_element, 'description')
    description_xml_element.text = '{0:s}\n'.format(description_text)

    point_xml_element = ElementTree.SubElement(placemark_xml_element, 'Point')

    coordinates_xml_element = ElementTree.SubElement(
        point_xml_element, 'coordinates')
    coordinates_xml_element.text = '{0!s},{1!s}'.format(longitude, latitude)

    # Note that ElementTree.tostring() will appropriately escape the input data.
    output_text = ElementTree.tostring(placemark_xml_element)

    output_text = codecs.decode(output_text, output_mediator.encoding)
    self.WriteText(output_text)

  def WriteFooter(self):
    """Writes the footer to the output."""
    self.WriteText('</Document></kml>')

  def WriteHeader(self, output_mediator):
    """Writes the header to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    xml_string = (
        '<?xml version="1.0" encoding="{0:s}"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'.format(
            output_mediator.encoding))
    self.WriteText(xml_string)


manager.OutputManager.RegisterOutput(KMLOutputModule)
