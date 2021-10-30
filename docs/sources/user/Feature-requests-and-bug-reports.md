# Feature requests and bug reports

## I would like to see support for a specific file format

If you like to see support for a specific file format here is how you can help.

1. Collect or create test data that can be publicly shared. Preferable test data that represents the necessary edge cases.
1. Document the data format, including the edge cases and common corruption cases. For example see [dtFormats](https://github.com/libyal/dtformats/tree/main/documentation).
1. Write a parser (or parser plugin) with tests and test data and submit as a PR to the project.

For more context on this approach see: [Testing digital forensic data processing tools](https://osdfir.blogspot.com/2020/09/testing-digital-forensic-data.html).

## GitHub issue tracker

Plaso feature requests and bug reports are tracked on the [GitHub issue tracker](https://github.com/log2timeline/plaso/issues).

### Labels

Feature requests in GitHub are labelled with "enhancement" for Plaso we
additionally label them with one or more of the following "focus area" labels:

* analysis; changes to analysis plug-ins
* core; changes to the core
* deployment; changes to deployment or development utility scripts
* parsers; changes to parsers and parser plug-ins
* testing; changes to improve testing
* UX; changes to user experience

### Milestones

After every release the Plaso maintainers will go over the open feature
requests and bug reports and determine which of the issues we are going to give
priority to work on and marked by a corresponding milestone.

Note that this is no guarantee that the feature will actually be implemented in
the next release. This is depend on other factors e.g. available time, show
stopper bugs, etc.

