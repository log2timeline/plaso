# -*- coding: utf-8 -*-
"""The attribute container interface."""


class AttributeContainer(object):
  """Class that defines the attribute container interface.

  This is the the base class for those object that exists primarily as
  a container of attributes with basic accessors and mutators.
  """

  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      A dictionary containing the attribute container attributes.
    """
    result_dict = {}
    for attribute_name in iter(self.__dict__.keys()):
      attribute_value = getattr(self, attribute_name, None)
      if attribute_value is not None:
        result_dict[attribute_name] = attribute_value

    return result_dict

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
