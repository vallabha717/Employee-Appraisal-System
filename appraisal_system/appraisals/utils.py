from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()

def create_notification(recipient, notification_type, title, message, appraisal=None):
    """Create a notification for a user"""
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        appraisal=appraisal
    )
    return notification

def notify_team_leader_about_appraisal(appraisal, notification_type, action):
    """Notify team leader when their team member's appraisal is updated"""
    employee = appraisal.employee
    
    # Find the team leader (manager of the employee)
    if employee.manager and employee.manager.role == 'team_leader':
        team_leader = employee.manager
        
        title = f"Team Member Appraisal {action}"
        message = f"Appraisal for your team member {employee.get_full_name()} has been {action.lower()}. " \
                 f"Period: {appraisal.period.title}. " \
                 f"Overall Score: {appraisal.overall_percentage:.1f}%"
        
        create_notification(
            recipient=team_leader,
            notification_type=notification_type,
            title=title,
            message=message,
            appraisal=appraisal
        )

def notify_hr_about_negotiation(negotiation_ticket):
    """Notify HR when a negotiation is requested"""
    hr_users = User.objects.filter(role='hr_admin')
    
    negotiator_role = "Team Leader" if negotiation_ticket.negotiated_by.role == 'team_leader' else "Employee"
    title = f"Appraisal Negotiation Request from {negotiator_role}"
    message = f"A negotiation request has been submitted for {negotiation_ticket.appraisal.employee.get_full_name()}'s appraisal " \
             f"by {negotiation_ticket.negotiated_by.get_full_name()} ({negotiator_role}). " \
             f"Period: {negotiation_ticket.appraisal.period.title}"
    
    for hr_user in hr_users:
        create_notification(
            recipient=hr_user,
            notification_type='negotiation_requested',
            title=title,
            message=message,
            appraisal=negotiation_ticket.appraisal
        )

def get_user_notifications(user, unread_only=False):
    """Get notifications for a user"""
    notifications = user.notifications.all()
    if unread_only:
        notifications = notifications.filter(is_read=False)
    return notifications

def mark_notification_as_read(notification_id, user):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False
