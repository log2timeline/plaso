# Developer Guide

* [Setting up and maintaining your development environment](Developers-Guide.html#setting-up-and-maintaining-your-development-environment)
* [Getting Started](Developers-Guide.html#getting-started)
* [Design](Developers-Guide.html#design)
* [Roadmap](Developers-Guide.html#roadmap)
* [Contributing Code](Developers-Guide.html#contributing-code)

## Setting up and maintaining your development environment

The first challenge you will encounter is setting up and maintaining your
development environment.

Start by setting up a development environment:

* [Development environment in a VirtualEnv](Developing-Virtualenv.md)
* [Development environment on Fedora](Developing-Fedora.md)
* [Development environment on MacOS](Developing-MacOS.md)
* [Development environment on Ubuntu](Developing-Ubuntu.md)
* [Development environment on Windows](Developing-Windows.md)

## Getting Started

Once you've set up your development environment we recommend start simple:

* [How to write a parser or (parser) plugin](How-to-write-a-parser.md)
* [How to write an analysis plugin](How-to-write-an-analysis-plugin.md)
* [How to write an output module](How-to-write-an-output-module.md)
* [How to write a tagging rule](How-to-write-a-tagging-rule.md)

## Design

Overview of the general architecture of Plaso:

* [Internals](Internals.md)
* [API documentation](https://plaso.readthedocs.io/en/latest/sources/api/plaso.html)

## Roadmap

A high level roadmap can be found [here](../user/Releases-and-roadmap.md).
Individual features are tracked as a github issue and labeled as "enhancement".
A list of features we'd already like to add can be found
[here](https://github.com/log2timeline/plaso/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement).

## Contributing Code

Want to add a parser to Plaso and you are ready to go? Start by checking
[here](https://github.com/log2timeline/plaso/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement)
if someone is already working on it. If you don't see anything there you can
just go ahead and [create an issue on the github site](https://github.com/log2timeline/plaso/issues)
and mark it as "enhancement". Assign the issue to yourself so that we can keep
track on who is working on what.

If you cannot program and still have a great idea for a feature please go ahead
and create an issue and leave it unassigned, note that the priority will be who
ever wants to work on it.

Before you start writing  code, please review the following:

* [Style guide](Style-guide.md). All code submitted to the project needs to
follow this style guide.
* [Code review](https://github.com/log2timeline/l2tdocs/blob/main/process/Code%20review%20process.md). All code that is submitted into the project is
 reviewed by at least one other person.
* [Adding a new dependency](https://github.com/log2timeline/l2tdocs/blob/main/process/Dependencies.md).
If your code requires adding a new dependency please check out these instructions.

### Before you submit your first code review

1. Join the development mailing list: [log2timeline-dev@googlegroups.com](https://groups.google.com/forum/#%21forum/log2timeline-dev)
and [Slack channel](https://github.com/open-source-dfir/slack), we recommend
using the same account as step 1
1. Install the required development tools like pylint and python-mock
1. Make sure to run all the tests in the Plaso codebase, and that they
successfully complete in your development environment
1. Make sure your development environment is set up correctly so that you can develop
 and test correctly.
1. Make sure your email address and name are correctly set in git. You can use
the following commands:
```
git config --global user.name "Full Name"
git config --global user.email name@example.com
git config --global push.default matching
```

Use `git config -l` to see your current configuration.

### Core features changes

Sometimes you need to make some change to the core of the Plaso codebase.
In those cases we ask that contributors first create a short design proposal
explaining the rationale behind the change. The design doc needs to contain:

1. A description of the problem you are facing
1. A list of the objectives of the change
1. A discussion of what's in scope and what's not
1. A description of your proposed the solution

The preferred way of creating these design docs is to use Google Docs and send
the link to the development mailing list so that it can be discussed further
**before** starting to implement the code.

### Tests

Tests are part of a maintainable code base. Code without sufficient test is very
likely to be broken by a large rewrite/refactor.

Plaso has specific guidelines for writing tests: [Style guide - tests](Style-guide.html#tests)
