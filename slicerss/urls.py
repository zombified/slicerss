from django.conf.urls import patterns, url

from slicerss import views


urlpatterns = patterns('',
    # feeds
    url(r'^$', views.index, name='index'),

    # feeds/mark_all_read
    url(r'^mark_all_read$', views.mark_all_read, name='mark_all_read'),
    url(r'^all/mark_all_read$', views.mark_all_read, name='mark_all_read_allitemview'),
    url(r'^all/mark_all_unread$', views.mark_all_unread, name='mark_all_unread_allitemview'),

    # feeds/all/
    url(r'^all$', views.all_items, name='all_items'),

    # feeds/<feed id>/
    url(r'^(?P<feed_id>\d+)/$', views.feed, name='feed'),

    # feeds/<feed id>/mark_all_read
    # feeds/<feed id>/mark_all_unread
    url(r'^(?P<feed_id>\d+)/mark_all_read$', views.mark_feed_read, name='mark_feed_read'),
    url(r'^(?P<feed_id>\d+)/mark_all_unread$', views.mark_feed_unread, name='mark_feed_unread'),

    # feeds/<feed id>/item/<item id>/
    url(r'^(?P<feed_id>\d+)/item/(?P<item_id>\d+)/$', views.item, name='item'),

    # feeds/<feed id>/item/<item id>/mark_unread
    url(r'^(?P<feed_id>\d+)/item/(?P<item_id>\d+)/mark_unread$', views.mark_item_unread, name='mark_item_unread'),
)

