"""SliceRSS Feed Manager

Usage:
    srfm.py guess <htmlurl> [--name=<name>] [TAG ...] [options]
    srfm.py add <feedurl> [--name=<name>] [TAG ...] [options]
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

from bs4 import BeautifulSoup
from docopt import docopt
import feedparser
import json
import opml
import os
import requests

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
        tags = sorted([a for a in set(tags)])
        for tag in tags:
            print tag
        return

    feedlist = sorted(feeds, key=lambda feed: feed['title']) if sortbyname else feeds
    filter = len(withtags) > 0
    filtertags = set(withtags)
    def print_feed(feed):
        print "%s%s: %s - %s [%s]" % (
                " " if feed['id'] < 10 else "",
                feed['id'], feed['title'], feed['xmlUrl'], ",".join(sorted(set(feed['tags']))))
    for feed in feedlist:
        if filter:
            if len(filtertags.intersection(set(feed['tags']))) > 0:
                print_feed(feed)
        else:
            print_feed(feed)

# feeds -- list of feed dicts to operate on
# feed -- the title or id of a feed to act on... all matches are modified
# tags -- list of strings representing tags to add to the selected feed
def add_tag(feeds, feed, tags):
    for f in feeds:
        if f['title'].strip().lower() == feed.strip().lower() or str(f['id']) == feed:
            f['tags'].extend(tags)
            f['tags'] = [a for a in set(f['tags'])]

# feeds -- list of feed dicts to operate on
# feed -- the title or id of a feed to act on... all matches are modified
# tags -- list of strings representing tags to add to the selected feed
def del_tag(feeds, feed, tags):
    for f in feeds:
        if f['title'].strip().lower() == feed.strip().lower() or str(f['id']) == feed:
            for t in tags:
                if t in f['tags']:
                    f['tags'].remove(t)

# feeds -- list of feed dicts to operate on
# feedurl -- the XML/RSS/Atom URL of the feed in question
# altname -- title to give to the feed instead of using the name provided by
#            the feed
# tags -- tags to associate with the feed
def addfeed(feeds, feedurl, altname, tags):
    # check to make sure this isn't already added
    for feed in feeds:
        if feed['xmlUrl'] == feedurl:
            print 'Feed already found.'
            return

    newfeed = dict(
        id=len(feeds),
        tags=[a for a in set(tags)] if tags else [],
        title=altname if altname else '',
        xmlUrl=feedurl,
        htmlUrl='')

    # grab the feed to get some metadata about it (specifically, the original
    # title and html url)
    try:
        resp = feedparser.parse(feedurl)
        if not hasattr(resp['feed'], 'title'):
            print 'Feed not found.'
            return
        if not altname:
            newfeed['title'] = resp['feed'].title
        newfeed['htmlUrl'] = resp['feed'].link
    except Exception as ex:
        print 'An error occured fetching your feed. %s' % str(ex)
        return

    feeds.append(newfeed)
    print "Added '%s' (id: %s)" % (newfeed['title'], newfeed['id'])

# feeds -- list of feed dicts to operate on
# feed -- the title or id of feeds to remove (all matching feeds are removed)
def delfeed(feeds, feed):
    return [a for a in feeds \
                if a['title'].strip().lower() != feed.strip().lower() \
                   and str(a['id']) != feed.strip().lower()]

# feeds -- list of feed dicts to operate on
# htmlurl -- url to use to try and guess an RSS feed url from
def guess(feeds, htmlurl, altname, tags):
    r = requests.get(htmlurl)
    if r.status_code != requests.codes.ok:
        print "Can't get url, got %s status code." % r.status_code
        return
    soup = BeautifulSoup(r.text)
    found_xmlurl = None
    try:
        links = soup.html.head.find_all('link')
        rsstypes = ('application/rss+xml',
                    'application/rdf+xml',
                    'application/atom+xml',
                    'application/xml',
                    'text/xml')
        for link in links:
            # does the html document have a link element identified as a RSS feed?
            if 'type' in link.attrs and link['type'].strip().lower() in rsstypes:
                found_xmlurl = link['href']

            # does the html document have a link element w/ a href ending w/ rss
            # or xml, possibly indicating an RSS feed?
            elif link['href'].strip().lower().endswith('rss') \
                    or link['href'].strip().lower().endswith('xml'):
                found_xmlurl = link['href']

    except AttributeError:
        found_xmlurl = None

    if not found_xmlurl:
        print "No RSS URL's found"
        return

    try:
        resp = feedparser.parse(found_xmlurl)
        if not hasattr(resp['feed'], 'title'):
            print "RSS feed guessed (%s), but doesn't seem to be valid." % found_xmlurl
            return
        newfeed = dict(
            id=len(feeds),
            tags=[a for a in set(tags)] if tags else [],
            title=altname if altname else resp['feed'].title,
            xmlUrl=found_xmlurl,
            htmlUrl=htmlurl)
        feeds.append(newfeed)
        print "Added '%s' (id: %s)" % (newfeed['title'], newfeed['id'])
    except Exception as ex:
        print 'An error occured fetching your feed. %s' % str(ex)
        return


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

    write_out_json = True
    if arguments['import']:
        newfeeds = opml_import(arguments['<opml_file_path>'], len(feeds), isdup)
        feeds.extend(newfeeds)
    elif arguments['export']:
        opml_export(arguments['<opml_file_path>'], feeds)
        write_out_json = False
    elif arguments['list']:
        show_list(feeds, arguments['--tags'], arguments['--with'], arguments['--sort-by-name'])
        write_out_json = False
    elif arguments['addtag']:
        add_tag(feeds, arguments['<feed>'], arguments['TAG'])
    elif arguments['deltag']:
        del_tag(feeds, arguments['<feed>'], arguments['TAG'])
    elif arguments['add']:
        addfeed(feeds, arguments['<feedurl>'], arguments['--name'], arguments['TAG'])
    elif arguments['del']:
        before = len(feeds)
        feeds = delfeed(feeds, arguments['<feed>'])
        after = len(feeds)
        delta = before - after
        if delta > 0:
            print "(%s) Deleted" % delta
        else:
            print "Nothing deleted"
    elif arguments['guess']:
        guess(feeds, arguments['<htmlurl>'], arguments['--name'], arguments['TAG'])

    if write_out_json:
        if arguments['--file'] is not None:
            with open(arguments['--file'], 'w') as fout:
                json.dump(feeds, fout)
        else:
            print "Changes not saved (no --file specified)"

