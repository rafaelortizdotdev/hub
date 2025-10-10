# Store Assignment System Design

## Business Context
- **Mobile retail** environment
- **High salesman turnover** - salesmen rotate frequently between stores
- Salesmen can work at **multiple stores** concurrently
- Both stores and salesmen may be **pending approval**
- Need **simple, fast assignment workflow**

## Core Entities

### Users (Salesmen)
- Active users in `users` table (approved)
- Pending users in `pending_clients` table (awaiting approval)
- User type: Store Staff

### Stores
- Active stores in `stores` table (approved)
- Pending stores in `pending_stores` table (awaiting approval)

### Assignments
- Track which salesman works at which store
- Support pending entities (pre-approval assignments)
- Track assignment lifecycle (active, ended)

---

## Recommended Design

### 1. Database Schema

```sql
-- Simplified StoreAssignment table
CREATE TABLE store_assignments (
    id INTEGER PRIMARY KEY,
    
    -- Polymorphic reference to salesman
    salesman_type TEXT NOT NULL,  -- 'active' or 'pending'
    salesman_id TEXT NOT NULL,    -- user.id or pending_client.id
    
    -- Polymorphic reference to store  
    store_type TEXT NOT NULL,     -- 'active' or 'pending'
    store_id TEXT NOT NULL,       -- store.id or pending_store.id
    
    -- Metadata
    supervisor_id TEXT NOT NULL,
    assigned_date DATETIME NOT NULL,
    end_date DATETIME,            -- NULL = currently active
    status TEXT NOT NULL,         -- ACTIVE, ENDED
    notes TEXT,
    
    created_at DATETIME,
    updated_at DATETIME,
    
    FOREIGN KEY (supervisor_id) REFERENCES users(id)
)

-- Indexes for performance
CREATE INDEX idx_assignments_salesman ON store_assignments(salesman_type, salesman_id);
CREATE INDEX idx_assignments_store ON store_assignments(store_type, store_id);
CREATE INDEX idx_assignments_status ON store_assignments(status);
```

**Why this approach?**
- No nullable FKs (better data integrity)
- Polymorphic pattern (flexible, clean)
- Supports assignment history (end_date)
- Simple queries with type discriminator

---

### 2. User Workflow (Simplified)

#### Option A: Single Assignment Form (RECOMMENDED)
```
┌────────────────────────────────┐
│  Assign Salesman to Store     │
├────────────────────────────────┤
│ 1. Select/Create Store         │
│    ○ Search existing stores    │
│    ○ Create new store          │
│                                │
│ 2. Select/Create Salesman      │
│    ○ Search existing salesmen  │
│    ○ Create new salesman       │
│                                │
│ 3. [Assign]                    │
└────────────────────────────────┘
```

**Benefits:**
- ✅ Simple, fast workflow
- ✅ Easy to understand
- ✅ Mobile-friendly
- ✅ Handles 95% of use cases

#### Option B: View-First Approach (ALTERNATIVE)
```
┌────────────────────────────────┐
│  Store: City Market B-205      │
├────────────────────────────────┤
│ Current Salesmen (3):          │
│  • Juan Pérez   [Remove]       │
│  • María López  [Remove]       │
│  • Carlos Ruiz  [Remove]       │
│                                │
│ [+ Add Salesman]               │
└────────────────────────────────┘
```

**Benefits:**
- ✅ See current state first
- ✅ Manage assignments per store
- ✅ Clear visual feedback

---

### 3. API Design

#### Simple REST approach

```python
# Get assignments
GET /api/stores/{store_id}/assignments
GET /api/salesmen/{salesman_id}/assignments

# Create assignment (flexible input)
POST /api/assignments
{
    "salesman": {
        "type": "active",      # or "pending"
        "id": "U001"           # or pending_client_id
    },
    "store": {
        "type": "active",      # or "pending"
        "id": "ST-12345"       # or pending_store_id
    },
    "notes": "Optional notes"
}

# Or create with new entities
POST /api/assignments
{
    "salesman": {
        "type": "new",
        "data": {...}          # Creates pending_client
    },
    "store": {
        "type": "existing",
        "id": "ST-12345"
    }
}

# End assignment
PATCH /api/assignments/{id}/end

# Delete assignment
DELETE /api/assignments/{id}
```

---

### 4. Service Layer (Single Responsibility)

```python
class AssignmentService:
    @staticmethod
    def create_assignment(salesman_type, salesman_id, store_type, store_id, supervisor_id):
        """Create a new assignment"""
        
    @staticmethod
    def end_assignment(assignment_id):
        """End an active assignment"""
        
    @staticmethod
    def get_store_assignments(store_type, store_id, active_only=True):
        """Get all assignments for a store"""
        
    @staticmethod
    def get_salesman_assignments(salesman_type, salesman_id, active_only=True):
        """Get all assignments for a salesman"""
        
    @staticmethod
    def validate_assignment(salesman_type, salesman_id, store_type, store_id):
        """Check if assignment is valid (prevents duplicates, etc)"""


class StoreService:
    @staticmethod
    def find_by_id(store_id):
        """Find active store"""
        
    @staticmethod
    def find_pending_by_id(pending_id):
        """Find pending store"""
        
    @staticmethod
    def create_pending(data):
        """Create new pending store"""


class SalesmanService:
    @staticmethod
    def find_by_id(user_id):
        """Find active user"""
        
    @staticmethod
    def find_pending_by_id(pending_id):
        """Find pending client"""
        
    @staticmethod
    def create_pending(data):
        """Create new pending client"""
```

---

## Implementation Priority

### Phase 1: Core Assignment (Week 1)
1. ✅ Create `StoreAssignment` model (polymorphic)
2. Create assignment services
3. Simple assignment form (one-to-one)
4. API endpoints

### Phase 2: Management UI (Week 2)
1. View store assignments page
2. View salesman assignments page
3. End/remove assignment functionality
4. Assignment history

### Phase 3: Enhancements (Week 3)
1. Bulk assignment (if needed after testing Phase 1)
2. Assignment analytics
3. Notifications
4. Auto-approval workflows

---

## Questions to Answer

### Business Rules
1. **Can a salesman be assigned to multiple stores simultaneously?**
   - Yes → No validation needed
   - No → Add validation to prevent

2. **Can a store have multiple salesmen?**
   - Yes → Current design works
   - No → Add validation

3. **What happens when pending entities are approved?**
   - Option A: Auto-convert assignments (pending → active)
   - Option B: Keep as-is (polymorphic handles it)

4. **What happens when pending entities are rejected?**
   - Auto-delete related assignments?
   - Mark assignments as invalid?

5. **Do ended assignments need to be preserved?**
   - Yes → Keep with end_date
   - No → Can delete

### Technical Decisions
1. **Form approach:**
   - Simple single assignment? ✅ (RECOMMENDED)
   - Bulk assignment?
   - Store-centric view?

2. **Validation:**
   - Prevent duplicate active assignments?
   - Require approval for assignments?
   - Geographic restrictions?

---

## Recommendation

**Start with Option A (Simple Single Assignment)**

Why?
- ✅ Fastest to implement
- ✅ Easiest to test
- ✅ Covers 90% of use cases
- ✅ Can add bulk later if needed
- ✅ Mobile-friendly
- ✅ Less bug-prone

**Use polymorphic pattern for database**

Why?
- ✅ Clean, maintainable
- ✅ No nullable FK issues
- ✅ Easy queries
- ✅ Standard pattern

**Implement proper service layer**

Why?
- ✅ Single responsibility
- ✅ Testable
- ✅ Reusable
- ✅ Clear separation

---

## Next Steps

1. Answer business rule questions above
2. Refactor `StoreAssignment` model to polymorphic pattern
3. Create `AssignmentService`
4. Build simple assignment form
5. Test with real workflow
6. Iterate based on feedback

