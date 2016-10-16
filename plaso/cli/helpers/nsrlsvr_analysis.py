# -*- coding: utf-8 -*-
"""The nsrlsvr analysis plugin CLI arguments helper."""

from plaso.analysis import nsrlsvr
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class NsrlsvrAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Nsrlsvr analysis plugin CLI arguments helper."""

  NAME = u'nsrlsvr_analysis'
  CATEGORY = u'analysis'
  DESCRIPTION = u'Argument helper for the nsrlsvr analysis plugin.'

  _DEFAULT_HASH = u'md5'
  _DEFAULT_HOST = u'localhost'
  _DEFAULT_PORT = 9120

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser): group
          to append arguments to.
    """
    argument_group.add_argument(
        u'--nsrlsvr-hash', u'--nsrlsvr_hash', dest=u'nsrlsvr_hash', type=str,
        action='store', choices=[u'md5', u'sha1'], default=cls._DEFAULT_HASH,
        metavar=u'HASH', help=(
            u'Type of hash to use to query the NSRL server, the default is: '
            u'{0:s}'.format(cls._DEFAULT_HASH)))

    argument_group.add_argument(
        u'--nsrlsvr-host', u'--nsrlsvr_host', dest=u'nsrlsvr_host', type=str,
        action='store', default=cls._DEFAULT_HOST, metavar=u'HOST',
        help=(
            u'Hostname of the NSRL server to query, the default is: '
            u'{0:s}'.format(cls._DEFAULT_HOST)))

    argument_group.add_argument(
        u'--nsrlsvr-port', u'--nsrlsvr_port', dest=u'nsrlvr_port', type=int,
        action='store', default=cls._DEFAULT_PORT, metavar=u'PORT', help=(
            u'Port of the NSRL server to query, the default is: {0:d}.'.format(
                cls._DEFAULT_PORT)))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options object.
      analysis_plugin (NsrlsvrAnalysisPlugin): analysis plugin to configure.

    Raises:
      BadConfigObject: when the analysis plugin is the wrong type.
      BadConfigOption: when unable to connect to nsrlsvr instance.
    """
    if not isinstance(analysis_plugin, nsrlsvr.NsrlsvrAnalysisPlugin):
      raise errors.BadConfigObject(
          u'Analysis plugin is not an instance of NsrlsvrAnalysisPlugin')

    lookup_hash = cls._ParseStringOption(
        options, u'nsrlsvr_hash', default_value=cls._DEFAULT_HASH)
    analysis_plugin.SetLookupHash(lookup_hash)

    host = cls._ParseStringOption(
        options, u'nsrlsvr_host', default_value=cls._DEFAULT_HOST)
    analysis_plugin.SetHost(host)

    port = cls._ParseStringOption(
        options, u'nsrlsvr_port', default_value=cls._DEFAULT_PORT)
    analysis_plugin.SetPort(port)

    if not analysis_plugin.TestConnection():
      raise errors.BadConfigOption(
          u'Unable to connect to nsrlsvr {0:s}:{1:d}'.format(host, port))


manager.ArgumentHelperManager.RegisterHelper(NsrlsvrAnalysisArgumentsHelper)
