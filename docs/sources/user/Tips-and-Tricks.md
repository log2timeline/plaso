# Tips and Tricks

This is a collection of few tips and tricks that can be used with **Plaso**

## Import the output of a third party tool into Plaso

If want to import the output of a third party tool into your Plaso timeline
export it to bodyfile format. The Plaso bodyfile parser can parse a bodyfile.

Note that the bodyfile format has numerous limitations see:
[ForensicsWiki: Bodyfile](https://forensics.wiki/bodyfile)

The Plaso bodyfile parser supports timestamps with a fraction of a second since
[Aug 25, 2020](https://github.com/log2timeline/plaso/commit/c81ef3aea9817646ea2846376ce9e2a83c7d5fe5).
