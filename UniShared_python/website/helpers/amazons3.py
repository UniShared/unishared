# -*- coding: utf-8 -*-
'''
Created on 7 sept. 2012

@author: Arnaud
'''
import urlparse
from django.conf import settings
from django.contrib.staticfiles.storage import CachedFilesMixin
from django.core.files.base import ContentFile
from pipeline.storage import PipelineMixin
from require.storage import OptimizedFilesMixin
from s3_folder_storage.s3 import StaticStorage, DefaultStorage
from django.core.files.base import File
import os

def domain(url):
    return urlparse.urlparse(url).hostname

class CloudfrontMediaStorage(DefaultStorage):
    def __init__(self, *args, **kwargs):
        kwargs['bucket'] = settings.AWS_STORAGE_BUCKET_NAME
        kwargs['custom_domain'] = domain(settings.MEDIA_URL)
        super(CloudfrontMediaStorage, self).__init__(*args, **kwargs)

class CloudfrontStaticStorage(StaticStorage):
    def __init__(self, *args, **kwargs):
        kwargs['bucket'] = settings.AWS_STORAGE_BUCKET_NAME
        kwargs['custom_domain'] = domain(settings.STATIC_URL)
        super(CloudfrontStaticStorage, self).__init__(*args, **kwargs)



# From https://github.com/jezdez/django_compressor/issues/100
class ForgivingFile(File):
    def _get_size(self):
        if not hasattr(self, '_size'):
            if hasattr(self.file, 'size'):
                self._size = self.file.size
            elif hasattr(self.file, 'name') and os.path.exists(self.file.name):
                self._size = os.path.getsize(self.file.name)
            elif hasattr(self.file, 'tell') and hasattr(self.file, 'seek'):
                pos = self.file.tell()
                self.file.seek(0, os.SEEK_END)
                self._size = self.file.tell()
                self.file.seek(pos)
            else:
                raise AttributeError("Unable to determine the file's size.")
        return self._size

    def _set_size(self, size):
        self._size = size

    size = property(_get_size, _set_size)

    def chunks(self, chunk_size=None):
        """
        Read the file and yield chucks of ``chunk_size`` bytes (defaults to
        ``UploadedFile.DEFAULT_CHUNK_SIZE``).
        """
        if not chunk_size:
            chunk_size = self.DEFAULT_CHUNK_SIZE

        if hasattr(self, 'seek'):
            self.seek(0)

        while True:
            data = self.read(chunk_size)
            if not data:
                break
            yield data


class CloudfrontCachedPipelineStaticStorage(PipelineMixin, OptimizedFilesMixin, CachedFilesMixin, CloudfrontStaticStorage):
    # HACK: The chunks implementation in S3 files appears broken when gzipped!
    def hashed_name(self, name, content=None):
        if content is None:
            content = ContentFile(self.open(name).read(), name=name)
        return super(CloudfrontCachedPipelineStaticStorage, self).hashed_name(name, content)

    def save(self, name, content):
        content = ForgivingFile(content)
        name = super(CloudfrontCachedPipelineStaticStorage, self).save(name, content)
        return name