from django import forms
from .models import Task, PerformanceRating, Appraisal, NegotiationTicket, AppraisalPeriod

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = PerformanceRating
        fields = ['task', 'quality_rating', 'timeliness_rating', 'overall_rating', 'remarks', 'keywords']
        widgets = {
            'overall_rating': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.1}),
            'remarks': forms.Textarea(attrs={'rows': 4}),
            'keywords': forms.TextInput(attrs={'placeholder': 'leadership, teamwork, communication'}),
        }

class AppraisalForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = ['final_remarks']
        widgets = {
            'final_remarks': forms.Textarea(attrs={'rows': 6}),
        }

class NegotiationForm(forms.ModelForm):
    class Meta:
        model = NegotiationTicket
        fields = ['employee_reason']
        widgets = {
            'employee_reason': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Please explain why you would like to negotiate this appraisal...'}),
        }

class AppraisalPeriodForm(forms.ModelForm):
    class Meta:
        model = AppraisalPeriod
        fields = ['title', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
