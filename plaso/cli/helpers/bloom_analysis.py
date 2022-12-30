# -*- coding: utf-8 -*-
"""The bloom analysis plugin CLI arguments helper."""

from plaso.analysis import bloom
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class BloomAnalysisArgumentsHelper(interface.ArgumentsHelper):
  """Bloom analysis plugin CLI arguments helper."""

  NAME = 'bloom'
  CATEGORY = 'analysis'
  DESCRIPTION = 'Argument helper for the hashlookup_bloom analysis plugin.'

  _DEFAULT_BLOOM_DATABASE_PATH = "hashlookup-full.bloom"
  _DEFAULT_HASH = 'sha1'
  _DEFAULT_LABEL = bloom.BloomAnalysisPlugin.DEFAULT_LABEL
  _SUPPORTED_HASHES = sorted(
      bloom.BloomAnalysisPlugin.SUPPORTED_HASHES)

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
        '--bloom-hash', '--bloom_hash',
        dest='bloom_hash', type=str, action='store',
        choices=cls._SUPPORTED_HASHES, default=cls._DEFAULT_HASH,
        metavar='HASH', help=(
            'Type of hash to use to query bloom file'
            '(hash are capitalized), the default is: '
            '{0:s}. Supported options: {1:s}'.format(
                cls._DEFAULT_HASH, ', '.join(cls._SUPPORTED_HASHES))))

    argument_group.add_argument(
        '--bloom-file', '--bloom_file',
        dest='bloom_file', type=str, action='store',
        default=cls._DEFAULT_BLOOM_DATABASE_PATH, metavar='PATH',
        help=(
            'Path to the bloom file, the '
            'default is: {0:s}').format(cls._DEFAULT_BLOOM_DATABASE_PATH))

    argument_group.add_argument(
        '--bloom-label', '--bloom_label',
        dest='bloom_label', type=str,
        action='store', default=cls._DEFAULT_LABEL, metavar='LABEL', help=(
            'Label to apply to events, the default is: {0:s}.').format(
                cls._DEFAULT_LABEL))

  @classmethod
  def ParseOptions(cls, options, analysis_plugin):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options object.
      analysis_plugin (BloomAnalysisPlugin): analysis plugin
        to configure.

    Raises:
      BadConfigObject: when the analysis plugin is the wrong type.
      BadConfigOption: when unable to load the bloom file.
    """
    if not isinstance(analysis_plugin, bloom.BloomAnalysisPlugin):
      raise errors.BadConfigObject(
          'Analysis plugin is not an instance of BloomAnalysisPlugin')

    label = cls._ParseStringOption(
        options, 'bloom_label', default_value=cls._DEFAULT_LABEL)
    analysis_plugin.SetLabel(label)

    lookup_hash = cls._ParseStringOption(
        options, 'bloom_hash', default_value=cls._DEFAULT_HASH)
    analysis_plugin.SetLookupHash(lookup_hash)

    bloom_file = cls._ParseStringOption(
        options, 'bloom_file',
        default_value=cls._DEFAULT_BLOOM_DATABASE_PATH)
    analysis_plugin.SetBloomDatabasePath(bloom_file)
    if not analysis_plugin.TestLoading():
      raise errors.BadConfigOption(
          'Unable to load bloom file {0:s}'.format(bloom_file))


manager.ArgumentHelperManager.RegisterHelper(
  BloomAnalysisArgumentsHelper)
