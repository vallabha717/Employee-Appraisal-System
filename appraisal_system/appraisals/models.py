from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='assigned')
    due_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    completion_report = models.FileField(upload_to='task_reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name()}"
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now() and self.status != 'completed'
    
    @property
    def completion_status(self):
        if self.status == 'completed':
            if self.completed_date <= self.due_date:
                return 'on_time'
            else:
                return 'late'
        elif self.is_overdue:
            return 'overdue'
        return 'pending'

class PerformanceRating(models.Model):
    RATING_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('below_average', 'Below Average'),
        ('poor', 'Poor'),
    ]
    
    TIMELINESS_CHOICES = [
        ('on_time', 'On Time'),
        ('slightly_late', 'Slightly Late'),
        ('late', 'Late'),
        ('very_late', 'Very Late'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    
    # Rating components
    quality_rating = models.CharField(max_length=15, choices=RATING_CHOICES)
    timeliness_rating = models.CharField(max_length=15, choices=TIMELINESS_CHOICES)
    overall_rating = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Feedback
    remarks = models.TextField()
    keywords = models.CharField(max_length=500, help_text="Comma-separated keywords")
    
    rating_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rating for {self.employee.get_full_name()} by {self.manager.get_full_name()}"

class AppraisalPeriod(models.Model):
    title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"

class Appraisal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('negotiation', 'Under Negotiation'),
        ('accepted', 'Accepted'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appraisals')
    period = models.ForeignKey(AppraisalPeriod, on_delete=models.CASCADE)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_appraisals')
    
    # Calculated scores
    overall_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    task_completion_score = models.FloatField(default=0)
    quality_score = models.FloatField(default=0)
    timeliness_score = models.FloatField(default=0)
    
    # Status and workflow
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    final_remarks = models.TextField()
    hr_approved = models.BooleanField(default=False)
    hr_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_approvals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Appraisal: {self.employee.get_full_name()} - {self.period.title}"
    
    def calculate_scores(self):
        """Calculate appraisal scores based on ratings and tasks"""
        ratings = PerformanceRating.objects.filter(employee=self.employee)
        
        if ratings.exists():
            # Calculate average scores
            self.overall_percentage = sum(r.overall_rating for r in ratings) / ratings.count()
            
            # Task completion analysis
            tasks = Task.objects.filter(assigned_to=self.employee)
            if tasks.exists():
                completed_tasks = tasks.filter(status='completed').count()
                self.task_completion_score = (completed_tasks / tasks.count()) * 100
                
                # Quality and timeliness scores
                quality_scores = {'excellent': 100, 'good': 80, 'average': 60, 'below_average': 40, 'poor': 20}
                timeliness_scores = {'on_time': 100, 'slightly_late': 80, 'late': 60, 'very_late': 40}
                
                if ratings.exists():
                    self.quality_score = sum(quality_scores.get(r.quality_rating, 0) for r in ratings) / ratings.count()
                    self.timeliness_score = sum(timeliness_scores.get(r.timeliness_rating, 0) for r in ratings) / ratings.count()
        
        self.save()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('appraisal_created', 'Appraisal Created'),
        ('appraisal_submitted', 'Appraisal Submitted'),
        ('appraisal_approved', 'Appraisal Approved'),
        ('appraisal_rejected', 'Appraisal Rejected'),
        ('negotiation_requested', 'Negotiation Requested'),
        ('negotiation_resolved', 'Negotiation Resolved'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    appraisal = models.ForeignKey(Appraisal, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.recipient.get_full_name()}: {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class NegotiationTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_review', 'In Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    appraisal = models.OneToOneField(Appraisal, on_delete=models.CASCADE)
    negotiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_negotiations', null=True, blank=True)
    employee_reason = models.TextField()
    manager_response = models.TextField(blank=True)
    hr_decision = models.TextField(blank=True)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Negotiation: {self.appraisal.employee.get_full_name()}"