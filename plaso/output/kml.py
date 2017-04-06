# -*- coding: utf-8 -*-
"""An output module that writes event with geography data to a KML XML file.

The Keyhole Markup Language (KML) is an XML notation for expressing geographic
annotation and visualization within Internet-based, two-dimensional maps and
three-dimensional Earth browsers.
"""

from xml.etree import ElementTree

from plaso.output import interface
from plaso.output import manager
from plaso.output import rawpy


class KMLOutputModule(interface.LinearOutputModule):
  """Output module for a Keyhole Markup Language (KML) XML file."""

  NAME = u'kml'
  DESCRIPTION = u'Saves events with geography data into a KML format.'

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    latitude = getattr(event_object, u'latitude', None)
    longitude = getattr(event_object, u'longitude', None)
    if latitude is not None and longitude is not None:
      placemark_xml_element = ElementTree.Element(u'Placemark')

      name_xml_element = ElementTree.SubElement(placemark_xml_element, u'name')

      name_xml_element.text = u'PLACEHOLDER FOR EVENT IDENTIFIER'

      description_xml_element = ElementTree.SubElement(
          placemark_xml_element, u'description')
      # TODO: move the description formatting into this output module.
      description_xml_element.text = (
          rawpy.NativePythonFormatterHelper.GetFormattedEventObject(
              event_object))

      point_xml_element = ElementTree.SubElement(
          placemark_xml_element, u'Point')

      coordinates_xml_element = ElementTree.SubElement(
          point_xml_element, u'coordinates')
      coordinates_xml_element.text = u'{0!s},{1!s}'.format(longitude, latitude)

      # Note that ElementTree.tostring() will appopriately escape
      # the input data.
      xml_string = ElementTree.tostring(placemark_xml_element)

      self._WriteLine(xml_string.encode(self._output_mediator.encoding))

  def WriteHeader(self):
    """Writes the header to the output."""
    xml_string = (
        u'<?xml version="1.0" encoding="{0:s}"?>'
        u'<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'.format(
            self._output_mediator.encoding))
    self._WriteLine(xml_string.encode(self._output_mediator.encoding))

  def WriteFooter(self):
    """Writes the footer to the output."""
    xml_string = u'</Document></kml>'
    self._WriteLine(xml_string.encode(self._output_mediator.encoding))


manager.OutputManager.RegisterOutput(KMLOutputModule)
