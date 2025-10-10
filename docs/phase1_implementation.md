# Phase 1: Core Assignment System Implementation

## Status: IN PROGRESS

### Completed ✅
1. **StoreAssignment Model** - Polymorphic design with approval workflow
   - Polymorphic staff (user/pending_client)
   - Polymorphic store (store/pending_store)
   - Role tracking (SALESMAN/PROMOTER)
   - Approval workflow (PENDING → APPROVED/REJECTED)
   - ERP sync tracking (synced_to_erp boolean)
   - Proper indexes for performance

---

## Phase 1 Goals

Build the core assignment system WITHOUT Excel generation:
- ✅ Assignment data model
- ⏳ Service layer (bulk operations)
- ⏳ API endpoints (assignment management)
- ⏳ Dual-list UI (supervisor view)
- ⏳ Admin approval interface
- ⏳ End-to-end workflow testing

---

## Next Tasks

### Task 1: AssignmentService
Create service class following Single Responsibility Principle:

```python
class AssignmentService:
    # Query methods
    @staticmethod
    def get_store_assignments(store_type, store_id, role, status='APPROVED')
    
    @staticmethod
    def get_available_staff(store_type, store_id, role, supervisor_id)
    
    @staticmethod
    def get_pending_assignments(supervisor_id=None)
    
    # Create methods
    @staticmethod
    def bulk_create_assignments(assignments_data, supervisor_id)
    
    # Approval methods (admin only)
    @staticmethod
    def approve_assignments(assignment_ids, admin_id)
    
    @staticmethod
    def reject_assignments(assignment_ids, admin_id, reason)
    
    # Sync tracking
    @staticmethod
    def mark_synced_to_erp(assignment_ids)
```

### Task 2: API Endpoints

```python
# Supervisor endpoints
GET  /api/stores/{store_id}/assignments?role=SALESMAN&status=APPROVED
GET  /api/available-staff?store_id=X&role=SALESMAN
POST /api/assignments/bulk
     {
         "store_type": "store",
         "store_id": "ST-12345",
         "role": "SALESMAN",
         "assign": [
             {"staff_type": "user", "staff_id": "U001"},
             {"staff_type": "pending_client", "staff_id": 15}
         ],
         "unassign": [1, 2, 3]  # assignment IDs
     }

# Admin endpoints
GET   /api/admin/assignments/pending
PATCH /api/admin/assignments/approve
      {"assignment_ids": [1, 2, 3]}
PATCH /api/admin/assignments/reject
      {"assignment_ids": [4, 5], "reason": "Duplicate assignment"}
PATCH /api/admin/assignments/mark-synced
      {"assignment_ids": [1, 2, 3]}
```

### Task 3: Dual-List UI

Build the SAP-style assignment interface:
- Store selector dropdown
- Role tabs (Salesmen/Promoters)
- Available staff list (left)
- Assigned staff list (right)
- Multi-select checkboxes
- Arrow buttons (→ ←)
- "Submit for Approval" button
- Loading/success states

### Task 4: Admin Approval Interface

Build admin dashboard for pending assignments:
- List of pending assignment batches
- Group by supervisor + store + date
- Show proposed changes (adds/removes)
- Bulk approve/reject buttons
- Rejection reason input
- "Mark as Synced to ERP" button

### Task 5: Dashboard Integration

Update existing dashboard:
- **Supervisor view:**
  - Link to Assignment Manager
  - Show pending assignment count
  - Show approved but not synced count
  
- **Admin view:**
  - Show pending assignments needing approval
  - Quick approve/reject actions
  - Sync status overview

---

## Data Flow

### Create Assignment Flow
```
1. Supervisor → Assignment Manager
2. Select store
3. Select role (Salesman/Promoter)
4. Move staff between lists
5. Click "Submit for Approval"
6. POST /api/assignments/bulk
7. Creates assignments with status=PENDING
8. Success message: "Submitted for approval"
```

### Approval Flow
```
1. Admin → Pending Assignments
2. Review batch:
   - Store: City Market B-205
   - Supervisor: Juan García  
   - Date: 2024-01-15
   - Changes:
     • Add: María López (SALESMAN)
     • Add: Carlos Ruiz (SALESMAN)
     • Remove: Pedro Sánchez
3. Click [Approve All]
4. PATCH /api/admin/assignments/approve
5. Assignments: PENDING → APPROVED
6. Supervisor notified
```

### ERP Sync Flow (Manual)
```
1. Admin → Approved Assignments
2. Select assignments
3. Click "Generate Excel" (Phase 2)
4. Download template
5. Upload to ERP (manual)
6. Click "Mark as Synced"
7. PATCH /api/admin/assignments/mark-synced
8. synced_to_erp = True
```

---

## Database Schema

```sql
-- Current schema (Phase 1)
CREATE TABLE store_assignments (
    id INTEGER PRIMARY KEY,
    
    -- Polymorphic references
    staff_type VARCHAR NOT NULL,      -- 'user' or 'pending_client'
    staff_id VARCHAR NOT NULL,
    store_type VARCHAR NOT NULL,      -- 'store' or 'pending_store'  
    store_id VARCHAR NOT NULL,
    
    -- Role and metadata
    role VARCHAR NOT NULL,            -- 'SALESMAN' or 'PROMOTER'
    supervisor_id VARCHAR NOT NULL,
    assigned_date DATETIME NOT NULL,
    end_date DATETIME,
    
    -- Approval workflow
    status VARCHAR NOT NULL DEFAULT 'PENDING',
    approved_by VARCHAR,
    approved_date DATETIME,
    rejection_reason TEXT,
    
    -- ERP sync
    synced_to_erp BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at DATETIME,
    updated_at DATETIME,
    
    -- Foreign keys
    FOREIGN KEY (supervisor_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_staff ON store_assignments(staff_type, staff_id);
CREATE INDEX idx_store ON store_assignments(store_type, store_id);
CREATE INDEX idx_role ON store_assignments(role);
CREATE INDEX idx_status ON store_assignments(status);
CREATE INDEX idx_supervisor ON store_assignments(supervisor_id);
```

---

## Business Rules

### Permissions
- **Supervisor:**
  - Create stores (pending)
  - Create salesmen (pending)
  - Submit assignment changes (pending)
  - View own assignments (all statuses)
  - Cannot approve assignments
  - Cannot create promoters

- **Admin:**
  - All supervisor permissions
  - Approve/reject assignments
  - Create promoters
  - Mark assignments as synced
  - View all assignments

### Status Transitions
```
PENDING → APPROVED (admin approves)
PENDING → REJECTED (admin rejects with reason)
APPROVED → [synced_to_erp = True] (admin marks after ERP upload)
```

### Validation Rules
1. Cannot assign same staff to same store with same role twice (active assignments)
2. Pending assignments can be edited before approval
3. Approved assignments cannot be modified (must create new change request)
4. Only admin can change status from PENDING

---

## Phase 2 Preview (ERP Templates)

What we'll add AFTER Phase 1 works:

1. **Template Generation Service**
   - Generate Excel for stores
   - Generate Excel for users
   - Generate Excel for assignments
   - Configurable template formats

2. **Bulk Download**
   - Download all pending templates
   - Download by date range
   - Download by supervisor

3. **Template History**
   - Track generated templates
   - Link assignments to template batches
   - Audit trail

4. **Advanced Features**
   - Template validation
   - Conflict detection
   - Rollback mechanism

---

## Testing Checklist

### Unit Tests
- [ ] AssignmentService methods
- [ ] Polymorphic queries work correctly
- [ ] Status transitions follow rules
- [ ] Permission checks

### Integration Tests
- [ ] Supervisor can submit assignments
- [ ] Admin can approve/reject
- [ ] Sync tracking works
- [ ] Dashboard displays correctly

### E2E Tests
- [ ] Complete workflow: create → assign → approve → sync
- [ ] Error handling (duplicates, invalid data)
- [ ] Permission boundaries respected
- [ ] UI feedback correct

---

## Success Criteria

Phase 1 is complete when:
1. ✅ Supervisor can create and submit assignments via dual-list UI
2. ✅ Admin can review and approve/reject via admin interface
3. ✅ System tracks sync status (boolean flag)
4. ✅ All statuses display correctly in dashboards
5. ✅ No critical bugs in core workflow
6. ✅ Ready for Phase 2 (Excel generation)

---

## Notes

- Excel generation deliberately postponed to Phase 2
- Focus on validating business logic first
- Template format can be refined with real usage
- Sync tracking is boolean (simple) for now
- Admin can manually create Excel templates during Phase 1

