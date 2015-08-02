# -*- coding: utf-8 -*-
"""The Windows Registry key path expander."""


class WinRegistryKeyPathExpander(object):
  """Class that implements the Windows Registry key path expander object."""

  def ExpandPath(self, key_path, pre_obj=None):
    """Expand a Registry key path based on attributes in pre calculated values.

       A Registry key path may contain paths that are attributes, based on
       calculations from either preprocessing or based on each individual
       Windows Registry file.

       An attribute is defined as anything within a curly bracket, eg.
       "\\System\\{my_attribute}\\Path\\Keyname". If the attribute my_attribute
       is defined in the preprocessing object its value will be replaced with
       the attribute name, e.g. "\\System\\MyValue\\Path\\Keyname".

       If the Registry path needs to have curly brackets in the path then
       they need to be escaped with another curly bracket, eg
       "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName". In this
       case the {{123-AF25-E523}} will be replaced with "{123-AF25-E523}".

    Args:
      key_path: The Registry key path before being expanded.
      pre_obj: Optional preprocess object that contains stored values from
               the image.

    Returns:
      A Registry key path that's expanded based on attribute values.

    Raises:
      KeyError: If an attribute name is in the key path not set in
                the preprocessing object a KeyError will be raised.
    """
    key_dict = {}

    if pre_obj:
      key_dict.update(pre_obj.__dict__.items())

    # TODO: make case insensitive.
    expanded_key_path = u''
    try:
      expanded_key_path = key_path.format(**key_dict)
    except KeyError as exception:
      raise KeyError(u'Unable to expand path with error: {0:s}'.format(
          exception))

    if not expanded_key_path:
      raise KeyError(u'Unable to expand path, no value returned.')

    return expanded_key_path
