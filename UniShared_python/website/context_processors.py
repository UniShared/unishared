'''
Created on 15 avr. 2012

@author: Arnaud
'''
def unishared_context(request):
    from django.conf import settings
    return {
        'BASE_URL': settings.BASE_URL, 'FACEBOOK_APP_ID': settings.FACEBOOK_APP_ID, \
        'GOOGLE_ANALYTICS_TRACK_ID' : settings.GOOGLE_ANALYTICS_TRACK_ID, \
        'FACEBOOK_OPEN_GRAPH_ROOT_NAME' : settings.FACEBOOK_OPEN_GRAPH_ROOT_NAME, \
        'GOOGLE_ANALYTICS_DOMAIN' : settings.GOOGLE_ANALYTICS_DOMAIN,
        'PUBLIC_DOCUMENT_MODEL_NAME' : 'notes',
        'FACEBOOK_OPEN_GRAPH_DOCUMENT_TYPE': settings.FACEBOOK_OPEN_GRAPH_DOCUMENT_TYPE,
        'FACEBOOK_OPEN_GRAPH_HUB_TYPE': settings.FACEBOOK_OPEN_GRAPH_HUB_TYPE,
        'USERVOICE_WIDGET_ID' : settings.USERVOICE_WIDGET_ID,
        'USERVOICE_DOCUMENT_WIDGET_ID' : settings.USERVOICE_DOCUMENT_WIDGET_ID
    }