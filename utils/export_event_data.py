#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract the event data attribute containers schema."""

import argparse
import importlib
import inspect
import logging
import pkgutil
import sys

from plaso.containers import events


class EventDataAttributeContainersSchemaExtractor(object):
  """Event data attribute containers schema extractor."""

  def FormatSchema(self, attribute_containers):
    """Formats the event data attribute containers as a schema.

    Args:
      attribute_containers (list[class]): event data attribute container
          classes.

    Returns:
      str: event data schema.
    """
    lines = []

    for cls in sorted(attribute_containers, key=lambda cls: cls.DATA_TYPE):
      try:
        event_data = cls()
      except TypeError:
        logging.warning('Unable to inspect: {0:s}'.format(cls.DATA_TYPE))
        continue

      lines.append('{0:s}'.format(event_data.data_type))
      for name in sorted(event_data.GetAttributeNames()):
        if name and name[0] != '_':
          lines.append('  {0:s}'.format(name))
      lines.append('')

    return '\n'.join(lines)

  def _GetAttributeContainersFromPackage(self, package):
    """Retrieves event data attribute containers from a package.

    Args:
      package (list[str]): package name segments such as ["plaso", "parsers"].

    Returns:
      list[class]: event data attribute container classes.
    """
    attribute_containers = []
    package_path = '/'.join(package)
    for _, name, is_package in pkgutil.iter_modules(path=[package_path]):
      if package_path == 'plaso/containers' and name in ('errors', 'events'):
        continue

      sub_package = list(package)
      sub_package.append(name)
      if is_package:
        sub_containers = self._GetAttributeContainersFromPackage(sub_package)
        attribute_containers.extend(sub_containers)
      else:
        module_path = '.'.join(sub_package)
        module_object = importlib.import_module(module_path)
        for _, cls in inspect.getmembers(module_object, inspect.isclass):
          if issubclass(cls, events.EventData):
            attribute_containers.append(cls)

    return attribute_containers

  def GetAttributeContainers(self):
    """Retrieves event data attribute containers from Plaso.

    Returns:
      list[plaso.EventData]: event data attribute containers.
    """
    return self._GetAttributeContainersFromPackage(['plaso'])


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Extract the event data schema from Plaso.'))

  argument_parser.parse_args()

  extractor = EventDataAttributeContainersSchemaExtractor()

  attribute_containers = extractor.GetAttributeContainers()
  if not attribute_containers:
    print('Unable to determine event data attribute containers')
    return False

  schema = extractor.FormatSchema(attribute_containers)
  print(schema)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
