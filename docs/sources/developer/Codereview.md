# Code Review

All code submitted into the plaso project goes through code review. We use the GitHub codereview process, which while not perfect, is good enough for our purposes.

One helpful hint is while you have a code in code review monitor the development mailing list for large changes or new dependencies that may potentially affect your code. Such changes may include code re-factors that change plugin interface while you have a plugin in review. These should be rare but they do happen every now and then.

### Rationale

To keep the code base maintainable and readable all code is developed using a similar coding style. See the [style guide](Style-guide.md). This makes the code easier to maintain and understand.

The purpose of the code review is to ensure that:

 * at least two eyes looked over the code in hopes of finding potential bugs or errors (before they become bugs and errors). This also improves the overall code quality.
 * make sure the code adheres to the style guide (we do have a linter but that is not perfect).
 * review design decisions and if needed assist with making the code more optimal or error tolerant.

**The short version:**

*don't be intimidated.*

**The longer version:**

One language is not the same as another, you might are fluent in C or Perl that does not mean the same for Python. You might have just started programming while others have been doing this for years. Our challenge is having a code base that is accessible and sufficiently uniform to most of you.

Also don't be intimidated by rewrites/refactors, which often feels the code base is changing under your feet. We have to make sure the code base is maintainable and a necessary evil there is to regular reshape and clean up things to get new features in.

We continuously try to improve the code base, including making things and easier and quicker to write which sometimes means that the way you just learned might already superseded by another. We try to keep the documentation up to date but this will sometimes be after you ran into an issue.

First time contributors may come across the fact that the code review process actually takes quite a long time, with lots of back and forth comments. You may think that you are wasting the core developers time, but rest assured you are not. We look at this as an investment of building up good solid code contributors. We would like to make sure our contributors understand the code and the style guide and will make suggestions to the contributor to fix what we think needs improving. Despite spending potentially more time to begin with to get code submitted into the project we believe this investment in code review will result in better code submissions and increased proficiency of the contributor.

Therefore we would like to ask people to hang on, to get through the code review process and try to learn something while going through it. Rest assured, it will get easier next time and even easier the time after that, and before you know it you can contribute code to the project with little to no comments.

And if things are unclear, don't hesitate to ask. The developer mailing list is: log2timeline-dev@googlegroups.com

### Why not use reviewable.io?

We have looked at [reviewable.io](https://reviewable.io) and our current assessment is that it looks very nice but does not make for a very functional User Interface/Experience. It also convolutes the git commit history.

### Referencing github issues

If your changes relate to a specific [github issue](https://github.com/log2timeline/plaso/issues) add the issue number as following:

```
Added serializers profiler #120
```

Where the "#120" is a reference to issue number 120.

### Updating the code review

During the code review process you'll be asked to change few things, that is the reviewer will add comments. Please follow the following guideline during the code review process:

* Answer **ALL** comments made in the code review, even if it is only an ACK or "Done".
  * It is also necessary to publish the comments, otherwise the reviewer doesn't see the answers.
  * On the codereview site hit "m" for "Publish+Mail Comments" so that the review gets updated alongside the newly updated code.
* Make the necessary changes to the code, as suggested by the reviewer.

The update process continues until the reviewer thinks the code is good enough to be submitted into the project. 