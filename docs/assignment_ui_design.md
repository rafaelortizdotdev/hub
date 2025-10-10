# Assignment UI Design - Dual-List Pattern

## Business Requirements (CONFIRMED)

### Real-World Usage
1. **Bulk operations are the norm** (not exception)
2. Supervisor manages **multiple assignments at once**
3. Two types of assignments:
   - **Salesmen → Stores** (store staff) - Supervisor can create
   - **Promoters → Stores** (promotional staff) - Admin creates (supervisors only assign)
4. Need **maximum simplicity** for users (complexity in code is acceptable)
5. Industry standard: **SAP-style dual-list selector**
6. **Assignments require admin approval** before becoming active

---

## UI Pattern: Store-Centric Dual List

### The Pattern You Described (SAP Inventory Style)

```
┌─────────────────────────────────────────────────────────────┐
│  Manage Store Assignments                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Select Store:  [City Market B-205 ▼]                      │
│                                                             │
│  ┌────────────────────────┬───┬────────────────────────┐   │
│  │  Available Staff       │   │  Assigned to Store     │   │
│  ├────────────────────────┤   ├────────────────────────┤   │
│  │ ☐ Juan Pérez          │   │ ☑ María López          │   │
│  │ ☐ Carlos Ruiz         │ → │ ☑ Ana García           │   │
│  │ ☐ Luis Martínez       │ ← │ ☑ Pedro Sánchez        │   │
│  │ ☐ Sofia Torres        │   │                        │   │
│  │ ☐ Diego López         │   │                        │   │
│  │                        │   │                        │   │
│  │ [+ Create New Staff]   │   │                        │   │
│  └────────────────────────┴───┴────────────────────────┘   │
│                                                             │
│  ☑ Salesmen  ☐ Promoters                                   │
│                                                             │
│  [Save Changes] [Cancel]                                   │
└─────────────────────────────────────────────────────────────┘
```

**This is EXCELLENT for:**
✅ Visual clarity (see current state)
✅ Bulk operations (multi-select)
✅ Instant feedback
✅ Familiar UX pattern
✅ One screen = one task

---

## Recommended Architecture

### Two Separate Views (BEST APPROACH)

#### View 1: **Creation Hub** 
*Create new entities (stores, salesmen)*

```
┌─────────────────────────────────────┐
│  Create New Entities                │
├─────────────────────────────────────┤
│  [Create Store]                     │
│  [Create Salesman]                  │
│                                     │
│  Recently Created:                  │
│  • Store: La Vega Mall (pending)    │
│  • Salesman: Juan P. (pending)      │
│                                     │
│  Note: Promoters are created by     │
│  administrators only.               │
└─────────────────────────────────────┘
```

#### View 2: **Assignment Manager**
*Assign existing/pending staff to stores (pending admin approval)*

```
┌─────────────────────────────────────────┐
│  Store Assignments                      │
├─────────────────────────────────────────┤
│  Store: [Search/Select] 🔍             │
│                                         │
│  [Dual List Interface Here]             │
│                                         │
│  Toggle: ○ Salesmen  ○ Promoters       │
│                                         │
│  ⚠️ Changes require admin approval      │
│  [Submit for Approval]                  │
└─────────────────────────────────────────┘
```

**Why separate views?**
- ✅ **Separation of concerns** (create vs assign)
- ✅ **Simpler UI** (one task per screen)
- ✅ **Faster workflow** (no context switching)
- ✅ **Mobile friendly** (focused interfaces)

---

## Technical Implementation

### Database Schema (Updated)

```python
class StoreAssignment(db.Model, TimestampMixin):
    """Polymorphic assignment table with approval workflow"""
    __tablename__ = 'store_assignments'
    id = db.Column(db.Integer, primary_key=True)
    
    # Staff member (polymorphic)
    staff_type = db.Column(db.String, nullable=False)  # 'user' or 'pending_client'
    staff_id = db.Column(db.String, nullable=False)    # The actual ID
    
    # Store (polymorphic)
    store_type = db.Column(db.String, nullable=False)  # 'store' or 'pending_store'
    store_id = db.Column(db.String, nullable=False)    # The actual ID
    
    # Role at this store
    role = db.Column(db.String, nullable=False)  # 'SALESMAN' or 'PROMOTER'
    
    # Metadata
    supervisor_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    
    # Approval workflow
    status = db.Column(db.String, nullable=False, default='PENDING')
    # Status: PENDING → APPROVED → ACTIVE (or REJECTED)
    approved_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    approved_date = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String, nullable=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_staff', 'staff_type', 'staff_id'),
        db.Index('idx_store', 'store_type', 'store_id'),
        db.Index('idx_role', 'role'),
        db.Index('idx_status', 'status'),
    )
```

---

### API Design (Bulk-Optimized)

```python
# Get current assignments for a store
GET /api/stores/{store_id}/assignments?role=SALESMAN
Response:
{
    "store": {
        "id": "ST-12345",
        "name": "City Market B-205",
        "type": "active"
    },
    "assigned": [
        {
            "id": 1,
            "staff_id": "U001",
            "staff_name": "María López",
            "staff_type": "user",
            "role": "SALESMAN",
            "assigned_date": "2024-01-15"
        }
    ]
}

# Get available staff (not assigned to this store)
GET /api/available-staff?store_id=ST-12345&role=SALESMAN
Response:
{
    "available": [
        {
            "id": "U002",
            "name": "Juan Pérez",
            "type": "user",
            "status": "ACTIVE"
        },
        {
            "id": 15,
            "name": "Carlos Ruiz",
            "type": "pending_client",
            "status": "PENDING"
        }
    ]
}

# Bulk update assignments (THE KEY ENDPOINT)
POST /api/stores/{store_id}/assignments/bulk
{
    "role": "SALESMAN",
    "assign": [
        {"staff_type": "user", "staff_id": "U002"},
        {"staff_type": "pending_client", "staff_id": 15}
    ],
    "unassign": [
        {"assignment_id": 1}
    ]
}
Response:
{
    "success": true,
    "assigned": 2,
    "unassigned": 1,
    "total_assigned": 3
}
```

---

### Service Layer

```python
class AssignmentService:
    @staticmethod
    def get_store_assignments(store_type, store_id, role):
        """Get all active assignments for a store by role"""
        return db.session.query(StoreAssignment).filter_by(
            store_type=store_type,
            store_id=store_id,
            role=role,
            status='ACTIVE'
        ).all()
    
    @staticmethod
    def get_available_staff(store_type, store_id, role, supervisor_id):
        """Get staff NOT assigned to this store"""
        # 1. Get all staff for supervisor by role
        # 2. Exclude already assigned to this store
        # 3. Return available list
        
    @staticmethod
    def bulk_assign(store_type, store_id, role, staff_list, supervisor_id):
        """Assign multiple staff to a store"""
        assignments = []
        for staff in staff_list:
            assignment = StoreAssignment(
                staff_type=staff['type'],
                staff_id=staff['id'],
                store_type=store_type,
                store_id=store_id,
                role=role,
                supervisor_id=supervisor_id,
                status='ACTIVE'
            )
            assignments.append(assignment)
        db.session.bulk_save_objects(assignments)
        db.session.commit()
        return len(assignments)
    
    @staticmethod
    def bulk_unassign(assignment_ids):
        """Remove multiple assignments"""
        db.session.query(StoreAssignment).filter(
            StoreAssignment.id.in_(assignment_ids)
        ).update({'status': 'INACTIVE', 'end_date': datetime.utcnow()})
        db.session.commit()
```

---

### Frontend Implementation

```javascript
// Assignment Manager Component
class AssignmentManager {
    constructor(storeId, role) {
        this.storeId = storeId;
        this.role = role; // 'SALESMAN' or 'PROMOTER'
        this.assigned = [];
        this.available = [];
        this.pendingChanges = {
            toAssign: [],
            toUnassign: []
        };
    }
    
    async loadData() {
        // Load assigned staff
        const assignedRes = await fetch(
            `/api/stores/${this.storeId}/assignments?role=${this.role}`
        );
        this.assigned = await assignedRes.json();
        
        // Load available staff
        const availableRes = await fetch(
            `/api/available-staff?store_id=${this.storeId}&role=${this.role}`
        );
        this.available = await availableRes.json();
        
        this.render();
    }
    
    moveToAssigned(staffIds) {
        // Move from available to assigned
        // Track in pendingChanges.toAssign
    }
    
    moveToAvailable(assignmentIds) {
        // Move from assigned to available
        // Track in pendingChanges.toUnassign
    }
    
    async saveChanges() {
        const response = await fetch(
            `/api/stores/${this.storeId}/assignments/bulk`,
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    role: this.role,
                    assign: this.pendingChanges.toAssign,
                    unassign: this.pendingChanges.toUnassign
                })
            }
        );
        
        if (response.ok) {
            showSuccess('Assignments updated!');
            this.loadData(); // Reload
        }
    }
}
```

---

## UI Flow

### Creation Flow (View 1)
```
1. Click "Create Store" → Form → Submit → Pending approval
2. Click "Create Salesman" → Form → Submit → Pending approval
3. Go to Assignment Manager
   (Promoters created by admin, not supervisor)
```

### Assignment Flow (View 2)
```
1. Select Store (dropdown with search)
2. Select Role (Salesmen/Promoters tabs)
3. See dual-list interface
   - Left: Available staff
   - Right: Currently assigned (APPROVED only)
4. Select staff → Click arrow → Move between lists
5. Click "Submit for Approval" → Creates PENDING assignments
6. See success message: "Changes submitted for admin approval"
7. Admin reviews → Approves/Rejects
8. If approved → Assignments become ACTIVE
```

### Admin Approval Flow (Separate View)
```
1. Admin sees "Pending Assignment Changes" dashboard
2. Reviews bulk assignment request:
   - Store: City Market B-205
   - Supervisor: Juan García
   - Proposed changes:
     • Assign: María López (SALESMAN)
     • Assign: Carlos Ruiz (SALESMAN)  
     • Remove: Pedro Sánchez (SALESMAN)
3. Admin clicks [Approve All] or [Reject]
4. If approved → Assignments status: PENDING → APPROVED → ACTIVE
5. Supervisor notified
```

---

## Implementation Plan

### Phase 1: Data Layer
1. ✅ Refactor `StoreAssignment` to polymorphic pattern
2. Create `AssignmentService` with bulk methods
3. Create helper services for staff/store lookup
4. Write unit tests

### Phase 2: API Layer
1. `GET /api/stores/{id}/assignments?role=X`
2. `GET /api/available-staff?store_id=X&role=X`
3. `POST /api/stores/{id}/assignments/bulk`
4. Test with Postman/curl

### Phase 3: Creation View
1. Simple forms for creating:
   - Stores (pending)
   - Salesmen (pending clients)
   - Promoters (pending clients)
2. Success feedback
3. Link to Assignment Manager

### Phase 4: Assignment Manager View
1. Store selector dropdown
2. Role tabs (Salesmen/Promoters)
3. Dual-list component
   - Multi-select checkboxes
   - Arrow buttons (→ ←)
   - Search/filter
4. Save button with bulk update
5. Loading states
6. Error handling

### Phase 5: Polish
1. Mobile responsive design
2. Keyboard shortcuts
3. Drag-and-drop (optional)
4. Undo functionality
5. Assignment history view

---

## Answer to Your Questions

### 1. Two Views?
**YES! Absolutely correct.**
- View 1: Creation Hub (simple forms)
- View 2: Assignment Manager (dual-list)

### 2. Will dual-list work?
**YES! Perfect for your use case.**
- Industry standard (SAP, Salesforce, etc.)
- Excellent for bulk operations
- Clear visual feedback
- Familiar to users

### 3. Complexity in code vs simplicity for users?
**100% correct priority.**
- User experience > code simplicity
- Bulk API = more complex code
- Dual-list UI = more JS
- But: Much better UX

---

## Recommendation

**Implement this order:**

1. **Start with Assignment Manager (View 2)** ← Most important
   - Build dual-list UI
   - Implement bulk API
   - Test with real workflow
   
2. **Then Creation Hub (View 1)** ← Secondary
   - Simple forms
   - Quick creation
   - Link to assignments

**Why this order?**
- Assignment is the **core pain point**
- Users will test it immediately
- Creation can use existing forms temporarily
- Validates the bulk approach early

---

## Updated Business Rules

### Permissions
- **Supervisor Can:**
  - Create stores (pending approval)
  - Create salesmen (pending approval)
  - Submit assignment changes (pending approval)
  - View promoters (created by admin)
  
- **Supervisor Cannot:**
  - Create promoters (admin only)
  - Approve assignments (admin only)
  - Directly activate assignments

- **Admin Can:**
  - Create/approve stores
  - Create/approve salesmen  
  - Create promoters
  - Approve/reject assignment changes
  - Override any assignment

### Assignment Status Flow
```
PENDING → (Admin Reviews) → APPROVED → ACTIVE
                         ↓
                      REJECTED (with reason)
```

### Key Differences from Original Design
1. ✅ Promoters created by admin only (not supervisors)
2. ✅ ALL assignments require admin approval
3. ✅ Dual-list shows only APPROVED assignments
4. ✅ Changes are submitted as batch for approval
5. ✅ Admin has dedicated approval interface

---

## Next Steps

1. Refactor `StoreAssignment` model to include approval workflow
2. Create `AssignmentService` with:
   - Bulk create (PENDING status)
   - Bulk approve/reject (admin only)
   - Get approved assignments for dual-list
3. Build bulk API endpoints with approval workflow
4. Create dual-list UI component
5. Create admin approval interface

**Ready to implement?** Which part should we start with?

