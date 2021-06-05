# -*- coding: utf-8 -*-
"""The event filter expression parser expression classes."""

import abc

from dfdatetime import interface as dfdatetime_interface

from plaso.filters import filters
from plaso.filters import logger
from plaso.filters import value_types
from plaso.lib import errors


class Expression(object):
  """An event filter parser expression.

  Attributes:
    attribute (str): attribute or None if not set.
    args (list[object]): arguments.
    number_of_args (int): expected number of arguments.
    operator (str): operator or None if not set.
  """

  # TODO: this currently needs to be a class attribute for objectfilter.
  # See if this can be changed to an instance attribute.
  attribute = None

  def __init__(self):
    """Initializes an event filter parser expression."""
    super(Expression, self).__init__()
    self.attribute = None
    self.args = []
    self.number_of_args = 1
    self.operator = None

  def AddArgument(self, argument):
    """Adds a new argument to this expression.

    Args:
      argument (object): argument to add.

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

  def __init__(self, operator=''):
    """Initializes an event filter parser binary expression.

    Args:
      operator (str): operator, such as "and" or "&&".
    """
    super(BinaryExpression, self).__init__()
    self.args = []
    self.operator = operator

  def __repr__(self):
    """Retrieves a string representation of the object for debugging."""
    if len(self.args) == 2:
      return '({0!s}) {1:s} {2!s}'.format(
          self.args[0], self.operator, self.args[1])
    return self.operator

  def AddOperands(self, lhs, rhs):
    """Adds an operand.

    Args:
      lhs (Expression): left hand side expression.
      rhs (Expression): right hand side expression.

    Raises:
      ParseError: if either left hand side or right hand side expression
          is not an instance of Expression.
    """
    # TODO: add information about what lhs and rhs are to these error messages.
    # https://github.com/log2timeline/plaso/pull/2498
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


class EventExpression(Expression):
  """Event expression."""

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

  _EVENT_FILTER_ALIAS = {
      'date': 'timestamp',
      'datetime': 'timestamp',
      'time': 'timestamp'}

  _DEPRECATED_EVENT_FILTER_ALIAS = frozenset([
      'description_long', 'description', 'description_short'])

  def __init__(self):
    """Initializes an event expression."""
    super(EventExpression, self).__init__()
    self._bool_value = True

  def __repr__(self):
    """Retrieves a string representation of the object for debugging."""
    return '{0:s} {1:s} {2!s}'.format(self.attribute, self.operator, self.args)

  def Compile(self):
    """Compiles the expression into a filter.

    Returns:
      Filter: filter object corresponding the expression.

    Raises:
      ParseError: if the operator is missing or unknown.
    """
    if self.attribute in self._DEPRECATED_EVENT_FILTER_ALIAS:
      logger.warning(
          'Event filter alias: "{0:s}" no longer supported'.format(
              self.attribute))

    if not self.operator:
      raise errors.ParseError('Missing operator.')

    lookup_key = self.operator.lower()
    operator = self._OPERATORS.get(lookup_key, None)
    if not operator:
      raise errors.ParseError('Unknown operator: {0:s}.'.format(self.operator))

    self.attribute = self._EVENT_FILTER_ALIAS.get(
        self.attribute, self.attribute)

    # Convert date and time values to (dfdatetime) date time objects.
    if self.attribute == 'timestamp':
      date_time_arguments = []
      for argument in self.args:
        if isinstance(argument, dfdatetime_interface.DateTimeValues):
          date_time = argument

        else:
          logger.warning(
              'Implicit event filter date and time conversion is deprecated '
              'use the DATETIME() value type indicator instead')

          try:
            date_time = value_types.DateTimeValueType(argument)
          except ValueError as exception:
            raise errors.ParseError(exception)

        date_time_arguments.append(date_time)

      self.args = date_time_arguments

    arguments = [self.attribute]
    arguments.extend(self.args)
    ops = operator(arguments=arguments)
    if not self._bool_value:
      if hasattr(ops, 'FlipBool'):
        ops.FlipBool()

    return ops

  def Negate(self):
    """Reverses the logic of (negates) the expression."""
    self._bool_value = not self._bool_value
