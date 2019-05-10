# -*- coding: utf-8 -*-
"""The event filter expression parser expression classes."""

from __future__ import unicode_literals

import abc

from plaso.lib import errors
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

    elif len(self.args) == self.number_of_args:
      return True

    return False

  @abc.abstractmethod
  def Compile(self, filter_implementation):
    """Given a filter implementation, compile this expression.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of BaseFilterImplementation.

    Returns:
      object: filter object of the binary expression.
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

  def Compile(self, filter_implementation):
    """Compiles the binary expression into a filter object.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of BaseFilterImplementation.

    Returns:
      object: filter object of the binary expression.
    """
    operator = self.operator.lower()
    if operator in ('and', '&&'):
      method = 'AndFilter'
    elif operator in ('or', '||'):
      method = 'OrFilter'
    else:
      raise errors.ParseError(
          'Invalid binary operator {0:s}.'.format(operator))

    args = [x.Compile(filter_implementation) for x in self.args]
    return filter_implementation.FILTERS[method](arguments=args)


class IdentityExpression(Expression):
  """An event filter parser expression which always evaluates to True."""

  def Compile(self, filter_implementation):
    """Compiles the binary expression into a filter object.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of BaseFilterImplementation.

    Returns:
      object: filter object of the identity expression.
    """
    return filter_implementation.IdentityFilter()


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

  def Compile(self, filter_implementation):
    """Given a filter implementation, compile this expression.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of BaseFilterImplementation.

    Returns:
      object: filter object of the binary expression.
    """
    arguments = [self.attribute]
    for argument in self.args:
      filter_object = argument.Compile(filter_implementation)
      arguments.append(filter_object)

    expander = filter_implementation.FILTERS['ValueExpander']
    context_cls = filter_implementation.FILTERS['Context']
    return context_cls(arguments=arguments, value_expander=expander)

  def SetExpression(self, expression):
    """Sets the expression.

    Args:
      expression (Expression): expression.

    Raises:
      ParseError: if expression is not of type Expression.
    """
    if not isinstance(expression, Expression):
      raise errors.ParseError('Expected expression, got {0:s}.'.format(
          type(expression)))

    self.args = [expression]


class EventExpression(Expression):
  """Event expression.

  Attribute:
    bool_value (bool): boolean value that represents the result of
        the operation.
  """

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

  def Compile(self, filter_implementation):
    """Given a filter implementation, compile this expression.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of BaseFilterImplementation.

    Returns:
      object: filter object of the binary expression.

    Raises:
      ParseError: if the operator is missing or unknown.
    """
    self.attribute = self._SWAP_SOURCE.get(self.attribute, self.attribute)
    arguments = [self.attribute]

    if not self.operator:
      raise errors.ParseError('Missing operator.')

    op_str = self.operator.lower()
    operator = filter_implementation.OPS.get(op_str, None)

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
        if 'Less' in str(operator):
          helpers.TimeRangeCache.SetUpperTimestamp(argument.data)
        else:
          helpers.TimeRangeCache.SetLowerTimestamp(argument.data)

    arguments.extend(self.args)
    expander = filter_implementation.FILTERS['ValueExpander']
    ops = operator(arguments=arguments, value_expander=expander)
    if not self.bool_value:
      if hasattr(ops, 'FlipBool'):
        ops.FlipBool()

    return ops

  def FlipBool(self):
    """Negates the value of the bool_value attribute."""
    self.bool_value = not self.bool_value
