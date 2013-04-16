from django.db import models


class Feed(models.Model):
    title = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    description = models.CharField(blank=True, null=True, max_length=255)
    pubdate = models.DateTimeField(blank=True, null=True)
    imgtitle = models.CharField(blank=True, null=True, max_length=255)
    imghref = models.CharField(blank=True, null=True, max_length=255)
    imgwidth = models.CharField(blank=True, null=True, max_length=255)
    imgheight = models.CharField(blank=True, null=True, max_length=255)
    imglink = models.CharField(blank=True, null=True, max_length=255)

    lastpull = models.DateTimeField()
    etag = models.CharField(blank=True, null=True, max_length=255)
    lastmodified = models.CharField(blank=True, null=True, max_length=255)
    feedurl = models.CharField(max_length=255)


    def unread(self):
        return Item.objects \
                    .filter(feed__id=self.id) \
                    .filter(has_been_read=False) \
                    .count()


class Item(models.Model):
    feed = models.ForeignKey(Feed)

    title = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    description = models.CharField(blank=True, null=True, max_length=255)
    published = models.DateTimeField(blank=True, null=True)
    guid = models.CharField(blank=True, null=True, max_length=255)
    updated = models.DateTimeField(blank=True, null=True)

    has_been_read = models.BooleanField(default=False)
    starred = models.BooleanField(default=False)
    last_updated = models.DateTimeField()


    def disp_description(self):
        content = ItemContent.objects.filter(item__id=self.id)
        if self.description is not None \
                and content.count() > 0 \
                and self.description in content[0]:
            return ""
        return self.description if self.description is not None else ""

    def disp_content(self):
        content = ItemContent.objects.filter(item__id=self.id)
        output = "<p>"+"</p><p>".join([c.value for c in content])+"</p>"
        return output

    def disp_enclosures(self):
        enc = ItemEnclosure.objects.filter(item__id=self.id)
        if enc.count() <= 0:
            return ""
        output = "<ul>"
        for e in enc:
            if e.mimetype == "audio/mpeg" or e.mimetype == "audio/ogg" or e.mimetype == "audio/wav":
                output += "<li><a href='%s' target='_blank'>%s</a></li>" \
                                % (e.href, e.href)
            elif e.mimetype == "video/mp4" or e.mimetype == "video/webm" or e.mimetype == "video/ogg":
                output += "<li><a href='%s' target='_blank'>%s</a></li>" \
                                % (e.href, e.href)
            else:
                output += "<li><a href='%s' target='_blank'>%s</a></li>" \
                                % (e.href, e.href)
        output += "</ul>"
        return output


class ItemContent(models.Model):
    item = models.ForeignKey(Item)

    mimetype = models.CharField(blank=True, null=True, max_length=255)
    base = models.CharField(blank=True, null=True, max_length=255)
    language = models.CharField(blank=True, null=True, max_length=255)
    value = models.TextField()


class ItemEnclosure(models.Model):
    item = models.ForeignKey(Item)

    mimetype = models.CharField(blank=True, null=True, max_length=255)
    length = models.CharField(blank=True, null=True, max_length=255)
    href = models.CharField(max_length=255)

