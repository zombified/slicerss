import unittest

from slice import srfm


class srfm_test(unittest.TestCase):
    def setUp(self):
        self.opml_file = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
    <head>
        <title>RSS Subscriptions</title>
    </head>
    <body>
        <!-- Entry -->
        <outline text="Polygon" title="polygon" type="rss"
            xmlUrl="http://www.polygon.com/rss/index.xml" htmlUrl="http://www.polygon.com" />

        <!-- "Folder" With an Entry -->
        <outline title="podcasts" text="podcasts">
            <outline text="FLOSS Weekly" title="FLOSS Weekly" type="rss"
                xmlUrl="http://leoville.tv/podcasts/floss.xml" htmlUrl="http://twit.tv/floss"/>
        </outline>
    </body>
</opml>"""
        self.feed_list = [
            {'id':4,
             'tags':[],
             'title':'Polygon',
             'xmlUrl':'http://www.polygon.com/rss/index.xml',
             'htmlUrl':'http://www.polygon.com',},
            {'id':5,
             'tags':['podcasts'],
             'title':'FLOSS Weekly',
             'xmlUrl':'http://leoville.tv/podcasts/floss.xml',
             'htmlUrl':'http://twit.tv/floss',}
        ]

    def tearDown(self):
        pass

    def test_import_opml(self):
        feeds = srfm.opml_import(self.opml_file, 4, lambda feedurl, tags: False)

        self.assertTrue(len(feeds) == 2)
        self.assertTrue(feeds[0]['title'] == "Polygon")
        self.assertTrue(feeds[0]['xmlUrl'] == "http://www.polygon.com/rss/index.xml")
        self.assertTrue(feeds[0]['id'] == 4)
        self.assertTrue(feeds[1]['id'] == 5)
        self.assertTrue(len(feeds[0]['tags']) == 0)
        self.assertTrue(len(feeds[1]['tags']) == 1)
        self.assertTrue(feeds[1]['tags'][0] == "podcasts")

    def test_export_opml(self):
        opml_data = srfm.opml_export(self.feed_list)
        self.assertTrue(opml_data.strip() == '<?xml version="1.0" encoding="UTF-8"?>\n<opml version="1.0">\n    <head>\n        <title>RSS Subscriptions</title>\n    </head>\n    <body>\n    <outline text="podcasts" title="podcasts">\n<outline text="FLOSS Weekly" title="FLOSS Weekly" type="rss" xmlUrl="http://leoville.tv/podcasts/floss.xml" htmlUrl="http://twit.tv/floss" />\n</outline>\n    </body>\n</opml>')

    def test_list(self):
        # basic feed list
        feedlist = srfm.get_list(self.feed_list, False, [], False)
        self.assertTrue(len(feedlist) == 2)
        self.assertTrue(feedlist[0]['id'] == 4)

        # just tags
        feedlist = srfm.get_list(self.feed_list, True, [], False)
        self.assertTrue(len(feedlist) == 1)
        self.assertTrue('podcasts' in feedlist)

        # feed list filtered with certain tags
        feedlist = srfm.get_list(self.feed_list, False, ['podcasts'], False)
        self.assertTrue(len(feedlist) == 1)
        self.assertTrue(feedlist[0]['id'] == 5)

        # feed list sorted by name
        feedlist = srfm.get_list(self.feed_list, False, [], True)
        self.assertTrue(len(feedlist) == 2)
        self.assertTrue(feedlist[0]['id'] == 5)
        self.assertTrue(feedlist[1]['id'] == 4)

    def test_deltag(self):
        srfm.del_tag(self.feed_list, '5', ['podcasts'])
        self.assertTrue(self.feed_list[1]['id'] == 5)
        self.assertTrue(len(self.feed_list[1]['tags']) == 0)

    def test_addtag(self):
        srfm.add_tag(self.feed_list, '5', ['testtag'])
        self.assertTrue(self.feed_list[1]['id'] == 5)
        self.assertTrue(len(self.feed_list[1]['tags']) == 2)
        self.assertTrue('testtag' in self.feed_list[1]['tags'])

    def test_del(self):
        newfeedlist = srfm.delfeed(self.feed_list, '4')
        self.assertTrue(len(newfeedlist) == 1)
        self.assertTrue(newfeedlist[0]['id'] != 4)

    def test_add(self):
        srfm.addfeed(self.feed_list, 'http://reddit.com/.rss', 'Bebopbadu', ['reddit'])
        self.assertTrue(len(self.feed_list) == 3)
        self.assertTrue(self.feed_list[2]['id'] == 6)
        self.assertTrue(self.feed_list[2]['title'] == 'Bebopbadu')
        self.assertTrue(self.feed_list[2]['xmlUrl'] == 'http://reddit.com/.rss')
        self.assertTrue(self.feed_list[2]['htmlUrl'] == 'http://www.reddit.com/')
        self.assertTrue(len(self.feed_list[2]['tags']) == 1)
        self.assertTrue(self.feed_list[2]['tags'][0] == 'reddit')

    def test_guess(self):
        srfm.guess(self.feed_list, 'http://www.reddit.com/', 'Bebopbadu', ['reddit'])
        self.assertTrue(len(self.feed_list) == 3)
        self.assertTrue(self.feed_list[2]['id'] == 6)
        self.assertTrue(self.feed_list[2]['title'] == 'Bebopbadu')
        self.assertTrue(self.feed_list[2]['xmlUrl'] == 'http://www.reddit.com/.rss')
        self.assertTrue(self.feed_list[2]['htmlUrl'] == 'http://www.reddit.com/')
        self.assertTrue(len(self.feed_list[2]['tags']) == 1)
        self.assertTrue(self.feed_list[2]['tags'][0] == 'reddit')


if __name__ == '__main__':
    unittest.main()

