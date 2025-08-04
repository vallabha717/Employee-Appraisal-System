from django.contrib import admin
from .models import Task, PerformanceRating, Appraisal, AppraisalPeriod, NegotiationTicket, Notification

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'assigned_by', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'assigned_by']
    search_fields = ['title', 'assigned_to__username']

@admin.register(PerformanceRating)
class PerformanceRatingAdmin(admin.ModelAdmin):
    list_display = ['employee', 'manager', 'quality_rating', 'overall_rating', 'rating_date']
    list_filter = ['quality_rating', 'timeliness_rating']

@admin.register(Appraisal)
class AppraisalAdmin(admin.ModelAdmin):
    list_display = ['employee', 'period', 'manager', 'overall_percentage', 'status', 'hr_approved']
    list_filter = ['status', 'hr_approved', 'period']
    actions = ['calculate_scores']
    
    def calculate_scores(self, request, queryset):
        for appraisal in queryset:
            appraisal.calculate_scores()
        self.message_user(request, f"Scores calculated for {queryset.count()} appraisals.")

@admin.register(AppraisalPeriod)
class AppraisalPeriodAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'is_active']

@admin.register(NegotiationTicket)
class NegotiationTicketAdmin(admin.ModelAdmin):
    list_display = ['appraisal', 'negotiated_by', 'status', 'created_at']
    list_filter = ['status', 'negotiated_by__role']
    search_fields = ['appraisal__employee__username', 'negotiated_by__username']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'title', 'message']
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notifications marked as unread.")