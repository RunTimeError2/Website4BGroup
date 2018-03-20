"""
Definition of urls for FC15Website.
"""
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import staticfiles

from datetime import datetime
from django.conf.urls import url, handler404, handler500
import django.contrib.auth.views

from django.conf.urls import include
from django.contrib import admin
import FC15.views
admin.autodiscover()

handler404 = 'FC15.views.page_not_found'
handler500 = 'FC15.views.page_error'

# All urls available
urlpatterns = [
    # Basic pages
    url(r'^$', FC15.views.home, name = 'home'),
    url(r'^home/$', FC15.views.home, name = 'home'),
    url(r'^about_rule/$', FC15.views.about_rule, name = 'about_rule'),
    url(r'^about_story/$', FC15.views.about_story, name = 'about_story'),
    url(r'^about_sponsor/$', FC15.views.about_sponsor, name = 'about_sponsor'),
    url(r'^document/$', FC15.views.document, name = 'document'),
    url(r'^index/$', FC15.views.index, name = 'index'),
    url(r'^login/$', FC15.views.login, name = 'login'),
    url(r'^logout/$', FC15.views.logout, name = 'logout'),
    url(r'^regist/$', FC15.views.regist, name = 'regist'),
    url(r'^upload/$', FC15.views.upload, name = 'upload'),
    url(r'^postblog/$', FC15.views.postblog, name = 'postblog'),
    url(r'^viewblogs/$', FC15.views.viewblogs, name = 'viewblogs'),
    url(r'^team/$', FC15.views.team, name = 'team'),
    url(r'^createteam/$', FC15.views.createteam, name = 'createteam'),
    url(r'^resetrequest/$', FC15.views.resetrequest, name = 'resetrequest'),
    url(r'^change/$', FC15.views.change, name = 'change'),
    url(r'^teamdetail/$', FC15.views.teamdetail, name = 'teamdetail'),
    url(r'^teamrequest/$', FC15.views.jointeamrequest, name = 'jointeamrequest'),
    url(r'^quitteam/$', FC15.views.quitteam, name = 'quitteam'),
    url(r'^dismissteam/$', FC15.views.dismissteam, name = 'dismissteam'),
    url(r'^playgame/$', FC15.views.playgame, name = 'playgame'),
    url(r'^unfinished/$', FC15.views.unfinished, name = 'unfinished'),
    url(r'^ui/$', FC15.views.ui, name = 'ui'),
    url(r'^activateagain/$', FC15.views.activateagain, name = 'activateagain'),

    # New page, and the link and name can be changed
    url(r'^newpage/$', FC15.views.newpage, name = 'newpage'),
 
    # Download files
    url(r'^sdkdownload/$', FC15.views.sdkdownload, name = 'sdkdownload'),
    url(r'^download_manual/$', FC15.views.download_manual, name = 'download_manual'),
    url(r'^download_0318ppt/$', FC15.views.download_0318ppt, name = 'download_0318ppt'),
    #url(r'^execode/$', FC15.views.exe_code, name = 'exe_code'),

    # Error pages
    url(r'^404/$', FC15.views.page_not_found, name = 'pagenotfount'),
    url(r'^500/$', FC15.views.page_error, name = 'pageerror'),

    # Pages releated to pk(specific items in the database)
    url(r'^blogdetail/(?P<pk>[0-9]+)/$', FC15.views.blogdetail, name = 'blogdetail'),
    url(r'^blogedit/(?P<pk>[0-9]+)/$', FC15.views.blogedit, name = 'blogedit'),
    url(r'^blogdelete/(?P<pk>[0-9]+)/$', FC15.views.blogdelete, name = 'blogdelete'),
    url(r'^fileedit/(?P<pk>[0-9]+)/$', FC15.views.fileedit, name = 'fileedit'),
    url(r'^filedelete/(?P<pk>[0-9]+)/$', FC15.views.filedelete, name = 'filedelete'),
    url(r'^filedownload/(?P<pk>[0-9]+)/$', FC15.views.filedownload, name = 'filedownload'),
    url(r'^recorddownload/(?P<pk>[0-9]+)/$', FC15.views.recorddownload, name = 'recorddownload'),
    url(r'^recorddelete/(?P<pk>[0-9]+)/$', FC15.views.recorddelete, name = 'recorddelete'),
    url(r'^jointeam/(?P<pk>[0-9]+)/$', FC15.views.jointeam, name = 'jointeam'),
    url(r'^jointeamrequest/(?P<pk>[0-9]+)/$', FC15.views.jointeamrequest, name = 'jointeamrequest'),
    url(r'^mailactivate/(?P<activate_code>.*)/$', FC15.views.activate, name = 'activate'),
    url(r'^resetpassword/(?P<reset_code>.*)/$', FC15.views.resetpassword, name = 'resetpassword'),
    url(r'^acceptrequest/(?P<pk>[0-9]+)/$', FC15.views.acceptrequest, name = 'acceptrequest'),
    url(r'^rejectrequest/(?P<pk>[0-9]+)/$', FC15.views.rejectrequest, name = 'rejectrequest'),
    url(r'^replay/(?P<pk>[0-9]+)/$', FC15.views.replay, name = 'replay'),

    # Admin page
	url(r'^admin/', admin.site.urls),
]

# Add static files
urlpatterns += staticfiles_urlpatterns()