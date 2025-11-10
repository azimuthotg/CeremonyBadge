# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NPU CeremonyBadge is a Django-based badge issuing system for Nakhon Phanom University's graduation ceremony staff. The system manages the complete workflow from staff registration, photo upload and cropping, approval process, to badge printing with secure QR codes.

**Tech Stack:** Django 5.2.7, MySQL, Bootstrap 5, Pillow, WeasyPrint, QRCode with HMAC signatures

**Language:** Thai (TH) locale, Bangkok timezone

## Development Commands

### Environment Setup
```bash
# 1. Activate virtual environment (Windows WSL)
source Ceremony_env/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file from template
cp .env.example .env

# 4. Edit .env and fill in your actual values:
#    - SECRET_KEY (generate new one)
#    - Database credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST)
#    - ALLOWED_HOSTS (for production)
nano .env  # or use any text editor
```

### Database Operations
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize default data (departments, badge types, system settings)
python create_initial_data.py
```

### Running the Application
```bash
# Development server
python manage.py runserver 0.0.0.0:8000

# Production server (using Waitress - see DEPLOYMENT_WINDOWS.md)
python run_server.py
```

### Testing and Static Files
```bash
# Run tests for specific app
python manage.py test apps.accounts
python manage.py test apps.registry

# Collect static files
python manage.py collectstatic
```

## Architecture

### Application Structure

The project uses a modular Django app structure under `apps/`:

**apps/accounts/** - User authentication and department management
- Custom User model extending AbstractUser with role-based permissions (admin, officer, submitter)
- Department model for organizational hierarchy
- Role methods: `is_admin()`, `is_officer()`, `is_submitter()`, `can_manage_all()`

**apps/registry/** - Staff profile and badge request management
- StaffProfile: Core staff information with department and badge type assignment
- Photo: Image handling with Cropper.js integration (original + cropped versions)
- BadgeRequest: Workflow state machine with 10 status states (draft → printed → completed)
- Status validation methods: `can_edit()`, `can_submit()`, `can_approve()`, `can_reject()`

**apps/badges/** - Badge generation and printing
- BadgeType: 4 color-coded badge types (pink, red, yellow, green) for different access levels
- BadgeTemplate: Configurable templates with position coordinates for logo, photo, QR
- Badge: Generated badges with QR codes containing HMAC signatures for security
- PrintLog: Audit trail of all badge printing operations
- Security methods: `generate_qr_code()`, `verify_qr_signature()`

**apps/approvals/** - Approval workflow tracking
- ApprovalLog: Complete audit trail of all actions (submit, review, approve, reject, edit, comment)
- Tracks status transitions, comments, performer, IP address, and timestamps

**apps/reports/** - Dashboard and reporting (placeholder)

**apps/settings_app/** - System configuration
- SystemSetting model for global configuration (QR secret key, colors, university info, ceremony year)

### User Roles and Permissions

**Submitter**: Department representatives
- Register staff members and upload photos
- Access only their own department's data
- Submit requests for approval

**Officer**: Operations staff (equivalent to Admin except system settings)
- Review, approve, reject, and print badges
- Full access to all data and operations
- Cannot modify system settings

**Admin**: System administrators
- All Officer permissions plus system settings management
- User and department management
- System backup/restore

### Badge Request Workflow

The system implements a strict state machine for badge requests:

1. **draft** → Staff info entered
2. **photo_uploaded** → Photo cropped and saved
3. **ready_to_submit** → Ready for submission
4. **submitted** → Sent for review
5. **under_review** → Officer reviewing
6. **approved** OR **rejected** → Decision made
7. **badge_created** → Badge with QR generated
8. **printed** → Physical badge printed
9. **completed** → Process finished

State transitions are validated through model methods. Never bypass these validations.

### Security Features

**QR Code Security**: Each badge QR code contains HMAC SHA-256 signature
- Data format: `badge_number|full_name|badge_type|signature`
- Secret key stored in SystemSetting
- Always use `generate_qr_code()` and `verify_qr_signature()` methods

**Environment Variables**: Uses python-decouple for secure configuration
- All sensitive data stored in `.env` file (excluded from git)
- `.env.example` provided as template
- Required variables: SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
- See `.env.example` for setup instructions

**Image Processing**: Uses Pillow + ImageKit
- Original photos preserved in `media/photos/original/`
- Cropped photos in `media/photos/cropped/` (300x400, JPEG, 95% quality)
- Crop data stored as JSON from Cropper.js

## Important Design Patterns

### Related Name Consistency
All ForeignKey relationships use descriptive `related_name`:
- User → StaffProfile: `staff_profiles_created`
- User → BadgeRequest: `badge_requests_created`, `badge_requests_reviewed`, `badge_requests_approved`
- Department → StaffProfile: `staff_profiles`
- BadgeRequest → ApprovalLog: `approval_logs`

### Soft Deletes
Models use `is_active` flags rather than deletion:
- Department, User, BadgeType, BadgeTemplate, Badge

### Timestamps
All models include `created_at` and `updated_at` with auto_now_add/auto_now

### Thai Language
All verbose_name, help_text, and user-facing strings are in Thai

## Configuration

### Settings (ceremony_badge/settings.py)

**Custom User Model**: `AUTH_USER_MODEL = 'accounts.User'` (line 161)

**Static/Media Files**:
- STATIC_URL: `/static/`
- STATIC_ROOT: `BASE_DIR / 'staticfiles'`
- STATICFILES_DIRS: `[BASE_DIR / 'static']`
- MEDIA_URL: `/media/`
- MEDIA_ROOT: `BASE_DIR / 'media'`

**Database**: MySQL with utf8mb4 charset (current settings point to remote database)

**Locale**: `LANGUAGE_CODE = 'th'`, `TIME_ZONE = 'Asia/Bangkok'`

**Third-party Apps**:
- crispy_forms + crispy_bootstrap5 (Bootstrap 5 form rendering)
- imagekit (image processing)

### Initial Data Script

`create_initial_data.py` creates:
- Default NPU department
- 4 badge types with color codes
- Badge templates for each type
- System settings (QR key, colors, university name, ceremony year)

Always run this after migrations on fresh databases.

## Template Structure

**base.html**: Base template with Bootstrap 5
**login.html**: Authentication
**dashboard/**: Role-specific dashboards (admin, officer, submitter)
**registry/**: 3-step wizard (staff info → photo upload → confirmation) + list/detail views

UI Theme: Pastel purple primary (#A78BFA), white background, black text

## Common Tasks

### Adding a New Badge Type
1. Add to BadgeType.COLOR_CHOICES tuple
2. Update create_initial_data.py badge_types_data list
3. Create corresponding BadgeTemplate with position coordinates

### Modifying Workflow States
1. Update BadgeRequest.STATUS_CHOICES
2. Update validation methods: can_edit(), can_submit(), can_approve(), can_reject()
3. Update ApprovalLog.ACTION_CHOICES if new actions needed
4. Update template logic for state transitions

### Adding System Settings
1. Add to create_initial_data.py settings_data list
2. Access via `SystemSetting.objects.get(key='...')`
3. Support types: string, boolean, color, integer, json

### Extending User Permissions
Role checks use model methods:
- `user.is_admin()` - Admin only
- `user.is_officer()` - Officer only
- `user.can_manage_all()` - Admin or Officer
- `user.is_submitter()` - Submitter only

Use these in views/templates, not direct role string comparisons.

## Database Considerations

**Table Names**: All models specify `db_table` (plural snake_case):
- users, departments, staff_profiles, photos, badge_requests
- badges, badge_types, badge_templates, print_logs
- approval_logs

**Character Set**: MySQL utf8mb4 required for Thai language support

**Foreign Key Protection**:
- Department/BadgeType: `on_delete=models.PROTECT` (prevent accidental deletion)
- User references: `on_delete=models.SET_NULL` (preserve audit trail)
- Child records: `on_delete=models.CASCADE`

## Deployment Notes

See DEPLOYMENT_WINDOWS.md for complete deployment instructions.

**Production Checklist**:
1. Create `.env` file from `.env.example`
2. Generate new SECRET_KEY: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
3. Set DEBUG=False in .env
4. Configure ALLOWED_HOSTS with production domain/IP in .env
5. Set database credentials in .env
6. Collect static files: `python manage.py collectstatic`
7. Run with Waitress (included in requirements.txt)
8. Setup as Windows Service via NSSM or Task Scheduler

**Security Notes**:
- Never commit `.env` file to git (already in .gitignore)
- Use strong database passwords
- Rotate SECRET_KEY regularly
- Keep `.env` file permissions restricted

**Git Repository**: https://github.com/azimuthotg/CeremonyBadge

## Key Files

- `ceremony_badge/settings.py` - Main configuration
- `ceremony_badge/urls.py` - Root URL routing
- `manage.py` - Django CLI entry point
- `create_initial_data.py` - Database initialization
- `requirements.txt` - Python dependencies (Django 5.2.7, mysqlclient, Pillow, etc.)
- `DEPLOYMENT_WINDOWS.md` - Detailed deployment guide
- `README_NPU_CeremonyBadge.md` - Thai language project documentation

## Development Guidelines

**Photo Handling**: Always validate image dimensions and file size. Use ImageKit processors, not manual PIL operations.

**QR Code Generation**: Never generate QR codes manually. Always use Badge.generate_qr_code() method which includes HMAC signature.

**State Transitions**: Never directly set BadgeRequest.status. Use workflow validation methods and create corresponding ApprovalLog entries.

**Thai Language**: All user-facing content must be in Thai. Use verbose_name for model fields, Thai strings in templates.

**Color Scheme**: Follow pastel purple theme (#A78BFA primary). Badge colors must match BadgeType.color_code values.

**Audit Trail**: All significant actions should create ApprovalLog or PrintLog entries for compliance.
