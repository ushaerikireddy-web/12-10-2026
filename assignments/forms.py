from django import forms

from .models import Assignment, Submission


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('course', 'title', 'instructions', 'attachment', 'max_marks', 'due_date', 'is_published', 'allow_late')
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_late': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not (self.user.is_superuser or getattr(self.user, 'role', '') == 'ADMIN'):
            from courses.models import Course
            self.fields['course'].queryset = Course.objects.filter(instructor=self.user)


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('answer_text', 'file')
        widgets = {
            'answer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class GradingForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('marks', 'feedback', 'status')
        widgets = {
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
