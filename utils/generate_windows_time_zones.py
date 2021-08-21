#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to generate Windows time zone name to Python mappings."""

import argparse
import sys

import urllib.request as urllib_request

from defusedxml import ElementTree


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Generate Windows time zone name to Python mappings.'))

  argument_parser.parse_args()

  url = ('https://raw.githubusercontent.com/unicode-org/cldr/master/common/'
         'supplemental/windowsZones.xml')
  with urllib_request.urlopen(url) as request_object:
    windows_time_zones_xml_data = request_object.read()

  windows_time_zones_xml_data = windows_time_zones_xml_data.decode('utf-8')

  windows_time_zones_xml = ElementTree.fromstring(windows_time_zones_xml_data)

  time_zone_mappings = {
    'Kamchatka Standard Time': 'Asia/Kamchatka',
    'Mexico Standard Time 2': 'America/Chihuahua',
    'Mexico Standard Time': 'America/Mexico_City',
    'Mid-Atlantic Standard Time': 'America/New_York'}
  for windows_time_zone in windows_time_zones_xml.findall('.//mapZone'):
    if windows_time_zone.attrib['territory'] == '001':
      windows_name = windows_time_zone.attrib['other']
      time_zone_mappings[windows_name] = windows_time_zone.attrib['type']

  for windows_name, python_name in sorted(time_zone_mappings.items()):
    print('    \'{0:s}\': \'{1:s}\''.format(windows_name, python_name))

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
