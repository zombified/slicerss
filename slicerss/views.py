from django.conf import settings
from django.shortcuts import redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import opml

from slicerss.models import Feed, Item


def __allitems(feed_id):
    if feed_id == "all":
        return Item.objects \
                .order_by('-published', '-updated', '-last_updated')

    return Item.objects \
                .filter(feed__id=feed_id) \
                .order_by('-published', '-updated', '-last_updated')


def index(request):
    opmlfile = settings.OPML_PATH
    outline = opml.parse(opmlfile)

    opmlstruct = {'title':'default', 'subs':[], 'subfolders':[]}

    def handlesub(sub, subs, folders):
        if len(sub) > 0:
            subf = {'title':sub.title, 'subs':[], 'subfolders':[]}
            folders.append(subf)
            for s in sub:
                handlesub(s, subf['subs'], subf['subfolders'])
        else:
            feedobj = None
            try:
                feedobj = Feed.objects.get(feedurl=sub.xmlUrl)
            except:
                feedobj = None
            subs.append(feedobj)

    handlesub(outline, opmlstruct['subs'], opmlstruct['subfolders'])

    def sortfolders(ostruct):
        ostruct['subs'].sort(key=lambda x: x.title.lower())
        ostruct['subfolders'].sort(key=lambda x: x['title'].lower())
        for f in ostruct['subfolders']:
            sortfolders(f)

    sortfolders(opmlstruct)

    linearopml = []

    def linearizeopml(ostruct):
        linearopml.append(('folder', ostruct['title'], None))
        for subf in ostruct['subfolders']:
            linearizeopml(subf)
            linearopml.append(('outdent', '', None))
        for sub in ostruct['subs']:
            linearopml.append(('sub', sub.title, sub))

    struct_to_linearize = opmlstruct['subfolders'][0]
    for s in struct_to_linearize['subfolders']:
        linearizeopml(s)
        linearopml.append(('outdent', '', None))
    for s in struct_to_linearize['subs']:
        linearopml.append(('sub', s.title, s))

    context = {
        #'feeds': Feed.objects.order_by('title').all()
        'sublist': linearopml
    }
    return render(request, 'feeds/index.html', context)


def all_items(request):
    allitems = __allitems("all")
    paginator = Paginator(allitems, settings.ITEMS_PER_PAGE)

    page = request.GET.get('page', 1)
    if page:
        page = int(page)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage: # page out of range
        if paginator.num_pages >= 1:
            items = paginator.page(paginator.num_pages)
        else:
            items = []

    prevpage = page - 1 if page > 1 else None
    nextpage = page + 1 if (page + 1) <= paginator.num_pages else None
    lastpage = paginator.num_pages

    context = {
        'feed_id': 'all',
        'feed_title': 'Items From All Feeds',
        'page': page,
        'totalpages': paginator.num_pages,
        'prevpage': prevpage,
        'nextpage': nextpage,
        'lastpage': lastpage,
        'items': items
    }
    return render(request, 'feeds/items.html', context)


def feed(request, feed_id):
    allitems = __allitems(feed_id)
    feed = Feed.objects.get(id=feed_id)
    paginator = Paginator(allitems, settings.ITEMS_PER_PAGE)

    page = request.GET.get('page', 1)
    if page:
        page = int(page)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage: # page out of range
        if paginator.num_pages >= 1:
            items = paginator.page(paginator.num_pages)
        else:
            items = []

    prevpage = page - 1 if page > 1 else None
    nextpage = page + 1 if (page + 1) <= paginator.num_pages else None
    lastpage = paginator.num_pages

    context = {
        'feed_id': feed_id,
        'feed_title': feed.title,
        'feed_link': feed.link,
        'page': page,
        'totalpages': paginator.num_pages,
        'prevpage': prevpage,
        'nextpage': nextpage,
        'lastpage': lastpage,
        'items': items
    }
    return render(request, 'feeds/items.html', context)


def item(request, feed_id, item_id):
    item = Item.objects.get(id=item_id)
    item.has_been_read = True
    item.save()

    prev_id = None
    next_id = None
    allitems = __allitems(feed_id)
    for (index, val) in enumerate(allitems):
        if val.id == int(item_id):
            if index > 0:
                next_id = allitems[index-1].id
            if index < allitems.count()-1:
                prev_id = allitems[index+1].id
            break

    context = {
        'feed_id': feed_id,
        'item': item,
        'prev_id': prev_id,
        'next_id': next_id
    }
    return render(request, 'feeds/item.html', context)


# mark items unread in a variaty of ways
# =============================================================================

def mark_item_unread(request, feed_id, item_id):
    item = Item.objects.get(id=item_id)
    item.has_been_read = False
    item.save()

    return redirect('feed', feed_id=feed_id)

def mark_feed_read(request, feed_id):
    items = Item.objects.filter(feed__id=feed_id).filter(has_been_read=False)
    for i in items:
        i.has_been_read = True
        i.save()

    return redirect('feed', feed_id=feed_id)

def mark_feed_unread(request, feed_id):
    items = Item.objects.filter(feed__id=feed_id).filter(has_been_read=True)
    for i in items:
        i.has_been_read = False
        i.save()

    return redirect('feed', feed_id=feed_id)

def mark_all_read(reqeust):
    items = Item.objects.filter(has_been_read=False)
    for i in items:
        i.has_been_read = True
        i.save()

    return redirect('index')

def mark_all_unread(reqeust):
    items = Item.objects.filter(has_been_read=True)
    for i in items:
        i.has_been_read = False
        i.save()

    return redirect('index')
