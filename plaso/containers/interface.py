# -*- coding: utf-8 -*-
"""The attribute container interface."""

from efilter.protocols import structured

class AttributeContainer(object):
  """Class that defines the attribute container interface.

  This is the the base class for those object that exists primarily as
  a container of attributes with basic accessors and mutators.

  The CONTAINER_TYPE class attribute contains a string that identifies
  the container type e.g. the container type "event" identifiers an event
  object.
  """
  CONTAINER_TYPE = None

  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      A dictionary containing the attribute container attributes.
    """
    dictionary = {}
    for attribute_name in iter(self.__dict__.keys()):
      attribute_value = getattr(self, attribute_name, None)
      if attribute_value is not None:
        dictionary[attribute_name] = attribute_value

    return dictionary

  def GetAttributes(self):
    """Retrieves the attributes from the attribute container.

    Attributes that are set to None are ignored.

    Yields:
      A tuple containing the attribute container attribute name and value.
    """
    for attribute_name in iter(self.__dict__.keys()):
      attribute_value = getattr(self, attribute_name, None)
      if attribute_value is not None:
        yield attribute_name, attribute_value

# Efilter protocol definition to enable filtering of containers.
structured.IStructured.implement(
  for_type=AttributeContainer,
  implementations = {
    structured.resolve: lambda container, key: getattr(container, key, None),
    structured.getmembers_runtime: lambda container: container.__dict__.keys(),
  })