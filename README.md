# Employee Appraisal System
# Team Name Akatsuki

## Contributers
- **Shrivallabha S S PES1PG24CS044**
- **Tarun Kumar Sahu PES1PG24CS051**
- **P Venkat Raidu PES1PG24CS030**
- **Yashas L PES1PG24CS057**

## Brief Introduction

The Employee Appraisal System is a comprehensive Django-based web application designed to streamline and automate the employee performance evaluation process. This system provides a structured approach to task management, performance rating, and appraisal generation with role-based access control and workflow management.

### Key Features

- **Multi-Role User Management**: Supports Employee, Team Leader, Manager, and HR Admin roles
- **Task Management**: Create, assign, track, and complete tasks with priority levels and due dates
- **Performance Rating System**: Rate employees based on quality, timeliness, and overall performance
- **Automated Appraisal Generation**: Calculate scores based on performance ratings and task completion
- **Negotiation Workflow**: Allow employees to negotiate appraisal results with HR oversight
- **PDF Report Generation**: Generate professional appraisal reports in PDF format
- **Notification System**: Real-time notifications for appraisal updates and negotiations
- **Dashboard Views**: Role-specific dashboards with relevant information and actions

## System Architecture

### User Roles and Permissions

1. **Employee**
   - View assigned tasks
   - Submit task completions
   - View personal appraisals
   - Accept or negotiate appraisal results

2. **Team Leader**
   - Create and assign tasks to employees
   - Rate employee performance
   - Create appraisals for team members
   - View team member appraisals

3. **Manager**
   - Create and assign tasks to team leaders
   - Rate team leader performance
   - Create appraisals for team leaders
   - View team leader appraisals

4. **HR Admin**
   - Create appraisal periods
   - Approve/reject appraisals
   - Handle negotiation requests
   - Generate PDF reports
   - Create and manage users

### Core Models

- **CustomUser**: Extended user model with role-based permissions
- **Department**: Organizational structure management
- **Task**: Task assignment and tracking
- **PerformanceRating**: Individual performance evaluations
- **Appraisal**: Comprehensive performance assessments
- **AppraisalPeriod**: Time-based evaluation periods
- **NegotiationTicket**: Dispute resolution workflow
- **Notification**: System-wide notification management

## Exception Handling

The application implements comprehensive exception handling to ensure robust operation and user experience:

### 1. Permission-Based Exceptions

```python
# Role-based access control
if request.user.role not in ['manager', 'team_leader']:
    messages.error(request, 'You do not have permission to create tasks.')
    return redirect('dashboard')

# Hierarchical rating permissions
if request.user.role == 'team_leader' and employee.role != 'employee':
    messages.error(request, 'Team leaders can only rate employees.')
    return redirect('dashboard')
```

### 2. Data Validation Exceptions

```python
# Form validation with custom error messages
def clean_password2(self):
    password1 = self.cleaned_data.get('password1')
    password2 = self.cleaned_data.get('password2')
    if password1 and password2 and password1 != password2:
        raise forms.ValidationError("Passwords don't match")
    return password2
```

### 3. Object Not Found Exceptions

```python
# Safe object retrieval with 404 handling
task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
appraisal = get_object_or_404(Appraisal, id=appraisal_id)
```

### 4. Business Logic Exceptions

```python
# Appraisal period validation
if not period:
    messages.error(request, 'No appraisal period exists. Please ask HR to create an appraisal period before appraising.')
    return redirect('dashboard')

# Duplicate appraisal prevention
existing_appraisal = Appraisal.objects.filter(employee=employee, period=period).first()
if existing_appraisal:
    messages.info(request, 'Appraisal already exists for this employee.')
    return redirect('view_appraisal', appraisal_id=existing_appraisal.id)
```

### 5. File Upload Exceptions

```python
# Safe file handling in task submission
if 'completion_report' in request.FILES:
    task.completion_report = request.FILES['completion_report']
```

### 6. Database Query Exceptions

```python
# Safe notification operations
try:
    notification = Notification.objects.get(id=notification_id, recipient=user)
    notification.is_read = True
    notification.save()
    return True
except Notification.DoesNotExist:
    return False
```

### 7. HTTP Response Exceptions

```python
# Forbidden access handling
if request.user.role != 'hr_admin':
    return HttpResponseForbidden()

# Permission-based redirects
if not (request.user == appraisal.employee or 
        request.user == appraisal.manager or 
        request.user.role == 'hr_admin'):
    messages.error(request, 'You do not have permission to view this appraisal.')
    return redirect('dashboard')
```

### 8. PDF Generation Exceptions

```python
# PDF generation with proper content type handling
response = HttpResponse(content_type='application/pdf')
response['Content-Disposition'] = f'attachment; filename="appraisal_{appraisal.employee.get_full_name()}_{appraisal.period.title}.pdf"'
```

## Future Improvements

### 1. Enhanced Security Features

- **Two-Factor Authentication (2FA)**: Implement SMS or email-based 2FA for sensitive operations
- **Session Management**: Add session timeout and concurrent login restrictions
- **API Security**: Implement JWT tokens for API access
- **Audit Logging**: Comprehensive logging of all user actions and system changes

### 2. Advanced Analytics and Reporting

- **Performance Trends**: Historical performance analysis and trend visualization
- **Comparative Analytics**: Compare performance across departments and time periods
- **Predictive Analytics**: AI-powered performance prediction models
- **Custom Report Builder**: Drag-and-drop report creation interface

### 3. Workflow Enhancements

- **Multi-Level Approvals**: Support for complex approval hierarchies
- **Conditional Workflows**: Dynamic workflow paths based on performance scores
- **Automated Reminders**: Email and SMS notifications for pending actions
- **Bulk Operations**: Mass task assignment and appraisal generation

### 4. User Experience Improvements

- **Real-time Updates**: WebSocket integration for live dashboard updates
- **Mobile Application**: Native mobile app for iOS and Android
- **Progressive Web App (PWA)**: Offline-capable web application
- **Dark Mode**: User preference for dark/light theme

### 5. Integration Capabilities

- **HRIS Integration**: Connect with existing HR information systems
- **Email Integration**: Direct email notifications and reminders
- **Calendar Integration**: Sync with Google Calendar and Outlook
- **Single Sign-On (SSO)**: Integration with corporate identity providers

### 6. Performance Optimizations

- **Database Optimization**: Query optimization and indexing strategies
- **Caching Layer**: Redis-based caching for frequently accessed data
- **CDN Integration**: Content delivery network for static assets
- **Load Balancing**: Horizontal scaling capabilities

### 7. Advanced Features

- **Goal Setting**: Individual and team goal management
- **Competency Framework**: Skill-based assessment system
- **360-Degree Feedback**: Peer and subordinate feedback collection
- **Learning Management**: Training and development tracking

### 8. Data Management

- **Data Export**: Excel, CSV, and JSON export capabilities
- **Data Backup**: Automated backup and recovery procedures
- **Data Archiving**: Historical data management and retention policies
- **Data Migration**: Tools for importing data from legacy systems

### 9. Compliance and Governance

- **GDPR Compliance**: Data protection and privacy controls
- **Audit Trails**: Complete audit logging for compliance requirements
- **Data Retention**: Configurable data retention policies
- **Access Controls**: Granular permission management

### 10. Technical Improvements

- **Microservices Architecture**: Break down into smaller, scalable services
- **Containerization**: Docker and Kubernetes deployment
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring**: Application performance monitoring and alerting

## Installation and Setup

### Prerequisites

- Python 3.8+
- Django 4.0+
- SQLite (or PostgreSQL for production)
- ReportLab (for PDF generation)

### Installation Steps

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the development server: `python manage.py runserver`

### Configuration

- Update `SECRET_KEY` in settings.py for production
- Configure database settings for production environment
- Set up static and media file serving
- Configure email settings for notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository. 