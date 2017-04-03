# -*- coding: utf-8 -*-
"""The attribute container interface."""

from efilter.protocols import structured


class AttributeContainerIdentifier(object):
  """The attribute container identifier.

  The identifier is used to uniquely identify attribute containers.
  The value should be unique at runtime and in storage.
  """

  def __init__(self):
    """Initializes an attribute container identifier."""
    super(AttributeContainerIdentifier, self).__init__()
    self._identifier = id(self)

  def CopyToString(self):
    """Copies the identifier to a string representation.

    Returns:
      str: unique identifier or None.
    """
    return u'{0:d}'.format(self._identifier)


class AttributeContainer(object):
  """The attribute container interface.

  This is the the base class for those object that exists primarily as
  a container of attributes with basic accessors and mutators.

  The CONTAINER_TYPE class attribute contains a string that identifies
  the container type e.g. the container type "event" identifiers an event
  object.

  Attributes are public class members of an serializable type. Protected
  and private class members are not to be serialized.
  """
  CONTAINER_TYPE = None

  def __init__(self):
    """Initializes an attribute container."""
    super(AttributeContainer, self).__init__()
    self._identifier = AttributeContainerIdentifier()
    self._session_identifier = None

  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      dict[str, object]: attribute values per name.
    """
    return {
        attribute_name: attribute_value
        for attribute_name, attribute_value in self.GetAttributes()}

  def GetAttributeNames(self):
    """Retrieves the names of all attributes.

    Returns:
      list[str]: attribute names.
    """
    attribute_names = []
    for attribute_name in iter(self.__dict__.keys()):
      if attribute_name.startswith(u'_'):
        continue
      attribute_names.append(attribute_name)

    return attribute_names

  def GetAttributes(self):
    """Retrieves the attribute names and values.

    Attributes that are set to None are ignored.

    Yields:
      tuple[str, object]: attribute name and value.
    """
    for attribute_name, attribute_value in iter(self.__dict__.items()):
      if attribute_name.startswith(u'_') or attribute_value is None:
        continue

      yield attribute_name, attribute_value

  def GetIdentifier(self):
    """Retrieves the identifier.

    The identifier is a storage specific value that should not be serialized.

    Returns:
      AttributeContainerIdentifier: an unique identifier for the container.
    """
    return self._identifier

  def GetSessionIdentifier(self):
    """Retrieves the session identifier.

    The session identifier is a storage specific value that should not
    be serialized.

    Returns:
      str: session identifier.
    """
    return self._session_identifier

  def SetIdentifier(self, identifier):
    """Sets the identifier.

    The identifier is a storage specific value that should not be serialized.

    Args:
      identifier (AttributeContainerIdentifier): identifier.
    """
    self._identifier = identifier

  def SetSessionIdentifier(self, session_identifier):
    """Sets the session identifier.

    The session identifier is a storage specific value that should not
    be serialized.

    Args:
      session_identifier (str): session identifier.
    """
    self._session_identifier = session_identifier


# Efilter protocol definition to enable filtering of containers.
structured.IStructured.implement(
    for_type=AttributeContainer,
    implementations={
        structured.resolve:
            lambda container, key: getattr(container, key, None),
        structured.getmembers_runtime:
            lambda container: container.GetAttributeNames()})
