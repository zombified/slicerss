from datetime import timedelta
from dateutil import parser
from django.conf import settings
from django.core.management.base import BaseCommand #, CommandError
from django.utils.timezone import now
import feedparser
import opml

from slicerss.models import Feed, Item, ItemContent, ItemEnclosure


def handleitems(feed, resp, indentch, stdout):
    try:
        print >> stdout, "%s  >> Feed has %s items" % (indentch, len(resp.entries))
        itemsadded = 0
        itemsupdated = 0
        for entry in resp.entries:
            qry = Item.objects.filter(link=entry.link) \
                              .filter(feed__id=feed.id)
            qres = [a for a in qry]

            title = entry.title if hasattr(entry, 'title') else None
            link = entry.link if hasattr(entry, 'link') else None
            published = parser.parse(entry.published) if hasattr(entry, 'published') else None
            updated = parser.parse(entry.updated) if hasattr(entry, 'updated') else None
            guid = entry.id if hasattr(entry, 'id') else None
            if hasattr(entry, 'description'):
                desc = entry.description
            elif hasattr(entry, 'summary'):
                desc = entry.summary
            else:
                desc = None

            needsupdate = False
            if len(qres) > 0:
                item = qres[0]
                needsupdate = False

                # existing item has an updated date, and the new entry has
                #   an updated date -- then check the equality of the date
                if updated and item.updated:
                    needsupdate = updated.year == item.updated.year \
                                    and updated.month == item.updated.month \
                                    and updated.day == item.updated.day \
                                    and updated.hour == item.updated.hour \
                                    and updated.minute == item.updated.minute \
                                    and updated.second == item.updated.second

                # existing item has an updated date, but the the recent version
                #   of the item does not -- then the object needs to be updated
                elif not updated and item.updated:
                    needsupdate = True

                # otherwise, double check the published dates to make sure they
                #   are still the same
                else:
                    needsupdate = published.year == item.published.year \
                                    and published.month == item.published.month \
                                    and published.day == item.published.day \
                                    and published.hour == item.published.hour \
                                    and published.minute == item.published.minute \
                                    and published.second == item.published.second

                # update the item if needed
                if needsupdate:
                    itemsupdated += 1
                    item.title = title
                    item.link = link
                    item.description = desc
                    item.published = published
                    item.guid = guid
                    item.updated = updated
                    item.last_updated = now()
                    item.feed = Feed.objects.get(id=feed.id)
            else:
                itemsadded += 1
                needsupdate = True
                item = Item(
                    title=title,
                    link=link,
                    description=desc,
                    published=published,
                    guid=guid,
                    updated=updated,
                    last_updated=now(),
                    feed_id=feed.id)

            item.save()

            if needsupdate:
                # delete any existing content
                ItemContent.objects.filter(item__id=item.id).all().delete()

                # add content, if it exists
                if hasattr(entry, 'content'):
                    for content in entry.content:
                        newc = ItemContent(
                                mimetype=content.type if hasattr(content, 'type') else None,
                                base=content.base if hasattr(content, 'base') else None,
                                language=content.language if hasattr(content, 'language') else None,
                                value=content.value if hasattr(content, 'value') else None,
                                item=item)
                        newc.save()

                # delete any existing enclosures
                ItemEnclosure.objects.filter(item__id=item.id).all().delete()

                # add enclosures, if they exist
                if hasattr(entry, 'enclosures'):
                    for enclosure in entry.enclosures:
                        newe = ItemEnclosure(
                                mimetype=enclosure.type if hasattr(enclosure, 'type') else None,
                                length=enclosure.length if hasattr(enclosure, 'length') else None,
                                href=enclosure.href if hasattr(enclosure, 'href') else None,
                                item=item)
                        newe.save()

        print >> stdout, "%s  >> Added %s items, Updated %s items" \
                    % (indentch, itemsadded, itemsupdated)

    except Exception as e:
        print >> stdout, "%s  ** Exception in Item" % indentch
        print >> stdout, e


def handlefeed(sub, indentch, stdout):
    try:
        print >> stdout, "%srss url: %s" % (indentch, sub.xmlUrl)

        #
        # get a feed from the database that matches the URL. If there is a
        #   feed that has the url already, then we need to update that feed
        #   instead of create a new one. We also need to use the etag/modified
        #   tags to play nice with publishers that use those to save bandwidth.
        #

        qry = Feed.objects.filter(feedurl=sub.xmlUrl)
        qres = [a for a in qry]
        if len(qres) > 0:
            print >> stdout, "%s  >> feed found, using etag/lastmodified" % indentch
            resp = feedparser.parse(sub.xmlUrl,
                                    etag=qres[0].etag,
                                    modified=qres[0].lastmodified)
        else:
            resp = feedparser.parse(sub.xmlUrl)


        # proper not-modified return status
        if hasattr(resp, 'status') and resp.status == 304:
            # "force" an update of the feed or just skip it, this usually
            #   depends on the etag/lastmodified values stored from the last
            #   http request
            if qres[0].lastpull and qres[0].lastpull + timedelta(days=30) < now():
                print >> stdout, "%s  >> feed has not been updated for 30 days, " \
                      "ignoring 304 status" % indentch
            else:
                print >> stdout, "%s  >> feed has not been updated, skipping" % indentch
                return

        f = resp['feed']
        if not hasattr(f, 'title'):
            if resp.status in [301, 302]:
                print >> stdout, "%s  >> feed returned %s status with debug_message: %s" % (indentch, resp.status, resp.debug_message)
                print >> stdout, "%s  >> skipping." % indentch
                return

        #if 'gurneyjourney' in sub.xmlUrl:
        #    import pdb; pdb.set_trace()
        print >> stdout, "%s  >> %s" % (indentch, f.title)

        # get values for all the fields kept -- there's a large posibility that
        # any one of them could not exist, and there's a difference between
        # rss and atom
        title = f.title
        link = f.link
        if hasattr(f, 'description'):
            desc = f.description
        elif hasattr(f, 'subtitle'):
            desc = f.subtitle
        else:
            desc = None

        if hasattr(f, 'published'):
            pubdate = parser.parse(f.published)
        elif hasattr(f, 'updated'):
            pubdate = parser.parse(f.updated)
        else:
            pubdate = None

        if hasattr(f, 'image'):
            img = f.image
            imgtitle = img.title if hasattr(img, 'title') else None
            imghref = img.href if hasattr(img, 'href') else None
            imgwidth = img.width if hasattr(img, 'width') else None
            imgheight = img.height if hasattr(img, 'height') else None
            imglink = img.link if hasattr(img, 'link') else None
        else:
            imgtitle = None
            imghref = None
            imgwidth = None
            imgheight = None
            imglink = None

        # do the actual creation or update of the feed object
        feedobj = None
        if len(qres) < 1:
            feedobj = Feed(title=title,
                           link=link,
                           description=desc,
                           pubdate=pubdate,
                           imgtitle=imgtitle,
                           imghref=imghref,
                           imgwidth=imgwidth,
                           imgheight=imgheight,
                           imglink=imglink,
                           feedurl=sub.xmlUrl)
            print >> stdout, "%s  >> adding..." % indentch
        else:
            feedobj = qres[0]
            feedobj.title = title
            feedobj.link = link
            feedobj.description = desc
            feedobj.pubdate = pubdate
            feedobj.imgtitle = imgtitle
            feedobj.imghref = imghref
            feedobj.imgwidth = imgwidth
            feedobj.imgheight = imgheight
            feedobj.imglink = imglink
            print >> stdout, "%s  >> updating..." % indentch

        feedobj.etag = resp.etag if hasattr(resp, 'etag') else None
        feedobj.lastmodified = resp.lastmodified if hasattr(resp, 'lastmodified') else None
        feedobj.lastpull = now()

        feedobj.save()

        # add/update items as necessary
        handleitems(feedobj, resp, indentch, stdout)

        print >> stdout, "%s  >> done." % indentch

    except Exception as e:
        print >> stdout, "%s  ** Exception in Feed" % indentch
        print >> stdout, e

def handleopml(path, stdout):
    outline = opml.parse(path)

    def handlesub(sub, indent=0):
        indentch = "".join([' ' for a in range(0, indent)])
        if len(sub) < 1:
            handlefeed(sub, indentch, stdout)
        else:
            print >> stdout, "%sFOLDER: %s" % (indentch, sub.title)
            for s in sub:
                handlesub(s, indent+1)

    handlesub(outline)


class Command(BaseCommand):
    help = 'Retreives rss feeds, parses them, and stores them'

    def handle(self, *args, **options):
        opmlpath = settings.OPML_PATH
        handleopml(opmlpath, self.stdout)

