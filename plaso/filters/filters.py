# -*- coding: utf-8 -*-
"""The event filter expression parser filter classes."""

from __future__ import unicode_literals

import abc
import logging
import re

from plaso.filters import helpers
from plaso.filters import value_expanders
from plaso.lib import errors
from plaso.lib import py2to3


class Filter(object):
  """Filter interface.

  Attributes:
    args (list[object]): arguments provided to the filter.
    value_expander (ValueExpander): value expanded that is used to expand
        arguments into comparable values.
    value_expander_cls (type): value expander class.
  """

  def __init__(self, arguments=None, value_expander=None):
    """Initializes a filter.

    Implementations expanders are provided by subclassing ValueExpander.

    Args:
      arguments (Optional[object]): arguments.
      value_expander (Optional[type]): class that is used to expand arguments
          into comparable values.

    Raises:
      ValueError: If value expander is not a subclass of ValueExpander.
    """
    logging.debug('Adding {0!s}'.format(arguments))

    if value_expander:
      if not issubclass(value_expander, value_expanders.ValueExpander):
        raise ValueError('{0:s} is not of type ValueExpander'.format(
            type(value_expander)))

    super(Filter, self).__init__()
    self.args = arguments or []
    self.value_expander = None
    self.value_expander_cls = value_expander

    if value_expander:
      self.value_expander = value_expander()

  def __str__(self):
    """Retrieve a string representation of the filter.

    Returns:
      str: a string representation of the filter.
    """
    return '{0:s}({1:s})'.format(self.__class__.__name__, ', '.join([
        str(argument) for argument in self.args]))

  def Filter(self, objects):
    """Retrieves objects that match the filter.

    Args:
      objects (list[object]): objects to filter.

    Returns:
      list[object]: objects that match the filter.
    """
    return filter(self.Matches, objects)

  @abc.abstractmethod
  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """


class AndFilter(Filter):
  """A filter that performs a boolean AND on the arguments.

  Note that if no conditions are passed, all objects will pass.
  """

  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """
    for child_filter in self.args:
      if not child_filter.Matches(obj):
        return False
    return True


class OrFilter(Filter):
  """A filter that performs a boolean OR on the arguments.

  Note that if no conditions are passed, all objects will pass.
  """

  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """
    if not self.args:
      return True

    for child_filter in self.args:
      if child_filter.Matches(obj):
        return True
    return False


class Operator(Filter):
  """Interface for filters that represent operators."""

  @abc.abstractmethod
  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """


class IdentityFilter(Operator):
  """A filter which always evaluates to True."""

  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True to indicated the object matches the filter.
    """
    return True


# TODO: remove, class is not used.
class UnaryOperator(Operator):
  """Interface for filters that represent unary operators."""

  def __init__(self, operand, **kwargs):
    """Initializes an unary operator.

    Args:
      operand (str): operand.

    Raises:
      InvalidNumberOfOperands: if the number of operands provided is not
          supported.
    """
    if len(operand) != 1:
      raise errors.InvalidNumberOfOperands((
          '{0:s} only supports 1 operand, provided were {1:d} '
          'operands.').format(self.__class__.__name__, len(operand)))

    super(UnaryOperator, self).__init__(arguments=[operand], **kwargs)

  @abc.abstractmethod
  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """


class BinaryOperator(Operator):
  """Interface for binary operators.

  Attributes:
    left_operand (object): left hand operand.
    right_operand (object): right hand operand.
  """

  def __init__(self, arguments=None, **kwargs):
    """Initializes a binary operator.

    Args:
      arguments (Optional[object]): operands of the filter.

    Raises:
      InvalidNumberOfOperands: if the number of operands provided is not
          supported.
    """
    if len(arguments) != 2:
      raise errors.InvalidNumberOfOperands((
          '{0:s} only supports 2 operands, provided were {1:d} '
          'operands.').format(self.__class__.__name__, len(arguments)))

    super(BinaryOperator, self).__init__(arguments=arguments, **kwargs)
    self.left_operand = arguments[0]
    self.right_operand = arguments[1]

  @abc.abstractmethod
  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """


class GenericBinaryOperator(BinaryOperator):
  """Shared functionality for common binary operators.

  Attribute:
    bool_value (bool): boolean value that represents the result of
        the operation.
  """

  def __init__(self, arguments=None, **kwargs):
    """Initializes a generic binary operator.

    Args:
      arguments (Optional[object]): operands of the filter.
    """
    super(GenericBinaryOperator, self).__init__(arguments=arguments, **kwargs)
    self.bool_value = True

  def FlipBool(self):
    """Negates the value of the bool_value attribute."""
    logging.debug('Negative matching.')
    self.bool_value = not self.bool_value

  @abc.abstractmethod
  def Operation(self, x, y):
    """Compares two values with the operator.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the values match according to the operator, False otherwise.
    """

  def Operate(self, values):
    """Determines if one or more values match the filter.

    Args:
      values (list[object]): values to match against the filter.

    Returns:
      bool: True if one or more values match, False otherwise.
    """
    for val in values:
      try:
        if self.Operation(val, self.right_operand):
          return True
      except (TypeError, ValueError):
        pass

    return False

  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """
    key = self.left_operand
    values = self.value_expander.Expand(obj, key)
    values = list(values)
    if values and self.Operate(values):
      return self.bool_value
    return not self.bool_value


class Equals(GenericBinaryOperator):
  """Equals (==) operator."""

  def Operation(self, x, y):
    """Compares if two values are equal.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the values are equal, False otherwise.
    """
    return x == y


class NotEquals(GenericBinaryOperator):
  """Not equals (!=) operator."""

  def Operation(self, x, y):
    """Compares if two values are not equal.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the values are not equal, False otherwise.
    """
    return x != y


class Less(GenericBinaryOperator):
  """Less than (<) operator."""

  def Operation(self, x, y):
    """Compares if the first value is less than the second.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the first value is less than the second, False otherwise.
    """
    return x < y


class LessEqual(GenericBinaryOperator):
  """Less than or equals (<=) operator."""

  def Operation(self, x, y):
    """Compares if the first value is less than or equals the second.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the first value is than or equals the second, False
          otherwise.
    """
    return x <= y


class Greater(GenericBinaryOperator):
  """Greater than (>) operator."""

  def Operation(self, x, y):
    """Compares if the first value is greater than the second.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the first value is greater than the second, False otherwise.
    """
    return x > y


class GreaterEqual(GenericBinaryOperator):
  """Greater than or equals (>=) operator."""

  def Operation(self, x, y):
    """Compares if the first value is greater than or equals the second.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the first value is greater than or equals the second, False
          otherwise.
    """
    return x >= y


class Contains(GenericBinaryOperator):
  """Operator to determine if a value contains another value."""

  def Operation(self, x, y):
    """Compares if the second value is part of the first.

    Note that this method will do a case insensitive comparion if the first
    value is a string.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the second value is part of the first, False otherwise.
    """
    if isinstance(x, py2to3.STRING_TYPES):
      return y.lower() in x.lower()

    return y in x


# TODO: Change to an N-ary Operator?
class InSet(GenericBinaryOperator):
  """Operator to determine if a value is part of another value."""

  def Operation(self, x, y):
    """Compares if the first value is part of the second.

    Note that this method will do a case insensitive string comparion if
    the first value is a string.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the first value is part of the second, False otherwise.
    """
    if x in y:
      return True

    # x might be an iterable
    # first we need to skip strings or we'll do silly things
    # pylint: disable=consider-merging-isinstance
    if isinstance(x, py2to3.STRING_TYPES) or isinstance(x, bytes):
      return False

    try:
      for value in x:
        if value not in y:
          return False
      return True
    except TypeError:
      return False


# TODO: is GenericBinaryOperator the most suitable super class here?
# Would BinaryOperator be a better fit?
class Regexp(GenericBinaryOperator):
  """Operator to determine if a value matches a regular expression.

  Attributes:
    compiled_re (???): compiled regular expression.
  """

  def __init__(self, arguments=None, **kwargs):
    """Initializes a regular expression operator.

    This operator uses case senstive comparision.

    Args:
      arguments (Optional[object]): operands of the filter.

    Raises:
      ValueError: if the regular expression is malformed.
    """
    super(Regexp, self).__init__(arguments=arguments, **kwargs)

    # Note that right_operand is not necessarily a string.
    logging.debug('Compiled: {0!s}'.format(self.right_operand))

    try:
      expression = helpers.GetUnicodeString(self.right_operand)
      compiled_re = re.compile(expression, re.DOTALL)
    except re.error:
      raise ValueError('Regular expression "{0!s}" is malformed.'.format(
          self.right_operand))

    self.compiled_re = compiled_re

  def Operation(self, x, y):
    """Compares if the first value matches a regular expression.

    Args:
      x (object): first value.
      y (object): second value.

    Returns:
      bool: True if the first value matches the regular expression, False
          otherwise.
    """
    try:
      string_value = helpers.GetUnicodeString(x)
      if self.compiled_re.search(string_value):
        return True
    except TypeError:
      pass

    return False


class RegexpInsensitive(Regexp):
  """Operator to determine if a value matches a regular expression."""

  def __init__(self, arguments=None, **kwargs):
    """Initializes a regular expression operator.

    This operator uses case insenstive comparision.

    Args:
      arguments (Optional[object]): operands of the filter.

    Raises:
      ValueError: if the regular expression is malformed.
    """
    super(RegexpInsensitive, self).__init__(arguments=arguments, **kwargs)

    # Note that right_operand is not necessarily a string.
    logging.debug('Compiled: {0!s}'.format(self.right_operand))

    try:
      expression = helpers.GetUnicodeString(self.right_operand)
      compiled_re = re.compile(expression, re.I | re.DOTALL)
    except re.error:
      raise ValueError('Regular expression "{0!s}" is malformed.'.format(
          self.right_operand))

    self.compiled_re = compiled_re


class Context(Operator):
  """Restricts the child operators to a specific context within the object.

  Solves the context problem. The context problem is the following:
  Suppose you store a list of loaded DLLs within a process. Suppose that for
  each of these DLLs you store the number of imported functions and each of the
  imported functions name.

  Imagine that a malicious DLL is injected into processes and its indicators are
  that it only imports one function and that it is RegQueryValueEx. You would
  write your indicator like this:

  AndOperator(
    Equal("ImportedDLLs.ImpFunctions.Name", "RegQueryValueEx"),
    Equal("ImportedDLLs.NumImpFunctions", "1"))

  Now imagine you have these two processes on a given system.

  Process1
  * __ImportedDlls

    * __Name: "notevil.dll"

      * __ImpFunctions

        * __Name: "CreateFileA"

      * __NumImpFunctions: 1

    * __Name: "alsonotevil.dll"

      * __ImpFunctions

        * __Name: "RegQueryValueEx"
        * __Name: "CreateFileA"

      * __NumImpFunctions: 2

  Process2
  * __ImportedDlls

    * __Name: "evil.dll"

      * __ImpFunctions

        * __Name: "RegQueryValueEx"

      * __NumImpFunctions: 1

  Both Process1 and Process2 match your query, as each of the indicators are
  evaluated separately. While you wanted to express "find me processes that
  have a DLL that has both one imported function and ReqQueryValueEx is in the
  list of imported functions", your indicator actually means "find processes
  that have at least a DLL with 1 imported functions and at least one DLL that
  imports the ReqQueryValueEx function".

  To write such an indicator you need to specify a context of ImportedDLLs for
  these two clauses. Such that you convert your indicator to::

      Context(
        "ImportedDLLs",
        AndOperator(
          Equal("ImpFunctions.Name", "RegQueryValueEx"),
          Equal("NumImpFunctions", "1")))

  Context will execute the filter specified as the second parameter for each of
  the objects under "ImportedDLLs", thus applying the condition per DLL, not per
  object and returning the right result.
  """

  def __init__(self, arguments=None, **kwargs):
    """Initializes a context operator.

    Args:
      arguments (Optional[object]): operands of the filter.

    Raises:
      InvalidNumberOfOperands: if the number of operands provided is not
          supported.
    """
    if len(arguments) != 2:
      raise errors.InvalidNumberOfOperands((
          '{0:s} only supports 2 operands, provided were {1:d} '
          'operands.').format(self.__class__.__name__, len(arguments)))

    super(Context, self).__init__(arguments=arguments, **kwargs)
    self.context, self.condition = self.args

  def Matches(self, obj):
    """Determines if the object matches the filter.

    Args:
      obj (object): object to compare against the filter.

    Returns:
      bool: True if the object matches the filter, False otherwise.
    """
    for object_list in self.value_expander.Expand(obj, self.context):
      for sub_object in object_list:
        if self.condition.Matches(sub_object):
          return True
    return False
