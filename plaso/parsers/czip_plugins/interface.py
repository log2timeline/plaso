# -*- coding: utf-8 -*-
"""czip_interface contains basic interface for compound ZIP plugins within
Plaso.

CompoundZIPPlugin defines the attributes necessary for registration, discovery
and operation of plugins for czip files which will be used by CompoundZIPParser.
"""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins

class CompoundZIPPlugin(plugins.BasePlugin):
  """This is and "abstract" class from which plugins should be based."""

  # REQUIRED_ITEMS is a list of items required by a plugin.
  # This is used to understand whether a plugin is suited for a given compound
  # ZIP archive.
  # This is expected to be overridden by actual plugins.
  # Ex. frozenset(['[Content_Types].xml', '_rels/.rels', 'docProps/core.xml'])
  REQUIRED_ITEMS = frozenset(['any'])

  NAME = 'czip'

  def Process(self, parser_mediator, archive_proxy, **kwargs):
    """Determine if this is the correct plugin; if so proceed with processing.

    Process() checks if the current czip file being processed is a match for
    a plugin by comparing REQUIRED_ITEMS: if they match processing continues;
    else raise WrongCompoundZIPPlugin.

    This method is intended to be extended by actual plugins with archive
    specific logic.
    """

    if not set(archive_proxy.NameList()).issuperset(self.REQUIRED_ITEMS):
      raise errors.WrongCompoundZIPPlugin(self.NAME)

    # This will raise if unhandled keyword arguments are passed.
    super(CompoundZIPPlugin, self).Process(parser_mediator)

    logger.debug('Compound ZIP Plugin Used: {0:s}'.format(self.NAME))
