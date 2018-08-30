# -*- coding: utf-8 -*-
"""The serializer object interfaces."""

from __future__ import unicode_literals

import abc


# Since abc does not seem to have an @abc.abstractclassmethod we're using
# @abc.abstractmethod instead and shutting up pylint about:
# E0213: Method should have "self" as first argument.
# pylint: disable=no-self-argument

class AttributeContainerSerializer(object):
  """Class that implements the attribute container serializer interface."""

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an attribute container from serialized form.

    Args:
      serialized (object): serialized form.

    Returns:
      AttributeContainer: attribute container.
    """

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def WriteSerialized(cls, attribute_container):
    """Writes an attribute container to serialized form.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      object: serialized form.
    """
