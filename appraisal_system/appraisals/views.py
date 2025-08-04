from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .models import Task, PerformanceRating, Appraisal, AppraisalPeriod, NegotiationTicket
from .forms import TaskForm, RatingForm, AppraisalForm, NegotiationForm, AppraisalPeriodForm
from accounts.models import CustomUser
from django.http import HttpResponseForbidden
from django import forms

class HRAppraisalScoreForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = ['overall_percentage', 'task_completion_score', 'quality_score', 'timeliness_score', 'final_remarks']

@login_required
def task_list(request):
    if request.user.role == 'employee':
        tasks = Task.objects.filter(assigned_to=request.user).order_by('-created_at')
        return render(request, 'appraisals/task_list.html', {'tasks': tasks})
    elif request.user.role == 'team_leader':
        assigned_to_me = Task.objects.filter(assigned_to=request.user).order_by('-created_at')
        assigned_by_me = Task.objects.filter(assigned_by=request.user).order_by('-created_at')
        # For each completed task assigned by me, check if rated by me
        rated_task_ids = set(PerformanceRating.objects.filter(manager=request.user, task__in=assigned_by_me).values_list('task_id', flat=True))
        return render(request, 'appraisals/task_list.html', {
            'tasks_assigned_to_me': assigned_to_me,
            'tasks_assigned_by_me': assigned_by_me,
            'rated_task_ids': rated_task_ids,
            'is_team_leader': True,
        })
    elif request.user.role == 'manager':
        tasks = Task.objects.filter(assigned_by=request.user).order_by('-created_at')
        rated_task_ids = set(PerformanceRating.objects.filter(manager=request.user, task__in=tasks).values_list('task_id', flat=True))
        return render(request, 'appraisals/task_list.html', {'tasks': tasks, 'rated_task_ids': rated_task_ids})
    else:
        # HR: do not show tasks or completed appraisals
        return render(request, 'appraisals/task_list.html', {'is_hr': True})

@login_required
def create_task(request):
    if request.user.role not in ['manager', 'team_leader']:
        messages.error(request, 'You do not have permission to create tasks.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('task_list')
    else:
        form = TaskForm()
        # Filter employees under this manager/team leader
        form.fields['assigned_to'].queryset = request.user.get_subordinates()
    
    return render(request, 'appraisals/create_task.html', {'form': form})

@login_required
def submit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    if request.method == 'POST':
        if 'completion_report' in request.FILES:
            task.completion_report = request.FILES['completion_report']
        task.status = 'completed'
        task.completed_date = timezone.now()
        task.save()
        messages.success(request, 'Task submitted successfully!')
        return redirect('task_list')
    
    return render(request, 'appraisals/submit_task.html', {'task': task})

@login_required
def rate_employee(request, employee_id):
    employee = get_object_or_404(CustomUser, id=employee_id)
    if request.user.role == 'team_leader' and employee.role != 'employee':
        messages.error(request, 'Team leaders can only rate employees.')
        return redirect('dashboard')
    if request.user.role == 'manager' and employee.role != 'team_leader':
        messages.error(request, 'Managers can only rate team leaders.')
        return redirect('dashboard')
    if request.user.role not in ['manager', 'team_leader']:
        messages.error(request, 'You do not have permission to rate employees.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.employee = employee
            rating.manager = request.user
            rating.save()
            messages.success(request, f'Rating submitted for {employee.get_full_name()}!')
            return redirect('dashboard')
    else:
        form = RatingForm()
        form.fields['task'].queryset = Task.objects.filter(assigned_to=employee, status='completed')
    
    return render(request, 'appraisals/rate_employee.html', {'form': form, 'employee': employee})

@login_required
def create_appraisal(request, employee_id):
    employee = get_object_or_404(CustomUser, id=employee_id)
    if request.user.role == 'team_leader' and employee.role != 'employee':
        messages.error(request, 'Team leaders can only appraise employees.')
        return redirect('dashboard')
    if request.user.role == 'manager' and employee.role != 'team_leader':
        messages.error(request, 'Managers can only appraise team leaders.')
        return redirect('dashboard')
    if request.user.role not in ['manager', 'team_leader', 'hr_admin']:
        messages.error(request, 'You do not have permission to create appraisals.')
        return redirect('dashboard')

    # Remove active period validation, just use the latest period or None
    period = AppraisalPeriod.objects.order_by('-id').first()
    if not period:
        messages.error(request, 'No appraisal period exists. Please ask HR to create an appraisal period before appraising.')
        return redirect('dashboard')

    # Check if appraisal already exists
    existing_appraisal = Appraisal.objects.filter(employee=employee, period=period).first()
    if existing_appraisal:
        messages.info(request, 'Appraisal already exists for this employee.')
        return redirect('view_appraisal', appraisal_id=existing_appraisal.id)

    appraisal = Appraisal.objects.create(
        employee=employee,
        period=period,
        manager=request.user,
        overall_percentage=0,
        final_remarks="Generated automatically based on performance ratings.",
        status='submitted',  # Always send to HR
    )

    appraisal.calculate_scores()
    messages.success(request, f'Appraisal created for {employee.get_full_name()} and sent to HR!')
    return redirect('view_appraisal', appraisal_id=appraisal.id)

@login_required
def view_appraisal(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    
    # Check permissions
    if not (request.user == appraisal.employee or 
            request.user == appraisal.manager or 
            request.user.role == 'hr_admin'):
        messages.error(request, 'You do not have permission to view this appraisal.')
        return redirect('dashboard')
    
    context = {
        'appraisal': appraisal,
        'ratings': PerformanceRating.objects.filter(employee=appraisal.employee),
    }
    
    return render(request, 'appraisals/view_appraisal.html', context)

@login_required
def negotiate_appraisal(request, appraisal_id):
    from .models import Appraisal, NegotiationTicket
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    ticket = NegotiationTicket.objects.filter(appraisal=appraisal).first()
    is_hr = request.user.role == 'hr_admin'
    is_team_leader_negotiating = False  # You can set this based on your logic if needed

    if not (request.user == appraisal.employee or request.user.role == 'hr_admin'):
        messages.error(request, 'You do not have permission to view this negotiation.')
        return redirect('dashboard')

    if request.method == 'POST' and not is_hr:
        form = NegotiationForm(request.POST)
        if form.is_valid():
            negotiation = form.save(commit=False)
            negotiation.appraisal = appraisal
            negotiation.save()
            appraisal.status = 'negotiation'
            appraisal.save()
            messages.success(request, 'Negotiation request submitted successfully!')
            return redirect('view_appraisal', appraisal_id=appraisal.id)
    else:
        form = NegotiationForm(instance=ticket) if ticket and not is_hr else NegotiationForm()

    return render(request, 'appraisals/negotiate_appraisal.html', {
        'form': form,
        'appraisal': appraisal,
        'ticket': ticket,
        'is_team_leader_negotiating': is_team_leader_negotiating,
        'user': request.user,
        'is_hr': is_hr,
    })

@login_required
def approve_appraisal(request, appraisal_id):
    if request.user.role != 'hr_admin':
        messages.error(request, 'You do not have permission to approve appraisals.')
        return redirect('dashboard')
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    if request.method == 'POST':
        appraisal.status = 'approved'
        appraisal.hr_approved = True
        appraisal.hr_approved_by = request.user
        appraisal.save()
        messages.success(request, 'Appraisal approved and letter sent to employee!')
        return redirect('view_appraisal', appraisal_id=appraisal.id)
    return render(request, 'appraisals/approve_appraisal.html', {'appraisal': appraisal})

@login_required
def generate_appraisal_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    
    if request.user.role != 'hr_admin':
        messages.error(request, 'You do not have permission to generate PDF reports.')
        return redirect('dashboard')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appraisal_{appraisal.employee.get_full_name()}_{appraisal.period.title}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # PDF Content
    p.drawString(100, height - 100, f"PERFORMANCE APPRAISAL REPORT")
    p.drawString(100, height - 130, f"Employee: {appraisal.employee.get_full_name()}")
    p.drawString(100, height - 150, f"Period: {appraisal.period.title}")
    p.drawString(100, height - 170, f"Manager: {appraisal.manager.get_full_name()}")
    p.drawString(100, height - 200, f"Overall Score: {appraisal.overall_percentage:.1f}%")
    p.drawString(100, height - 220, f"Task Completion: {appraisal.task_completion_score:.1f}%")
    p.drawString(100, height - 240, f"Quality Score: {appraisal.quality_score:.1f}%")
    p.drawString(100, height - 260, f"Timeliness Score: {appraisal.timeliness_score:.1f}%")
    p.drawString(100, height - 290, f"Status: {appraisal.get_status_display()}")
    
    # Add remarks
    p.drawString(100, height - 320, "Final Remarks:")
    y_pos = height - 340
    for line in appraisal.final_remarks.split('\n'):
        p.drawString(120, y_pos, line)
        y_pos -= 20
    
    p.showPage()
    p.save()
    
    return response

@login_required
def create_appraisal_period(request):
    if request.user.role != 'hr_admin':
        messages.error(request, 'You do not have permission to create appraisal periods.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AppraisalPeriodForm(request.POST)
        if form.is_valid():
            period = form.save(commit=False)
            period.created_by = request.user
            period.save()
            messages.success(request, 'Appraisal period created successfully!')
            return redirect('dashboard')
    else:
        form = AppraisalPeriodForm()
    return render(request, 'appraisals/create_appraisal_period.html', {'form': form})

@login_required
def edit_appraisal_period(request, period_id):
    from .models import AppraisalPeriod
    period = get_object_or_404(AppraisalPeriod, id=period_id)
    if request.user.role != 'hr_admin':
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = AppraisalPeriodForm(request.POST, instance=period)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appraisal period updated successfully!')
            return redirect('dashboard')
    else:
        form = AppraisalPeriodForm(instance=period)
    return render(request, 'appraisals/edit_appraisal_period.html', {'form': form, 'period': period})

@login_required
def edit_appraisal_scores(request, appraisal_id):
    from .models import Appraisal
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    if request.user.role != 'hr_admin':
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = HRAppraisalScoreForm(request.POST, instance=appraisal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appraisal scores updated successfully!')
            return redirect('view_appraisal', appraisal_id=appraisal.id)
    else:
        form = HRAppraisalScoreForm(instance=appraisal)
    return render(request, 'appraisals/edit_appraisal_scores.html', {'form': form, 'appraisal': appraisal})