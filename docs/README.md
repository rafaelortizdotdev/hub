# HONOR Hub - Documentation

Complete documentation for the Store Assignment Management System.

---

## Documentation Index

### Main Documents

1. **[DESIGN.md](DESIGN.md)** - Architecture and design decisions
   - Business requirements
   - Database schema
   - API specifications
   - UI/UX patterns
   - Workflows

2. **[CHANGELOG.md](CHANGELOG.md)** - All changes and fixes
   - Phase 1 features
   - Bug fixes
   - Improvements
   - Known limitations

3. **[DE_TODO.md](DE_TODO.md)** - Future work and TODOs
   - Phase 2 plans
   - Optional enhancements

---

## Quick Start

### For Developers
1. Read `DESIGN.md` to understand the architecture
2. Check `CHANGELOG.md` for recent changes
3. Review API endpoints in `DESIGN.md`

### For Users
- The system has three main interfaces:
  1. **Create Store/Salesman** - Simple forms with validation
  2. **Manage Assignments** - Dual-list interface for bulk operations
  3. **Admin Approvals** - Review and approve pending changes

---

## Current Status

### Phase 1 Complete
- Store/Salesman creation forms
- Dual-list assignment manager
- Admin approval interface
- Comprehensive error handling
- Input validation
- Contextual user feedback

### Phase 2 Planned
- ERP template generation
- Excel import/export
- Notification system
- Analytics dashboard

---

## Technical Stack

- **Backend:** Flask + SQLAlchemy
- **Frontend:** Vanilla JavaScript + Tailwind CSS
- **Database:** SQLite
- **UI Components:** SweetAlert2 for popups

---

## File Structure

```
docs/
├── README.md              ← You are here
├── DESIGN.md             ← Architecture & design
├── CHANGELOG.md          ← All changes & fixes
└── DE_TODO.md            ← Future work

app/
├── routes/
│   ├── api.py           ← API endpoints + services
│   ├── dashboard.py     ← Dashboard routes
│   └── auth.py          ← Authentication
├── templates/
│   ├── assignments.html          ← Dual-list manager
│   ├── admin_approvals.html      ← Admin interface
│   ├── create_store.html         ← Store form
│   └── create_salesman.html      ← Salesman form
└── models.py            ← Database models
```

---

## Reporting Issues

When reporting issues, please include:
1. What you were trying to do
2. What happened (with screenshots if possible)
3. Browser console errors (F12 → Console tab)
4. Network errors (F12 → Network tab)

---

## 📖 Key Concepts

### Assignment States
- **PENDING** - Awaiting admin approval
- **APPROVED** - Active assignment
- **REJECTED** - Rejected with reason

### Entity Types
- **Active:** User, Stores (approved and ready)
- **Pending:** PendingClients, PendingStores (awaiting approval)

### Roles
- **SALESMAN** - Created by supervisors
- **PROMOTER** - Created by admins only

---

**Version:** Phase 1 Complete  
**Last Updated:** 2025-10-10

