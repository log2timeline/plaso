# -*- coding: utf-8 -*-
"""The attribute container interface."""


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
    return '{0:d}'.format(self._identifier)


class AttributeContainer(object):
  """The attribute container interface.

  This is the the base class for those object that exists primarily as
  a container of attributes with basic accessors and mutators.

  The CONTAINER_TYPE class attribute contains a string that identifies
  the container type, for example the container type "event" identifiers
  an event object.

  Attributes are public class members of an serializable type. Protected and
  private class members are not to be serialized, with the exception of those
  defined in _SERIALIZABLE_PROTECTED_ATTRIBUTES.
  """
  CONTAINER_TYPE = None

  # Names of protected attributes, those with a leading underscore, that
  # should be serialized.
  _SERIALIZABLE_PROTECTED_ATTRIBUTES = []

  def __init__(self):
    """Initializes an attribute container."""
    super(AttributeContainer, self).__init__()
    self._identifier = AttributeContainerIdentifier()

  def CopyFromDict(self, attributes):
    """Copies the attribute container from a dictionary.

    Args:
      attributes (dict[str, object]): attribute values per name.
    """
    for attribute_name, attribute_value in attributes.items():
      # Not using startswith to improve performance.
      if (attribute_name[0] != '_' or
          attribute_name in self._SERIALIZABLE_PROTECTED_ATTRIBUTES):
        self.__dict__[attribute_name] = attribute_value

  def CopyToDict(self):
    """Copies the attribute container to a dictionary.

    Returns:
      dict[str, object]: attribute values per name.
    """
    return dict(self.GetAttributes())

  def GetAttributeNames(self):
    """Retrieves the names of all attributes.

    Returns:
      list[str]: attribute names.
    """
    attribute_names = list(self._SERIALIZABLE_PROTECTED_ATTRIBUTES)
    for attribute_name in self.__dict__:
      # Not using startswith to improve performance.
      if attribute_name[0] != '_':
        attribute_names.append(attribute_name)

    return attribute_names

  def GetAttributes(self):
    """Retrieves the attribute names and values.

    Attributes that are set to None are ignored.

    Yields:
      tuple[str, object]: attribute name and value.
    """
    for attribute_name, attribute_value in self.__dict__.items():
      # Not using startswith to improve performance.
      if attribute_value is not None and (
          attribute_name[0] != '_' or
          attribute_name in self._SERIALIZABLE_PROTECTED_ATTRIBUTES):
        yield attribute_name, attribute_value

  def GetAttributeValuesHash(self):
    """Retrieves a comparable string of the attribute values.

    Returns:
      int: hash of comparable string of the attribute values.
    """
    return hash(self.GetAttributeValuesString())

  def GetAttributeValuesString(self):
    """Retrieves a comparable string of the attribute values.

    Returns:
      str: comparable string of the attribute values.
    """
    attributes = []
    for attribute_name, attribute_value in sorted(self.__dict__.items()):
      # Not using startswith to improve performance.
      if attribute_value is not None and (
          attribute_name[0] != '_' or
          attribute_name in self._SERIALIZABLE_PROTECTED_ATTRIBUTES):
        if isinstance(attribute_value, dict):
          attribute_value = sorted(attribute_value.items())

        elif isinstance(attribute_value, bytes):
          attribute_value = repr(attribute_value)

        attribute_string = '{0:s}: {1!s}'.format(
            attribute_name, attribute_value)
        attributes.append(attribute_string)

    return ', '.join(attributes)

  def GetIdentifier(self):
    """Retrieves the identifier.

    The identifier is a storage specific value that should not be serialized.

    Returns:
      AttributeContainerIdentifier: an unique identifier for the container.
    """
    return self._identifier

  def MatchesExpression(self, expression):
    """Determines if an attribute container matches the expression.

    Args:
      expression (code|str): expression.

    Returns:
      bool: True if the attribute container matches the expression, False
          otherwise.
    """
    result = not expression
    if expression:
      namespace = dict(self.GetAttributes())
      # Make sure __builtins__ contains an empty dictionary.
      namespace['__builtins__'] = {}

      try:
        result = eval(expression, namespace)  # pylint: disable=eval-used
      except Exception:  # pylint: disable=broad-except
        pass

    return result

  def SetIdentifier(self, identifier):
    """Sets the identifier.

    The identifier is a storage specific value that should not be serialized.

    Args:
      identifier (AttributeContainerIdentifier): identifier.
    """
    self._identifier = identifier
