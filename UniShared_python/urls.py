from django.conf.urls.defaults import patterns, include
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    #(r'^admin/', include(admin.site.urls)),
    (r'^profile/(?P<user_id>[^/]*)$', 'website.views.profile'),
    (r'^settings/$', 'website.views.settings'),
    (r'^disable-emails-notifications/$', 'website.views.disable_emails_notifications'),
    (r'^login/$', 'website.views.login'),
    #(r'^login-session/$', 'website.views.login_session'),
    (r'^signoff/$', 'website.views.sign_off'),
    (r'^social/', include('social_auth.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),
    (r'^login-error/$', 'website.views.login_error'),
    (r'^class/(?P<action>.*)$', 'website.views.redirect_to_notes'),
    (r'^notes/create-private/$', 'website.views.create_document'),
    (r'^notes/create/$', 'website.views.create_document'),
    (r'^notes/(?P<role>cowriters|participants)/(?P<resource_id>.*)$', 'website.views.cowriters_participants_document'),
    (r'^notes/delete/(?P<resource_id>.+)/$', 'website.views.remove_document'),
    #(r'^(?P<hub_id>[^/]+)/buddies/start$', 'website.views.note_taking_buddy'),
    #(r'^(?P<hub_id>[^/]+)/buddies/(?P<user_id>[^?/]*)$', 'website.views.note_taking_buddy_results'),
    (r'^notes/(?P<resource_id>.*)$', 'website.views.embedded_document'),
    (r'^activity/(?P<user_id>[a-z_0-9]*)/(?P<objects>(documents|hubs))$', 'website.views.activity'),
    (r'^hubs/create/$', 'website.views.create_hub'),
    (r'^hub/(?P<role>cowriters|participants)/(?P<hub_id>[^/]*)$', 'website.views.cowriters_participants_hub'),
    (r'^open25/$', 'website.views.open25_leadboard'),
    (r'^hubs/$', 'website.views.hubs'),
    (r'^partners/$', 'website.views.partners'),
    (r'^yyprod/$', 'website.views.yyprod'),
    (r'^qrcode/$', 'website.views.qrcode'),
    (r'^policy/$', 'website.views.policy'),
    (r'^about/$', 'website.views.about'),
    (r'^videonotes/$', 'website.views.videonotes'),
    (r'^oauth2callback$', 'website.views.oauth2callback'),
    (r'^oauth2$', 'website.views.oauth2'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        #(r'^spec/javascripts/fixtures/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.JASMINE_TEST_FIXTURE_DIRECTORY}),
        #(r'^jasmine/', include('django_jasmine.urls')),
        (r'^500/$', 'django.views.defaults.server_error'),
        (r'^404/$', 'django.views.generic.simple.direct_to_template', {'template': '404.html'}),
    )

urlpatterns += patterns('',
    (r'^(?P<user_id>[^/]+)/$', 'website.views.profile'),
    (r'^$', 'website.views.home'),
)