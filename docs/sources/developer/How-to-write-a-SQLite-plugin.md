# How to write a SQLite plugin

To write a SQLite plugin it is best to use [l2t_scaffolder](https://github.com/log2timeline/l2tscaffolder).
The scaffolder will ask you questions and guide you through setting up the
necessary files needed for the plugin.

## Locate/create test data

* Before writing the plugin you'll need to have a SQLite database file to test
  the plugin with. Either generate one, or have one that does not contain
  personal data (since it will get checked into the project).
* Start by listing out all the SQL commands you'll need to issue against the
  database beforehand. Try them out manually, see if they work and produce the
  data you are looking for.

## Creating all the files.

* Start by [installing the l2t_scaffolder tool](https://l2tscaffolder.readthedocs.io/en/latest/sources/user/Installation.html)
* Have your git repo for Plaso correctly setup (personal fork, see
  [here](Developers-Guide.md)).
* Then follow the [usage instructions](https://l2tscaffolder.readthedocs.io/en/latest/sources/user/Using-The-Tool.html).
  * Essentially run this command (you'll need to remember the path to the test
    file and the path to the plaso git repo before you start).

```
$ l2t_scaffolder.py plaso
```

* After answering all questions a new feature branch will be created in your
  Plaso repository with all the files needed for the plugin.

## Write minimal tests

* Write a test that loads your plugin and parses a file.
* It will fail initially, but running the test while you're developing your
  plugin gives you a quick way to see if your code is doing what you expect.

## Develop plugin

* There will be TODO's and missing code inside the newly generated files. Fill
  these in with your code.

## Expand tests

* Add additional tests that test your plugin and formatter

## Register classes

* Edit `plaso/parsers/sqlite_plugins/__init__.py` to correct alphabetical
  order of the imports.
* Edit `plaso/formatters/__init__.py` to correct alphabetical order of imports.

## Extend the timeliner and formatters configurations

Extend the timeliner and formatters configurations with the necessary
definitions for new event data types.

See: [How to write a parser or (parser) plugin](How-to-write-a-parser.md)

## Code review/submit

