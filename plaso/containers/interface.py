# -*- coding: utf-8 -*-
"""The attribute container interface."""

import abc


class AttributeContainer(object):
  """Class that defines the attribute container interface.

  This is the the base class for those object that exists primarily as
  a container of attributes with basic accessors and mutators.
  """

  @abc.abstractmethod
  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      A dictionary containing the attribute container attributes.
    """

  @abc.abstractmethod
  def GetAttributes(self):
    """Retrieves the attributes from the attribute container.

    Attributes that are set to None are ignored.

    Yields:
      A tuple containing the attribute container attribute name and value.
    """
