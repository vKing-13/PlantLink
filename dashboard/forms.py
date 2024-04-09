from django import forms

class ChannelForm(forms.Form):
    channel_name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    location = forms.CharField(max_length=100)
    PRIVACY_CHOICES = (
        ('private', 'Private'),
        ('public', 'Public'),
    )
    privacy = forms.ChoiceField(choices=PRIVACY_CHOICES)
