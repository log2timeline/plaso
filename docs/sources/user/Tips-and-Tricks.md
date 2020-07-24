# Tips and Tricks

This is a collection of few tips and tricks that can be used with **Plaso**

## Output of a third party tools and Plaso

If want to import the output of a third party tool into your Plaso timeline
export it to bodyfile (or mactime) format. The Plaso mactime parser can parse
a bodyfile.

Also see: [Mactime](http://wiki.sleuthkit.org/index.php?title=Mactime)

## Split the output of psort

**psort** itself does not provide you the option of splitting the file into
chunks, however there are other ways to achieve that, such as using the
standard Unix tool ``split``, for example:

```
$ psort.py test.plaso | split -b 10m - split_output_
```

This will leave you with the following files:

+ split_output_aa
+ split_output_ab
+ split_output_ac
+ split_output_ad
+ ...

And so on... the size can be controlled by the ``-b``` parameter of the split
command.

