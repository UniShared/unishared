from django.forms import ModelForm, Form, CharField, ValidationError
from website.models import NoteTakingBuddy, Training

__author__ = 'arnaud'

class DocumentTitleForm(Form):
    title = CharField(max_length=256)

    def clean_title(self):
        title = self.cleaned_data['title']

        result = Training.objects.filter(title__icontains=title)
        if not result.exists():
            raise ValidationError('This document doesn\'t exists')

class NoteTakingBuddyForm(ModelForm):
    class Meta:
        model = NoteTakingBuddy
        exclude = ('hub', 'user', 'score',)

    def __init__(self, *args, **kwargs):
        self._hub = kwargs.pop('hub', None)
        self._user = kwargs.pop('user', None)
        super(NoteTakingBuddyForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        inst = self.instance
        inst.hub = self._hub
        inst.user = self._user
        inst.score = inst.get_score()
        if commit:
            inst.save()
        return inst