# -*- coding: utf-8 -*-
"""An output module that writes event with geography data to a KML XML file.

The Keyhole Markup Language (KML) is an XML notation for expressing geographic
annotation and visualization within Internet-based, two-dimensional maps and
three-dimensional Earth browsers.
"""

from __future__ import unicode_literals

import codecs

from xml.etree import ElementTree

from plaso.output import interface
from plaso.output import manager
from plaso.output import rawpy


class KMLOutputModule(interface.LinearOutputModule):
  """Output module for a Keyhole Markup Language (KML) XML file."""

  NAME = 'kml'
  DESCRIPTION = 'Saves events with geography data into a KML format.'

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    latitude = getattr(event_data, 'latitude', None)
    longitude = getattr(event_data, 'longitude', None)
    if latitude is not None and longitude is not None:
      placemark_xml_element = ElementTree.Element('Placemark')

      name_xml_element = ElementTree.SubElement(placemark_xml_element, 'name')

      event_identifier = event.GetIdentifier()
      name_xml_element.text = '{0!s}'.format(event_identifier.CopyToString())

      description_xml_element = ElementTree.SubElement(
          placemark_xml_element, 'description')
      # TODO: move the description formatting into this output module.
      description_xml_element.text = (
          rawpy.NativePythonFormatterHelper.GetFormattedEvent(
              event, event_data, event_tag))

      point_xml_element = ElementTree.SubElement(
          placemark_xml_element, 'Point')

      coordinates_xml_element = ElementTree.SubElement(
          point_xml_element, 'coordinates')
      coordinates_xml_element.text = '{0!s},{1!s}'.format(longitude, latitude)

      # Note that ElementTree.tostring() will appropriately escape
      # the input data.
      xml_string = ElementTree.tostring(placemark_xml_element)

      output_text = codecs.decode(xml_string, self._output_mediator.encoding)
      self._output_writer.Write(output_text)

  def WriteHeader(self):
    """Writes the header to the output."""
    xml_string = (
        '<?xml version="1.0" encoding="{0:s}"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'.format(
            self._output_mediator.encoding))
    self._output_writer.Write(xml_string)

  def WriteFooter(self):
    """Writes the footer to the output."""
    xml_string = '</Document></kml>'
    self._output_writer.Write(xml_string)


manager.OutputManager.RegisterOutput(KMLOutputModule)
