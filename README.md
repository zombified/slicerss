# SliceRSS

**2013/10/29** The project is in the process of being changed radically. It's
being transformed into a tool that pulls down and manages more static content.
The goal is to remove the need for a database to store content, and to have
better utilities for managing feeds from the command line. All of the points
about what this project tries to do is mostly going to stay the same -- just
the mechanism by which it does so is changing.


This is a really basic, *personal* RSS/Atom fetcher + reader. It is not
intended to have a lot of features, or have multiple users.

Here are a few things that this project tries to adhere to:

  * **Minimal Javascript** -- IE no jquery or other libraries. If a library
    would make a feature significantly easier to implement, the feature
    probably doesn't belong in this project
  * **Minimal CSS** -- rendering should be accomplished as fast as possible.
    There's no need for overly flashy GUI when all this project is intended to
    do is help you read text. Certainly a good looking project is intended,
    but not an overly flashy one.
  * **Minimal use of Async** -- It complicates things, and doesn't add much to
    the experience this project is intending.
  * **Mobile Friendly** -- The mobile reading experience should be a first
    class consideration in addition to desktop. This means either responsive
    design, or a design that works well regardless of viewing size.
  * **Ease of installation** -- Anyone should be able to install this project
    with a minimal of configuration and commands. However, this project isn't
    aimed at users that just want to run an install script and get using the
    app.



## Installation

  1. Clone `https://github.com/zombified/slicerss.git`
  2. run `python setup.py develop` to install all dependencies for the project
  3. edit `slice/settings.py`
     * set the `DATABASES` values -- if you'd like to use a sqlite3 database,
       just set the 'NAME' value under the 'default' database to an absolute
       path for the database
     * set the `OPML_PATH` value to an absolute path to your OPML file. There
       is an example OPML file in the OPML directory of the project.
  4. run `python manage.py syncdb` to create and configure the database


## Fetching RSS/Atom feeds

The command `python manage.py fetch` will download all feeds into the
configured database. This command could be setup in a cron job (or similar).
Be careful not to run it to often, as you don't want your IP blacklisted or
some such from a feed provider.


## Viewing Feeds

The command `python manage.py runserver` will start a server on localhost:8080.

To view the feeds, go to `http://localhost:8000/feeds`

