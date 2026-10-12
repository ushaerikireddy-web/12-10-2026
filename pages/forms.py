from django import forms
from django.utils.html import strip_tags

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # Honeypot spam trap: must stay empty
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'maxlength': 5000}),
        }

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Spam detected.')
        return ''

    def clean_message(self):
        msg = strip_tags(self.cleaned_data.get('message', '')).strip()
        if len(msg) < 10:
            raise forms.ValidationError('Message is too short (min 10 characters).')
        return msg
