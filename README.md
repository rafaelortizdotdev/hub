# HONOR Supervisor Hub - Enterprise Store Assignment Management System

A comprehensive data pipeline and management system for retail store assignments, featuring advanced data modeling, bulk operations, and approval workflows.

### Core Data Management
- **Dual-List Assignment Manager** - SAP-style bulk operations interface
- **Admin Approval Workflow** - Complete business process automation
- **Store & Salesman Creation** - Forms with cascading dropdowns and validation
- **Service Layer & API** - RESTful endpoints with comprehensive error handling
- **Database Models** - Complete with proper relationships and constraints

### Advanced Data Engineering Features
- **Polymorphic Assignments** - Support for active/pending entities
- **Approval Workflow** - PENDING → APPROVED → ACTIVE state management
- **ERP Integration Ready** - Sync tracking and workflow preparation
- **CLI Data Tools** - Template generation, FK-aware loading, dry-run support
- **Data Validation** - Multi-layer validation (frontend + backend)
- **Audit Trail** - Complete change tracking and history

## Architecture

### Service Layer Pattern
```
┌─────────────┐
│   Routes    │ ← HTTP Endpoints
└──────┬──────┘
       │
┌──────▼──────┐
│  Services   │ ← Business Logic (Single Responsibility)
└──────┬──────┘
       │
┌──────▼──────┐
│   Models    │ ← Database ORM
└─────────────┘
```

### Database Design
- **Polymorphic Design**: `staff_type`/`staff_id` and `store_type`/`store_id` patterns
- **Complex Relationships**: Proper FK constraints, indexes, and referential integrity
- **Workflow States**: PENDING → APPROVED → ACTIVE with proper state management
- **Audit Trail**: Complete timestamp tracking and approval history

## Data Models

### Core Entities
- **Users** - Active staff members with role-based access
- **PendingClients** - Staff awaiting approval
- **Stores** - Active retail locations
- **PendingStores** - Stores awaiting approval
- **StoreAssignment** - Polymorphic assignment table with approval workflow

### Key Features
- **Polymorphic Assignments** - Single table handles multiple entity types
- **Approval Workflow** - Complete business process automation
- **ERP Sync Tracking** - Ready for enterprise system integration
- **Performance Indexes** - Optimized for bulk operations

## Technical Stack

- **Backend**: Flask + SQLAlchemy
- **Frontend**: Vanilla JavaScript + Tailwind CSS
- **Database**: SQLite (production-ready for PostgreSQL)
- **Migration**: Alembic with proper versioning
- **CLI Tools**: Click-based data management commands
- **UI Components**: SweetAlert2 for user feedback

## Data Engineering Capabilities

### Data Pipeline Features
- **Template Generation**: Dynamic model discovery and JSON template creation
- **FK-Aware Loading**: Topological sort for dependency resolution
- **Dry-Run Support**: Validation before commit
- **Archive System**: Historical data tracking with timestamps
- **Bulk Operations**: Enterprise-scale data management

### Data Quality & Validation
- **Schema Validation**: Type checking, required fields, format validation
- **Business Rules**: CI (7-10 digits), Phone (10-11 digits), status enums
- **Referential Integrity**: FK validation, cascade handling
- **Error Handling**: Comprehensive validation with detailed error messages

## Installation & Setup

### Requirements
- Python 3.7+
- Flask
- SQLite3

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd honor-hub

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run application
python app.py
```

### Access
- **URL**: `http://localhost:5000`
- **Default Password**: `honor1##` (for all users)

## 🔧 CLI Data Management Tools

### Template Generation
```bash
# Generate templates for all tables
flask generate-all-templates

# Generate specific table template
flask generate-template users users.json

# Load data from templates
flask load-templates --dry-run
```

### Data Operations
```bash
# Populate table from JSON/CSV
flask populate-table users users.json

# Clear table data
flask clear-table users

# Export table data
flask generate-template users users.json --format csv
```

## 📋 API Endpoints

### Assignment Management
- `GET /api/assignments/store/{store_type}/{store_id}` - Get store assignments
- `GET /api/assignments/available-staff` - Get available staff
- `POST /api/assignments/bulk` - Bulk assign/remove operations

### Admin Operations
- `GET /api/admin/assignments/pending` - Get pending assignments
- `PATCH /api/admin/assignments/approve` - Approve assignments
- `PATCH /api/admin/assignments/reject` - Reject assignments
- `PATCH /api/admin/assignments/sync` - Mark as synced to ERP

## Business Workflow

### Complete Assignment Lifecycle
1. **Supervisor Creates Assignment** - Selects store and staff
2. **Admin Reviews** - Views in approval interface
3. **Approval Decision** - Approve or reject with reason
4. **ERP Sync** - Mark as synced to enterprise system

### User Roles
- **Supervisor**: Create stores/staff, submit assignments
- **Admin**: Approve/reject assignments, create promoters, ERP sync

## Project Structure

```
honor-hub/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models
│   ├── extensions.py        # Database extensions
│   ├── routes/
│   │   ├── api.py          # API endpoints & services
│   │   ├── dashboard.py    # Dashboard routes
│   │   └── auth.py         # Authentication
│   └── templates/           # HTML templates
├── docs/                    # Documentation
│   ├── DESIGN.md           # Architecture & design
│   ├── CHANGELOG.md        # All changes & fixes
│   └── DE_TODO.md          # Future work
├── data/                    # Data templates & archives
├── migrations/              # Alembic migrations
├── tests/                   # Test files
└── requirements.txt         # Dependencies
```

## Data Engineering Patterns

### Polymorphic Data Modeling
```python
# Single table handles multiple entity types
class StoreAssignment(db.Model):
    staff_type = db.Column(db.String)  # 'user' or 'pending_client'
    staff_id = db.Column(db.String)    # The actual ID
    store_type = db.Column(db.String)  # 'store' or 'pending_store'
    store_id = db.Column(db.String)    # The actual ID
```

### Service Layer Architecture
```python
class AssignmentService:
    def bulk_create_assignments(self, assignments):
        # Business logic with transaction safety
        # Comprehensive error handling
        # Detailed validation
```

### CLI Data Tools
```python
@app.cli.command("load-templates")
def load_templates(in_dir, dry_run=False):
    # FK-aware loading order
    # Dry-run validation
    # Archive system
    # Error handling
```

## Portfolio Value

This project demonstrates:
- **Enterprise Data Pipeline** - Complete data management system
- **Advanced Database Design** - Polymorphic patterns, proper relationships
- **Business Process Automation** - Real-world workflow automation
- **Scalable Architecture** - Designed for enterprise use
- **Data Quality Focus** - Comprehensive validation and error handling
- **Developer Productivity** - CLI tools and template generation

## Future Enhancements

- **ERP Template Generation** - Excel export/import
- **Analytics Dashboard** - Data insights and metrics
- **Notification System** - Real-time updates
- **Performance Monitoring** - System metrics and logging
- **PostgreSQL Migration** - Production database upgrade

## License

Internal HONOR system - Authorized use only.

---

**Built with love for Data Engineering Excellence**
**This was built to satisfy a real world scenario problem**