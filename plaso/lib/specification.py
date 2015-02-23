# -*- coding: utf-8 -*-
"""The format specification classes."""


class Signature(object):
  """Class that defines a signature of a format specification.

  The signature consists of a byte string pattern, an optional
  offset relative to the start of the data, and a value to indicate
  if the pattern is bound to the offset.
  """
  def __init__(self, pattern, offset=None):
    """Initializes the signature.

    The signatures can be defined in 3 different "modes":
    * where offset >= 0, which represents that the signature is bound to the
      start of the data and only the relevant part is scanned;
    * where offset < 0, which represents that the signature is bound to the
      end of the data and only the relevant part is scanned;
    * offset == None, which represents that the signature is not offset bound
      and that all of the data is scanned.

    Args:
      pattern: a binary string containing the pattern of the signature.
               Wildcards or regular pattern (regexp) are not supported.
      offset: the offset of the signature or None by default.
    """
    super(Signature, self).__init__()
    self.identifier = None
    self.offset = offset
    self.pattern = pattern

  def SetIdentifier(self, identifier):
    """Sets the identifier of the signature in the specification store.

    Args:
      identifier: a string containing an unique signature identifier for
                  a specification store.
    """
    self.identifier = identifier


class FormatSpecification(object):
  """Class that contains a format specification."""

  def __init__(self, identifier):
    """Initializes the specification.

    Args:
      identifier: string containing a unique name for the format.
    """
    super(FormatSpecification, self).__init__()
    self.identifier = identifier
    self.signatures = []

  def AddNewSignature(self, pattern, offset=None):
    """Adds a signature.

    Args:
      pattern: a binary string containing the pattern of the signature.
      offset: the offset of the signature or None by default. None is used
              to indicate the signature has no offset. A positive offset
              is relative from the start of the data a negative offset
              is relative from the end of the data.
    """
    self.signatures.append(Signature(pattern, offset=offset))


class FormatSpecificationStore(object):
  """Class that serves as a store for specifications."""

  def __init__(self):
    """Initializes the specification store."""
    super(FormatSpecificationStore, self).__init__()
    self._format_specifications = {}
    # Maps signature identifiers to format specifications.
    self._signature_map = {}

  @property
  def specifications(self):
    """A specifications iterator object."""
    return self._format_specifications.itervalues()

  def AddNewSpecification(self, identifier):
    """Adds a new specification.

    Args:
      identifier: a string containing the format identifier,
                  which should be unique for the store.

    Returns:
      The format specification (instance of FormatSpecification).

    Raises:
      KeyError: if the store already contains a specification with
                the same identifier.
    """
    if identifier in self._format_specifications:
      raise KeyError(
          u'Format specification {0:s} is already defined in store.'.format(
              identifier))

    self._format_specifications[identifier] = FormatSpecification(identifier)

    return self._format_specifications[identifier]

  def AddSpecification(self, specification):
    """Adds a specification.

    Args:
      specification: the format specification (instance of FormatSpecification).

    Raises:
      KeyError: if the store already contains a specification with
                the same identifier.
    """
    if specification.identifier in self._format_specifications:
      raise KeyError(
          u'Format specification {0:s} is already defined in store.'.format(
              specification.identifier))

    self._format_specifications[specification.identifier] = specification

    for signature in specification.signatures:
      signature_index = len(self._signature_map)

      signature_identifier = u'{0:s}:{1:d}'.format(
          specification.identifier, signature_index)

      if signature_identifier in self._signature_map:
        raise KeyError(
            u'Signature {0:s} is already defined in map.'.format(
                signature_identifier))

      signature.SetIdentifier(signature_identifier)
      self._signature_map[signature_identifier] = specification

  def GetSpecificationBySignature(self, signature_identifier):
    """Retrieves a specification mapped to a signature identifier.

    Args:
      identifier: a string containing an unique signature identifier for
                  a specification store.

    Returns:
      A format specification (instance of FormatSpecification) or None
      if the signature identifier does not exist within the specification
      store.
    """
    return self._signature_map.get(signature_identifier, None)
