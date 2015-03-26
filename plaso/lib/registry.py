# -*- coding: utf-8 -*-
"""This file contains a class registration system for plugins."""

import abc


class MetaclassRegistry(abc.ABCMeta):
  """Automatic Plugin Registration through metaclasses."""

  def __init__(cls, name, bases, env_dict):
    """Initialize a metaclass.

    Args:
      name: The interface class name.
      bases: A tuple of base names.
      env_dict: The namespace of the object.

    Raises:
      KeyError: If a classes given name is already registered, to make sure
                no two classes that inherit from the same interface can have
                the same name attribute.
    """
    abc.ABCMeta.__init__(cls, name, bases, env_dict)

    # Register the name of the immediate parent class.
    if bases:
      cls.parent_class_name = getattr(bases[0], 'NAME', bases[0])
      cls.parent_class = bases[0]

    # Attach the classes dict to the baseclass and have all derived classes
    # use the same one:
    for base in bases:
      try:
        cls.classes = base.classes
        cls.plugin_feature = base.plugin_feature
        cls.top_level_class = base.top_level_class
        break
      except AttributeError:
        cls.classes = {}
        cls.plugin_feature = cls.__name__
        # Keep a reference to the top level class
        cls.top_level_class = cls

    # The following should not be registered as they are abstract. Classes
    # are abstract if the have the __abstract attribute (note this is not
    # inheritable so each abstract class must be explicitely marked).
    abstract_attribute = '_{0:s}__abstract'.format(name)
    if getattr(cls, abstract_attribute, None):
      return

    if not cls.__name__.startswith('Abstract'):
      cls_name = getattr(cls, 'NAME', cls.__name__)

      if cls_name in cls.classes:
        raise KeyError(u'Class: {0:s} already registered. [{1:s}]'.format(
            cls_name, repr(cls)))

      cls.classes[cls_name] = cls

      try:
        if cls.top_level_class.include_plugins_as_attributes:
          setattr(cls.top_level_class, cls.__name__, cls)
      except AttributeError:
        pass
