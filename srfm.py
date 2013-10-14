"""SliceRSS Feed Manager

Usage:
    srfm.py guess <htmlurl> [options]
    srfm.py add <feedurl> [--name=<name>] [options]
    srfm.py del <feed> [options]
    srfm.py addtag <feed> [TAG ...] [options]
    srfm.py deltag <feed> [TAG ...] [options]
    srfm.py list ([--tags]|[--with=TAG]...) [--sort-by-name] [options]
    srfm.py export <opml_file_path> [options]
    srfm.py import <opml_file_path> [options]

Options:
    -h --help            Show this info
    --version            Show version info
    -f FILE --file=FILE  SliceRSS feed file to manage [default: ~/.slicerss/opml]

"""
__version__ = '0.1'


# TODO:
#   - deltag, addtag
#   - add, del
#   - guess
#

from docopt import docopt
import json
import opml
import os

#
# the storage format:
#
#   [
#       {
#           'id':idnumber,
#           'tags':['tag', ...],
#           'title':'title',
#           'xmlUrl':'http://url/to/rss.xml',
#           'htmlUrl':'http://url/to/source',
#           'etag':'etag value',
#           'lastmodified':'lastmodified value',
#       },
#       ...
#   ]
#
# the 'idnumber' gets auto-assigned and is used for quick reference when
# doing operations on the feed itself. IE 'srfm.py del 1' would delete the
# feed with the id of '1'
#

# path -- path to JSON formatted file containing a list of feeds
def loadfeeds(path):
    if not os.path.isfile(path):
        return []
    with open(path, "r") as fin:
        feeds = json.load(fin)
        return feeds

# path -- path to OPML file to import
# idoffset -- ID to start at when creating id's for feeds
# isdup -- function that will return True or False if the given feed xmlUrl
#           value is already found in our 'database', and it also takes a
#           list of tags that should be added to the feed entery should it
#           exist already
def opml_import(path, idoffset, isdup):
    if not os.path.isfile(path):
        return []

    outline = opml.parse(path)
    feeds = []

    def handlefeed(sub, tags):
        if isdup(sub.xmlUrl.strip().lower(), tags):
            return []
        feeddata = dict(
            id=len(feeds)+idoffset,
            tags=[a for a in set(tags)],
            title=sub.text,
            xmlUrl=sub.xmlUrl,
            htmlUrl=sub.htmlUrl if sub.htmlUrl else '')
        feeds.append(feeddata)
    def handlesub(sub, tags):
        if len(sub) < 1:  # just a feed
            handlefeed(sub, tags)
        else:  # a folder of feeds
            newtags = []
            newtags.extend(tags)
            try:
                newtags.append(sub.text)
            except:
                pass
            for s in sub:
                handlesub(s, newtags)

    handlesub(outline, [])
    return feeds

# path -- path to OPML file you'd like to write to
# feeds -- list of feed dicts
def opml_export(path, feeds):
    template = """
<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
    <head>
        <title>RSS Subscriptions</title>
    </head>
    <body>
    %s
    </body>
</opml>"""

    # get a set of all unique tags, then, for each tag, output entries with
    # that tag in a single-level OPML outline
    tags = set()
    for feed in feeds:
        tags.update(set(feed['tags']))
    outlines = []
    for tag in tags:
        outlines.append('<outline text="%s" title="%s">'%(tag,tag))
        for feed in feeds:
            if tag in feed['tags']:
                outlines.append('<outline text="%s" title="%s" type="rss" xmlUrl="%s" htmlUrl="%s" />'
                                % (feed['title'], feed['title'], feed['xmlUrl'], feed['htmlUrl']))
        outlines.append('</outline>')
    entries = "\n".join(outlines)

    with open(path, "w") as fout:
        fout.write((template%entries).encode('utf8'))

# feeds -- list of feed dicts to operate on
# only_tags -- if true, a list of all tags used are shown
# withtags -- if only_tags is false, this is a list of tags used to filter the feeds by
def show_list(feeds, only_tags, withtags, sortbyname):
    if only_tags:
        tags = []
        for feed in feeds:
            tags.extend(feed['tags'])
        tags = [a for a in set(tags)]
        for tag in tags:
            print tag
        return

    feedlist = sorted(feeds, key=lambda feed: feed['title']) if sortbyname else feeds
    filter = len(withtags) > 0
    filtertags = set(withtags)
    def print_feed(feed):
        print "%s%s: %s - %s [%s]" % (
                " " if feed['id'] < 10 else "",
                feed['id'], feed['title'], feed['xmlUrl'], ",".join(set(feed['tags'])))
    for feed in feedlist:
        if filter:
            if len(filtertags.intersection(set(feed['tags']))) > 0:
                print_feed(feed)
        else:
            print_feed(feed)

if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)

    feeds = loadfeeds(arguments['--file'])

    def isdup(xmlUrl, tags):
        for feed in feeds:
            if feed['xmlUrl'].strip().lower() == xmlUrl:
                feed['tags'].extend(tags)
                feed['tags'] = [a for a in set(feed['tags'])]
                return True
        return False

    write_out_json = False
    if arguments['import']:
        newfeeds = opml_import(arguments['<opml_file_path>'], len(feeds), isdup)
        feeds.extend(newfeeds)
        write_out_json = True
    elif arguments['export']:
        opml_export(arguments['<opml_file_path>'], feeds)
    elif arguments['list']:
        show_list(feeds, arguments['--tags'], arguments['--with'], arguments['--sort-by-name'])

    if write_out_json:
        with open(arguments['--file'], 'w') as fout:
            json.dump(feeds, fout)

