# Store Assignment System - Design Document

Complete architecture and design decisions for the HONOR Hub Store Assignment Management System.

---

## Table of Contents
1. [Overview](#overview)
2. [Business Requirements](#business-requirements)
3. [Architecture](#architecture)
4. [Database Design](#database-design)
5. [API Design](#api-design)
6. [UI/UX Design](#uiux-design)
7. [Workflow](#workflow)

---

## Overview

### Purpose
Manage store-to-salesman assignments for a mobile retail business with:
- **Bulk operations** (industry standard requirement)
- **Approval workflow** (all changes require admin approval)
- **Dual entity support** (active and pending stores/staff)
- **ERP integration preparation** (sync tracking)

### Key Principles
1. **User Experience > Code Complexity** - Make it simple for users
2. **Bulk is the norm** - Not an exception
3. **Clear visual feedback** - Users always know what's happening
4. **Single Responsibility** - Each function/service does one thing

---

## Business Requirements

### Roles

#### Supervisor Can:
- Create stores (pending approval)
- Create salesmen (pending approval)  
- View all stores/staff under supervision
- Submit assignment changes (creates PENDING)
- View promoters (created by admin)

#### Supervisor Cannot:
- Create promoters (admin only)
- Approve assignments (admin only)
- Directly activate assignments

#### Admin Can:
- All supervisor permissions
- Create promoters
- Approve/reject assignments
- Override any assignment
- Mark assignments as synced to ERP

### Entities

#### Staff Types:
- **User** (Active) - Approved staff member
- **PendingClients** (Pending) - Awaiting approval to become User

#### Store Types:
- **Stores** (Active) - Approved store
- **PendingStores** (Pending) - Awaiting approval

#### Role Types:
- **SALESMAN** - Regular store staff (created by supervisor)
- **PROMOTER** - Promotional staff (created by admin only)

---

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

### Service Classes

#### CompanyService
- `find_by_name(name)` - Find company by name
- `create(name)` - Create new company

#### ProvinceService
- `find_by_name(name)` - Find province by name
- `create(name)` - Create new province

#### CityService
- `find_by_name(name, province_id)` - Find city in province
- `create(name, province_id)` - Create new city

#### MarketCenterService
- `find_by_name(name, city_id)` - Find market center in city
- `create(name, city_id)` - Create new market center

#### StoreCodeService
- `generate()` - Generate unique store code

#### AssignmentService
- `get_store_assignments()` - Get assignments for store
- `get_available_staff()` - Get unassigned staff
- `bulk_create_assignments()` - Create multiple assignments
- `bulk_remove_assignments()` - Remove multiple assignments
- `approve_assignments()` - Approve pending assignments
- `reject_assignments()` - Reject with reason
- `mark_synced()` - Mark as synced to ERP
- `get_assignment_details()` - Get full assignment info

---

## Database Design

### StoreAssignment (Core Table)

```sql
CREATE TABLE store_assignments (
    -- Identity
    id INTEGER PRIMARY KEY,
    
    -- Polymorphic Staff (user or pending_client)
    staff_type VARCHAR NOT NULL,
    staff_id VARCHAR NOT NULL,
    
    -- Polymorphic Store (store or pending_store)
    store_type VARCHAR NOT NULL,
    store_id VARCHAR NOT NULL,
    
    -- Assignment Details
    role VARCHAR NOT NULL,  -- SALESMAN or PROMOTER
    supervisor_id VARCHAR NOT NULL,
    assigned_date DATETIME,
    end_date DATETIME,
    
    -- Approval Workflow
    status VARCHAR NOT NULL DEFAULT 'PENDING',
    approved_by VARCHAR,
    approved_date DATETIME,
    rejection_reason VARCHAR,
    
    -- ERP Integration
    synced_to_erp BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at DATETIME,
    updated_at DATETIME,
    
    -- Foreign Keys
    FOREIGN KEY (supervisor_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Indexes for Performance
CREATE INDEX idx_staff ON store_assignments(staff_type, staff_id);
CREATE INDEX idx_store ON store_assignments(store_type, store_id);
CREATE INDEX idx_role ON store_assignments(role);
CREATE INDEX idx_status ON store_assignments(status);
CREATE INDEX idx_supervisor ON store_assignments(supervisor_id);
```

### Status Flow

```
PENDING → APPROVED → ACTIVE
        ↓
     REJECTED
```

- **PENDING** - Just created, awaiting admin review
- **APPROVED** - Admin approved, assignment is active
- **REJECTED** - Admin rejected with reason
- **ACTIVE** - (Future) After ERP sync

---

## API Design

### Assignment Management (Supervisor)

#### Get Store Assignments
```http
GET /api/assignments/store/{store_type}/{store_id}?role=SALESMAN&status=ALL

Response:
{
  "success": true,
  "assignments": [
    {
      "id": 1,
      "staff_name": "Juan Pérez",
      "role": "SALESMAN",
      "status": "PENDING",
      "assigned_date": "2025-10-10T10:30:00"
    }
  ]
}
```

#### Get Available Staff
```http
GET /api/assignments/available-staff?store_type=store&store_id=123&role=SALESMAN

Response:
{
  "success": true,
  "available": [
    {
      "id": "U001",
      "original_id": "U001",
      "name": "María López",
      "type": "user",
      "status": "ACTIVE",
      "stores_count": 2
    }
  ]
}
```

#### Bulk Assign/Remove
```http
POST /api/assignments/bulk

Request:
{
  "store_type": "store",
  "store_id": "123",
  "role": "SALESMAN",
  "assign": [
    {"staff_type": "user", "staff_id": "U001"}
  ],
  "unassign": [1, 2, 3]
}

Response:
{
  "success": true,
  "message": "Assignment changes submitted for approval",
  "created": 1,
  "removed": 3
}
```

### Admin Approval

#### Get Pending Assignments
```http
GET /api/admin/assignments/pending?status=PENDING

Response:
{
  "success": true,
  "assignments": [...],
  "stats": {
    "pending": 10,
    "approved_today": 5,
    "rejected_today": 1
  }
}
```

#### Approve Assignments
```http
PATCH /api/admin/assignments/approve

Request:
{
  "assignment_ids": [1, 2, 3]
}

Response:
{
  "success": true,
  "message": "3 assignments approved",
  "approved_count": 3
}
```

#### Reject Assignments
```http
PATCH /api/admin/assignments/reject

Request:
{
  "assignment_ids": [1, 2],
  "rejection_reason": "Staff not qualified for this role"
}

Response:
{
  "success": true,
  "message": "2 assignments rejected",
  "rejected_count": 2
}
```

---

## UI/UX Design

### Dual-List Pattern (SAP-Style)

```
┌─────────────────────────────────────────────────────────────┐
│  Manage Store Assignments                                   │
├─────────────────────────────────────────────────────────────┤
│  Store: [City Market B-205 ▼]                               │
│  Role:  ○ Salesmen  ○ Promoters                            │
│                                                             │
│  ┌────────────────────────┬───┬────────────────────────┐   │
│  │  Available Staff       │   │  Assigned to Store     │   │
│  ├────────────────────────┤   ├────────────────────────┤   │
│  │ ☐ Juan Pérez          │   │ ☑ María López          │   │
│  │   2 stores             │ → │   APPROVED             │   │
│  │ ☐ Carlos Ruiz         │ ← │   Assigned: 10/5/25    │   │
│  │   0 stores             │   │                        │   │
│  │ ☐ Luis Martínez       │   │ ☑ Ana García           │   │
│  │   1 store              │   │   PENDING              │   │
│  │                        │   │   Awaiting approval    │   │
│  └────────────────────────┴───┴────────────────────────┘   │
│                                                             │
│  Changes: 1 to assign, 1 to cancel                         │
│  [Cancel] [Submit for Approval]                            │
│                                                             │
│   Changes require admin approval                          │
└─────────────────────────────────────────────────────────────┘
```

### Visual States

#### Status Badges:
-  **PENDING** (Yellow) - Awaiting admin approval
-  **APPROVED** (Blue) - Active assignment
-  **REJECTED** (Red) - Rejected by admin

#### Action Badges:
-  **To Cancel** (Orange) - Cancelling pending request (no approval needed)
-  **To Remove** (Red) - Removing approved assignment (needs approval)
-  **To be submitted** (Gray) - Local change not yet saved

### User Flows

#### Flow 1: Create New Assignment
```
1. Select store from dropdown
2. Switch to "Salesmen" or "Promoters" tab
3. Select staff from "Available" list
4. Click → button
5. Staff moves to "Assigned" list with "To be submitted"
6. Click "Submit for Approval"
7. Assignment saved with status='PENDING'
8. Message: "1 assignment(s) created. Requires admin approval."
```

#### Flow 2: Cancel Pending Assignment
```
1. Select PENDING assignment (yellow badge)
2. Click ← button
3. Shows orange "To Cancel" badge
4. Click "Submit for Approval"
5. Assignment deleted from database
6. Message: "1 assignment(s) cancelled/removed."
   (No approval note - you're cancelling your own request)
```

#### Flow 3: Remove Approved Assignment
```
1. Select APPROVED assignment (blue badge)
2. Click ← button
3. Shows red "To Remove" badge
4. Click "Submit for Approval"
5. Assignment marked for removal (status='PENDING_REMOVAL')
6. Message: "1 assignment(s) cancelled/removed. Requires admin approval."
```

---

## Workflow

### Complete Assignment Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│ 1. SUPERVISOR CREATES ASSIGNMENT                         │
│    • Selects store and staff                             │
│    • Submits → Creates StoreAssignment(status='PENDING') │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│ 2. ADMIN REVIEWS                                         │
│    • Views in "Admin Approvals" interface                │
│    • Sees: staff name, store, supervisor, role           │
│    • Decision: Approve or Reject                         │
└───────┬─────────────────────────┬────────────────────────┘
        │                         │
        ▼ APPROVE                 ▼ REJECT
┌───────────────────┐     ┌──────────────────────┐
│ 3a. APPROVED      │     │ 3b. REJECTED         │
│ • Status=APPROVED │     │ • Status=REJECTED    │
│ • Assignment      │     │ • Rejection reason   │
│   becomes active  │     │ • Supervisor sees    │
└─────────┬─────────┘     └──────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────┐
│ 4. ERP SYNC (Phase 2)                                     │
│    • Admin generates Excel template                       │
│    • Admin uploads to ERP                                 │
│    • Admin marks synced_to_erp = TRUE                     │
└───────────────────────────────────────────────────────────┘
```

---

## Error Handling

### Frontend
- Console logging for all requests/responses
- Detailed error popups with:
  - Error message
  - Field name (if validation error)
  - Problematic data
  - Error type

### Backend
- Comprehensive validation before processing
- Different HTTP status codes:
  - 400 - Validation errors
  - 401 - Unauthorized
  - 403 - Forbidden (not admin)
  - 500 - Server errors
- Error response format:
```json
{
  "error": "Missing staff_type in assignment 0",
  "field": "staff_type",
  "data": {"id": "U001"},
  "type": "KeyError",
  "traceback": "..." // only in debug mode
}
```

---

## Design Decisions

### Why Polymorphic Assignments?
 Support both active and pending entities  
 No need for separate tables per entity type  
 Flexible for future entity types  
 Single source of truth for assignments  

### Why Dual-List UI?
 Industry standard (SAP, Salesforce)  
 Excellent for bulk operations  
 Clear visual feedback  
 Familiar to users  
 One screen = one task  

### Why Approval Workflow?
 Business requirement (admin oversight)  
 Audit trail  
 Error prevention  
 Integration with ERP process  

### Why Service Layer?
 Single Responsibility Principle  
 Easy to test  
 Reusable business logic  
 Clean separation of concerns  

---

**Last Updated:** 2025-10-10  
**Version:** Phase 1 Complete

