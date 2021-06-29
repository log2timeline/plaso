# -*- coding: utf-8 -*-
"""The format specification classes."""


class Signature(object):
  """The format specification signature.

  The signature consists of a byte string pattern, an optional
  offset relative to the start of the data, and a value to indicate
  if the pattern is bound to the offset.
  """
  def __init__(self, pattern, offset=None):
    """Initializes a format specification signature.

    The signatures can be defined in 3 different "modes":
    * where offset >= 0, which represents that the signature is bound to the
      start of the data and only the relevant part is scanned;
    * where offset < 0, which represents that the signature is bound to the
      end of the data and only the relevant part is scanned;
    * offset == None, which represents that the signature is not offset bound
      and that all of the data is scanned.

    Args:
      pattern (bytes): pattern of the signature. Wildcards or regular
          expressions (regexp) are not supported.
      offset (int): offset of the signature. None is used to indicate
          the signature has no offset. A positive offset is relative from
          the start of the data a negative offset is relative from the end
          of the data.
    """
    super(Signature, self).__init__()
    self.identifier = None
    self.offset = offset
    self.pattern = pattern

  def SetIdentifier(self, identifier):
    """Sets the identifier of the signature in the specification store.

    Args:
      identifier (str): unique signature identifier for a specification store.
    """
    self.identifier = identifier


class FormatSpecification(object):
  """The format specification."""

  def __init__(self, identifier, text_format=False):
    """Initializes a format specification.

    Args:
      identifier (str): unique name for the format.
      text_format (Optional[bool]): True if the format is a text format,
          False otherwise.
    """
    super(FormatSpecification, self).__init__()
    self._text_format = text_format
    self.identifier = identifier
    self.signatures = []

  def AddNewSignature(self, pattern, offset=None):
    """Adds a signature.

    Args:
      pattern (bytes): pattern of the signature.
      offset (int): offset of the signature. None is used to indicate
          the signature has no offset. A positive offset is relative from
          the start of the data a negative offset is relative from the end
          of the data.
    """
    self.signatures.append(Signature(pattern, offset=offset))

  def IsTextFormat(self):
    """Determines if the format is a text format.

    Returns:
      bool: True if the format is a text format, False otherwise.
    """
    return self._text_format


class FormatSpecificationStore(object):
  """The store for format specifications."""

  def __init__(self):
    """Initializes a specification store."""
    super(FormatSpecificationStore, self).__init__()
    self._format_specifications = {}
    # Maps signature identifiers to format specifications.
    self._signature_map = {}

  @property
  def specifications(self):
    """iterator: specifications iterator."""
    return iter(self._format_specifications.values())

  def AddNewSpecification(self, identifier):
    """Adds a new format specification.

    Args:
      identifier (str): format identifier, which should be unique for the store.

    Returns:
      FormatSpecification: format specification.

    Raises:
      KeyError: if the store already contains a specification with
                the same identifier.
    """
    if identifier in self._format_specifications:
      raise KeyError(
          'Format specification {0:s} is already defined in store.'.format(
              identifier))

    self._format_specifications[identifier] = FormatSpecification(identifier)

    return self._format_specifications[identifier]

  def AddSpecification(self, specification):
    """Adds a format specification.

    Args:
      specification (FormatSpecification): format specification.

    Raises:
      KeyError: if the store already contains a specification with
                the same identifier.
    """
    if specification.identifier in self._format_specifications:
      raise KeyError(
          'Format specification {0:s} is already defined in store.'.format(
              specification.identifier))

    self._format_specifications[specification.identifier] = specification

    for signature in specification.signatures:
      signature_index = len(self._signature_map)

      signature_identifier = '{0:s}:{1:d}'.format(
          specification.identifier, signature_index)

      if signature_identifier in self._signature_map:
        raise KeyError('Signature {0:s} is already defined in map.'.format(
            signature_identifier))

      signature.SetIdentifier(signature_identifier)
      self._signature_map[signature_identifier] = specification

  def GetSpecificationBySignature(self, signature_identifier):
    """Retrieves a specification mapped to a signature identifier.

    Args:
      signature_identifier (str): unique signature identifier for a
          specification store.

    Returns:
      FormatSpecification: format specification or None if the signature
          identifier does not exist within the specification store.
    """
    return self._signature_map.get(signature_identifier, None)
