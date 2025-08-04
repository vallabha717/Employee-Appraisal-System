from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import CustomUser, Department
from django import forms
from django.http import HttpResponseForbidden

@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}
    
    if user.role == 'employee':
        from appraisals.models import Task, Appraisal
        assigned_tasks = Task.objects.filter(assigned_to=user).order_by('-created_at')[:5]
        completed_tasks = Task.objects.filter(assigned_to=user, status='completed')
        context.update({
            'assigned_tasks': assigned_tasks,
            'completed_tasks': completed_tasks,
            'recent_appraisals': Appraisal.objects.filter(employee=user, hr_approved=True).order_by('-updated_at')[:3],
        })
        return render(request, 'accounts/employee_dashboard.html', context)
    
    elif user.role == 'manager':
        context.update({
            'departments': Department.objects.all(),
            'subordinates': user.get_subordinates(),
        })
        return render(request, 'accounts/manager_dashboard.html', context)
    
    elif user.role == 'hr_admin':
        from appraisals.models import Appraisal, NegotiationTicket, AppraisalPeriod
        context.update({
            'pending_appraisals': Appraisal.objects.filter(status='submitted', hr_approved=False),
            'negotiation_tickets': NegotiationTicket.objects.filter(status__in=['open', 'in_review']),
            'completed_appraisals': Appraisal.objects.filter(status='accepted', hr_approved=True),
            'appraisal_periods': AppraisalPeriod.objects.all().order_by('-start_date'),
        })
        return render(request, 'accounts/hr_dashboard.html', context)
    
    elif user.role == 'team_leader':
        from appraisals.models import Appraisal
        context.update({
            'departments': Department.objects.all(),
            'subordinates': user.get_subordinates(),
            'recent_appraisals': Appraisal.objects.filter(employee=user, hr_approved=True).order_by('-updated_at')[:3],
        })
        return render(request, 'accounts/team_leader_dashboard.html', context)
    
    return render(request, 'accounts/dashboard.html', context)

# Removed the register view as registration is now HR-only.

class HRUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'department', 'employee_id', 'phone', 'hire_date', 'manager']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

@login_required
def hr_create_user(request):
    if request.user.role != 'hr_admin':
        messages.error(request, 'You do not have permission to add users.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = HRUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully!')
            return redirect('dashboard')
    else:
        form = HRUserCreationForm()
    return render(request, 'accounts/hr_create_user.html', {'form': form})

@login_required
def accept_appraisal(request, appraisal_id):
    from appraisals.models import Appraisal, NegotiationTicket
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    if request.user != appraisal.employee:
        return HttpResponseForbidden()
    if request.method == 'POST':
        appraisal.status = 'accepted'
        appraisal.save()
        
        # Update negotiation ticket status if it exists
        try:
            negotiation_ticket = NegotiationTicket.objects.get(appraisal=appraisal)
            print(f"Found negotiation ticket: {negotiation_ticket.id}, status: {negotiation_ticket.status}")
            negotiation_ticket.status = 'resolved'
            negotiation_ticket.resolved_at = timezone.now()
            negotiation_ticket.save()
            print(f"Updated negotiation ticket status to: {negotiation_ticket.status}")
        except NegotiationTicket.DoesNotExist:
            print("No negotiation ticket found for this appraisal")
            pass  # No negotiation ticket exists
        
        messages.success(request, 'Appraisal accepted!')
        return redirect('dashboard')
    return redirect('view_appraisal', appraisal_id=appraisal.id)