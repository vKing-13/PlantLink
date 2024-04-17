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

class SensorForm(forms.Form):
    API_KEY=forms.CharField(max_length=30)
    sensor_name=forms.CharField(max_length=100)
    SENSOR_CHOICE = (
        ('DHT11', 'DHT11'),
        ('public', 'PH Sensor'),
        ('NPK', 'NPK'),
    )
    sensor_type=forms.ChoiceField(choices=SENSOR_CHOICE)
