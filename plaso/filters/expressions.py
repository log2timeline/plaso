# -*- coding: utf-8 -*-
"""The event filter expression parser expression classes."""

from __future__ import unicode_literals

import abc

from plaso.lib import errors
from plaso.filters import filters
from plaso.filters import helpers


class Expression(object):
  """An event filter parser expression.

  Attributes:
    attribute (str): attribute or None if not set.
    args (list[str]): arguments.
    number_of_args (int): expected number of arguments.
    operator (str): operator or None if not set.
  """

  # TODO: this currently needs to be a class attribute for objectfilter.
  # See if this can be changed to an instance attribute.
  attribute = None

  def __init__(self):
    """Initializes an event filter parser expression."""
    super(Expression, self).__init__()
    self.args = []
    self.number_of_args = 1
    self.operator = None

  def AddArg(self, argument):
    """Adds a new argument to this expression.

    Args:
       argument (str): argument to add.

    Returns:
      bool: True if the argument is the last argument, False otherwise.

    Raises:
      ParseError: If there are too many arguments.
    """
    self.args.append(argument)
    if len(self.args) > self.number_of_args:
      raise errors.ParseError('Too many arguments for this expression.')

    if len(self.args) == self.number_of_args:
      return True

    return False

  @abc.abstractmethod
  def Compile(self):
    """Compiles the expression into a filter.

    Returns:
      Filter: filter object corresponding the expression.
    """

  def SetAttribute(self, attribute):
    """Sets the attribute.

    Args:
      attribute (str): attribute, or None if not set.
    """
    self.attribute = attribute

  def SetOperator(self, operator):
    """Set the operator.

    Args:
      operator (str): operator, such as "and" or "&&", or None if not set.
    """
    self.operator = operator


class BinaryExpression(Expression):
  """An event filter parser expression which takes two other expressions."""

  def __init__(self, operator='', part=None):
    """Initializes an event filter parser binary expression.

    Args:
      operator (str): operator, such as "and" or "&&".
      part (str): expression part.
    """
    super(BinaryExpression, self).__init__()
    self.args = []
    self.operator = operator

    if part:
      self.args.append(part)

  def AddOperands(self, lhs, rhs):
    """Adds an operand.

    Args:
      lhs (Expression): left hand side expression.
      rhs (Expression): right hand side expression.

    Raises:
      ParseError: if either left hand side or right hand side expression
          is not an instance of Expression.
    """
    if not isinstance(lhs, Expression):
      raise errors.ParseError('Left hand side is not an expression')

    if not isinstance(rhs, Expression):
      raise errors.ParseError('Right hand side is not an expression')

    self.args = [lhs, rhs]

  def Compile(self):
    """Compiles the expression into a filter.

    Returns:
      Filter: filter object corresponding the expression.

    Raises:
      ParseError: if the operator is not supported.
    """
    operator = self.operator.lower()
    if operator in ('and', '&&'):
      filter_class = filters.AndFilter
    elif operator in ('or', '||'):
      filter_class = filters.OrFilter
    else:
      raise errors.ParseError('Unusupported operator: {0:s}.'.format(operator))

    args = [argument.Compile() for argument in self.args]
    return filter_class(arguments=args)


class IdentityExpression(Expression):
  """An event filter parser expression which always evaluates to True."""

  def Compile(self):
    """Compiles the expression into a filter.

    Returns:
      IdentityFilter: filter object which always evaluates to True.
    """
    return filters.IdentityFilter()


class ContextExpression(Expression):
  """Context operator expression."""

  # TODO: remove part, which is never used.
  def __init__(self, attribute='', part=None):
    """Initializes a context expression.

    Args:
      attribute (str): attribute.
      part (str): expression part.
    """
    super(ContextExpression, self).__init__()
    self.attribute = attribute
    self.args = []
    if part:
      self.args.append(part)

  def Compile(self):
    """Compiles the expression into a filter.

    Returns:
      ContextOperator: context operator filter.
    """
    arguments = [self.attribute]
    for argument in self.args:
      filter_object = argument.Compile()
      arguments.append(filter_object)

    return filters.ContextOperator(arguments=arguments)

  def SetExpression(self, expression):
    """Sets the expression.

    Args:
      expression (Expression): expression.

    Raises:
      ParseError: if expression is not of type Expression.
    """
    if not isinstance(expression, Expression):
      raise errors.ParseError('Expected expression, got {0!s}.'.format(
          type(expression)))

    self.args = [expression]


class EventExpression(Expression):
  """Event expression.

  Attribute:
    bool_value (bool): boolean value that represents the result of
        the operation.
  """

  # TODO: add an IsOperator
  _OPERATORS = {
      '==': filters.EqualsOperator,
      '>': filters.GreaterThanOperator,
      '>=': filters.GreaterEqualOperator,
      '<': filters.LessThanOperator,
      '<=': filters.LessEqualOperator,
      '!=': filters.NotEqualsOperator,
      'contains': filters.Contains,
      'equals': filters.EqualsOperator,
      'inset': filters.InSet,
      'iregexp': filters.RegexpInsensitive,
      'is': filters.EqualsOperator,
      'regexp': filters.Regexp}

  # A simple dictionary used to swap attributes so other names can be used
  # to reference some core attributes (implementation specific).
  _SWAP_SOURCE = {
      'date': 'timestamp',
      'datetime': 'timestamp',
      'description_long': 'message',
      'description': 'message',
      'description_short': 'message_short',
      'time': 'timestamp'}

  def __init__(self):
    """Initializes an event expression."""
    super(EventExpression, self).__init__()
    self.bool_value = True

  def Compile(self):
    """Compiles the expression into a filter.

    Returns:
      Filter: filter object corresponding the expression.

    Raises:
      ParseError: if the operator is missing or unknown.
    """
    self.attribute = self._SWAP_SOURCE.get(self.attribute, self.attribute)
    arguments = [self.attribute]

    if not self.operator:
      raise errors.ParseError('Missing operator.')

    lookup_key = self.operator.lower()
    operator = self._OPERATORS.get(lookup_key, None)
    if not operator:
      raise errors.ParseError('Unknown operator: {0:s}.'.format(self.operator))

    # Plaso specific implementation - if we are comparing a timestamp
    # to a value, we use our specific implementation that compares
    # timestamps in a "human readable" format.
    if self.attribute == 'timestamp':
      args = []
      for argument in self.args:
        date_compare_object = helpers.DateCompareObject(argument)
        args.append(date_compare_object)
      self.args = args

    for argument in self.args:
      if isinstance(argument, helpers.DateCompareObject):
        if isinstance(operator, (
            filters.LessEqualOperator, filters.LessThanOperator)):
          helpers.TimeRangeCache.SetUpperTimestamp(argument.data)
        else:
          helpers.TimeRangeCache.SetLowerTimestamp(argument.data)

    arguments.extend(self.args)
    ops = operator(arguments=arguments)
    if not self.bool_value:
      if hasattr(ops, 'FlipBool'):
        ops.FlipBool()

    return ops

  def FlipBool(self):
    """Negates the value of the bool_value attribute."""
    self.bool_value = not self.bool_value
