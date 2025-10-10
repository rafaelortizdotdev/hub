from flask import Blueprint, jsonify, request, session
import random
import string

from ..database import get_db_connection
from ..extensions import db
from ..models import Stores, PendingStores, PendingClients, Company, City, Province, MarketCenter, StoreAssignment, User

api_bp = Blueprint('api', __name__)


# Service classes following Single Responsibility Principle
class CompanyService:
    @staticmethod
    def find_by_name(name):
        """Find company by name"""
        return db.session.query(Company).filter_by(name=name).first()
    
    @staticmethod
    def create(name):
        """Create new company"""
        company = Company(name=name)
        db.session.add(company)
        db.session.commit()
        return company


class ProvinceService:
    @staticmethod
    def find_by_name(name):
        """Find province by name"""
        return db.session.query(Province).filter_by(name=name).first()
    
    @staticmethod
    def create(name, rm_id=1):
        """Create new province"""
        province = Province(name=name, rm_id=rm_id)
        db.session.add(province)
        db.session.commit()
        return province


class CityService:
    @staticmethod
    def find_by_name_and_province(name, province_id):
        """Find city by name and province"""
        return db.session.query(City).filter_by(name=name, province_id=province_id).first()
    
    @staticmethod
    def create(name, province_id):
        """Create new city"""
        city = City(name=name, province_id=province_id)
        db.session.add(city)
        db.session.commit()
        return city


class MarketCenterService:
    @staticmethod
    def find_by_name_and_city(name, city_id):
        """Find market center by name and city"""
        return db.session.query(MarketCenter).filter_by(name=name, city_id=city_id).first()
    
    @staticmethod
    def create(name, city_id):
        """Create new market center"""
        market_center = MarketCenter(name=name, city_id=city_id)
        db.session.add(market_center)
        db.session.commit()
        return market_center


class StoreCodeService:
    @staticmethod
    def generate():
        """Generate a unique store code"""
        while True:
            code = 'ST-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            existing = db.session.query(Stores).filter_by(id=code).first()
            if not existing:
                return code
    
    @staticmethod
    def exists(code):
        """Check if store code exists"""
        return db.session.query(Stores).filter_by(id=code).first() is not None


class AssignmentService:
    """Service for managing store assignments with approval workflow"""
    
    @staticmethod
    def get_store_assignments(store_type, store_id, role, status='APPROVED'):
        """Get all assignments for a store by role and status"""
        return db.session.query(StoreAssignment).filter_by(
            store_type=store_type,
            store_id=str(store_id),
            role=role,
            status=status
        ).all()
    
    @staticmethod
    def get_available_staff(store_type, store_id, role, supervisor_id):
        """Get staff NOT currently assigned to this store"""
        # Get all assigned staff IDs for this store and role
        assigned = db.session.query(
            StoreAssignment.staff_type,
            StoreAssignment.staff_id
        ).filter_by(
            store_type=store_type,
            store_id=str(store_id),
            role=role,
            status='APPROVED'
        ).all()
        
        assigned_pairs = [(a.staff_type, a.staff_id) for a in assigned]
        
        available = []
        
        # Get active users (store staff type)
        users = db.session.query(User).filter_by(
            supervisor_id=supervisor_id,
            status='ACTIVE'
        ).all()
        
        for user in users:
            if ('user', user.id) not in assigned_pairs:
                available.append({
                    'type': 'user',
                    'id': user.id,
                    'name': user.name,
                    'status': 'ACTIVE'
                })
        
        # Get pending clients
        pending_clients = db.session.query(PendingClients).filter_by(
            supervisor_id=supervisor_id,
            status='PENDING'
        ).all()
        
        for client in pending_clients:
            if ('pending_client', str(client.id)) not in assigned_pairs:
                available.append({
                    'type': 'pending_client',
                    'id': client.id,
                    'name': client.name,
                    'status': 'PENDING'
                })
        
        return available
    
    @staticmethod
    def get_pending_assignments(supervisor_id=None):
        """Get pending assignments, optionally filtered by supervisor"""
        query = db.session.query(StoreAssignment).filter_by(status='PENDING')
        
        if supervisor_id:
            query = query.filter_by(supervisor_id=supervisor_id)
        
        return query.order_by(StoreAssignment.created_at.desc()).all()
    
    @staticmethod
    def bulk_create_assignments(store_type, store_id, role, staff_list, supervisor_id):
        """Create multiple assignments at once (all PENDING status)"""
        created = []
        
        for staff in staff_list:
            assignment = StoreAssignment(
                staff_type=staff['type'],
                staff_id=str(staff['id']),
                store_type=store_type,
                store_id=str(store_id),
                role=role,
                supervisor_id=supervisor_id,
                status='PENDING'
            )
            db.session.add(assignment)
            created.append(assignment)
        
        db.session.commit()
        return created
    
    @staticmethod
    def bulk_remove_assignments(assignment_ids, supervisor_id):
        """Mark assignments for removal (create PENDING removal records)"""
        # For now, just delete them directly
        # In production, you might want to create "removal requests"
        deleted = db.session.query(StoreAssignment).filter(
            StoreAssignment.id.in_(assignment_ids),
            StoreAssignment.supervisor_id == supervisor_id
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return deleted
    
    @staticmethod
    def approve_assignments(assignment_ids, admin_id):
        """Approve pending assignments (admin only)"""
        from datetime import datetime
        
        updated = db.session.query(StoreAssignment).filter(
            StoreAssignment.id.in_(assignment_ids),
            StoreAssignment.status == 'PENDING'
        ).update({
            'status': 'APPROVED',
            'approved_by': admin_id,
            'approved_date': datetime.utcnow()
        }, synchronize_session=False)
        
        db.session.commit()
        return updated
    
    @staticmethod
    def reject_assignments(assignment_ids, admin_id, reason):
        """Reject pending assignments (admin only)"""
        from datetime import datetime
        
        updated = db.session.query(StoreAssignment).filter(
            StoreAssignment.id.in_(assignment_ids),
            StoreAssignment.status == 'PENDING'
        ).update({
            'status': 'REJECTED',
            'approved_by': admin_id,
            'approved_date': datetime.utcnow(),
            'rejection_reason': reason
        }, synchronize_session=False)
        
        db.session.commit()
        return updated
    
    @staticmethod
    def mark_synced_to_erp(assignment_ids):
        """Mark assignments as synced to ERP (admin only)"""
        updated = db.session.query(StoreAssignment).filter(
            StoreAssignment.id.in_(assignment_ids),
            StoreAssignment.status == 'APPROVED'
        ).update({
            'synced_to_erp': True
        }, synchronize_session=False)
        
        db.session.commit()
        return updated
    
    @staticmethod
    def get_assignment_details(assignment_id):
        """Get full details of an assignment with related entities"""
        assignment = db.session.query(StoreAssignment).filter_by(id=assignment_id).first()
        if not assignment:
            return None
        
        # Build details dictionary
        details = {
            'id': assignment.id,
            'role': assignment.role,
            'status': assignment.status,
            'assigned_date': assignment.assigned_date.isoformat() if assignment.assigned_date else None,
            'approved_date': assignment.approved_date.isoformat() if assignment.approved_date else None,
            'synced_to_erp': assignment.synced_to_erp,
            'rejection_reason': assignment.rejection_reason
        }
        
        # Get staff details
        if assignment.staff_type == 'user':
            staff = db.session.query(User).filter_by(id=assignment.staff_id).first()
            if staff:
                details['staff'] = {
                    'type': 'user',
                    'id': staff.id,
                    'name': staff.name,
                    'status': staff.status
                }
        else:
            staff = db.session.query(PendingClients).filter_by(id=int(assignment.staff_id)).first()
            if staff:
                details['staff'] = {
                    'type': 'pending_client',
                    'id': staff.id,
                    'name': staff.name,
                    'status': staff.status
                }
        
        # Get store details
        if assignment.store_type == 'store':
            store = db.session.query(Stores).filter_by(id=assignment.store_id).first()
            if store:
                details['store'] = {
                    'type': 'store',
                    'id': store.id,
                    'name': store.store_name,
                    'status': store.status
                }
        else:
            store = db.session.query(PendingStores).filter_by(id=int(assignment.store_id)).first()
            if store:
                details['store'] = {
                    'type': 'pending_store',
                    'id': store.id,
                    'name': store.store_name,
                    'code': store.store_code,
                    'status': store.status
                }
        
        return details


@api_bp.route('/stores')
def api_stores():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    stores = conn.execute(
        '''
        SELECT s.*, c.name as city_name, p.name as province_name 
        FROM stores s 
        JOIN cities c ON s.city_id = c.id 
        JOIN provinces p ON s.province_id = p.id 
        WHERE s.supervisor_id = ?
        ''',
        (session['user_id'],),
    ).fetchall()
    conn.close()

    stores_list = [dict(row) for row in stores]
    return jsonify(stores_list)


@api_bp.route('/market-centers', methods=['POST'])
def api_market_centers():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'Nombre requerido'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        existing = cursor.execute(
            'SELECT id FROM market_centers WHERE name = ?', (name,)
        ).fetchone()
        if existing:
            return jsonify({'error': 'Mercado/CC ya existe'}), 409

        cursor.execute('INSERT INTO market_centers (name) VALUES (?)', (name,))
        conn.commit()
        new_center = cursor.execute(
            'SELECT * FROM market_centers WHERE id = ?', (cursor.lastrowid,)
        ).fetchone()
        conn.close()

        return jsonify({'id': new_center['id'], 'name': new_center['name']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/search-stores')
def api_search_stores():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    try:
        # Search existing stores with proper joins
        stores = db.session.query(Stores).join(Company).join(City).join(Province).filter(
            Stores.supervisor_id == session['user_id']
        ).filter(
            db.or_(
                Stores.id.like(f'%{query}%'),
                Stores.store_name.like(f'%{query}%'),
                Company.name.like(f'%{query}%')
            )
        ).all()

        # Search pending stores with proper joins
        pending_stores = db.session.query(PendingStores).join(Company).join(City).join(Province).filter(
            PendingStores.supervisor_id == session['user_id']
        ).filter(
            db.or_(
                PendingStores.store_name.like(f'%{query}%'),
                PendingStores.store_code.like(f'%{query}%'),
                Company.name.like(f'%{query}%')
            )
        ).all()

        # Convert to dict format
        results = []
        
        # Add existing stores
        for store in stores:
            results.append({
                'id': store.id,
                'store_name': store.store_name,
                'store_code': store.id,  # store.id is the store code
                'city_id': store.city_id,
                'type': 'existing'
            })
        
        # Add pending stores
        for store in pending_stores:
            results.append({
                'id': store.id,
                'store_name': store.store_name,
                'store_code': store.store_code,
                'city_id': store.city_id,
                'type': 'pending'
            })

        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/search-clients')
def api_search_clients():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    try:
        conn = get_db_connection()
        clients = conn.execute(
            '''
            SELECT id, name, contact_number, city, province
            FROM pending_clients 
            WHERE (name LIKE ? OR contact_number LIKE ?) 
            AND supervisor_id = ?
            ''',
            (f'%{query}%', f'%{query}%', session['user_id']),
        ).fetchall()
        conn.close()

        results = [dict(c) for c in clients]
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/approve-store/<int:store_id>', methods=['POST'])
def approve_store(store_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Find the pending store with relationships
        pending_store = db.session.query(PendingStores).filter_by(
            id=store_id, 
            supervisor_id=session['user_id']
        ).first()
        
        if not pending_store:
            return jsonify({'error': 'Store not found'}), 404

        # Create the actual store record
        new_store = Stores(
            id=pending_store.store_code,  # Use store_code as the store ID
            store_name=pending_store.store_name,
            province_id=pending_store.province_id,
            company_id=pending_store.company_id,
            city_id=pending_store.city_id,
            market_center_id=pending_store.market_center_id,
            supervisor_id=pending_store.supervisor_id,
            street=pending_store.street,
            level=pending_store.level,
            local=pending_store.local,
            status='ACTIVE'
        )
        
        db.session.add(new_store)
        
        # Mark pending store as approved
        pending_store.status = 'APPROVED'
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Store approved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/approve-client/<int:client_id>', methods=['POST'])
def approve_client(client_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        client = cursor.execute(
            'SELECT * FROM pending_clients WHERE id = ? AND supervisor_id = ?',
            (client_id, session['user_id']),
        ).fetchone()
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        cursor.execute(
            'UPDATE pending_clients SET status = "APPROVED" WHERE id = ?', (client_id,)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Client approved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Simple creation endpoints - Phase 1
@api_bp.route('/stores/create', methods=['POST'])
def create_store():
    """Create a new pending store"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        
        # Find or create company
        company = CompanyService.find_by_name(data['company'])
        if not company:
            company = CompanyService.create(data['company'])
        
        # Find or create province
        province = ProvinceService.find_by_name(data['province'])
        if not province:
            province = ProvinceService.create(data['province'])
        
        # Find or create city
        city = CityService.find_by_name_and_province(data['city'], province.id)
        if not city:
            city = CityService.create(data['city'], province.id)
        
        # Find or create market center
        market_center = MarketCenterService.find_by_name_and_city(data['market_center'], city.id)
        if not market_center:
            market_center = MarketCenterService.create(data['market_center'], city.id)
        
        # Generate unique store code
        store_code = StoreCodeService.generate()
        
        # Create pending store
        pending_store = PendingStores(
            store_name=data['store_name'],
            store_code=store_code,
            province_id=province.id,
            company_id=company.id,
            city_id=city.id,
            market_center_id=market_center.id,
            supervisor_id=session['user_id'],
            street=data['street'],
            level=data['level'],
            local=data['local'],
            status='PENDING'
        )
        
        db.session.add(pending_store)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Store created and pending approval',
            'store_id': pending_store.id,
            'store_code': store_code
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/salesmen/create', methods=['POST'])
def create_salesman():
    """Create a new pending salesman (client)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        
        # Find or create province
        province = ProvinceService.find_by_name(data['province'])
        if not province:
            province = ProvinceService.create(data['province'])
        
        # Find or create city
        city = CityService.find_by_name_and_province(data['city'], province.id)
        if not city:
            city = CityService.create(data['city'], province.id)
        
        # Create pending client
        pending_client = PendingClients(
            name=data['name'],
            client_id=data['client_id'],
            gender=data['gender'],
            contact_number=data['contact_number'],
            email=data.get('email', ''),
            city_id=city.id,
            province_id=province.id,
            supervisor_id=session['user_id'],
            status='PENDING'
        )
        
        db.session.add(pending_client)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Salesman created and pending approval',
            'salesman_id': pending_client.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Assignment Management Endpoints
@api_bp.route('/assignments/store/<store_type>/<store_id>', methods=['GET'])
def get_store_assignments(store_type, store_id):
    """Get all assignments for a store"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        role = request.args.get('role', 'SALESMAN')
        status = request.args.get('status', 'APPROVED')
        
        assignments = AssignmentService.get_store_assignments(store_type, store_id, role, status)
        
        result = []
        for assignment in assignments:
            details = AssignmentService.get_assignment_details(assignment.id)
            if details:
                result.append(details)
        
        return jsonify({
            'success': True,
            'store_type': store_type,
            'store_id': store_id,
            'role': role,
            'status': status,
            'assignments': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/assignments/available-staff', methods=['GET'])
def get_available_staff():
    """Get staff available for assignment to a store"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        store_type = request.args.get('store_type', 'store')
        store_id = request.args.get('store_id')
        role = request.args.get('role', 'SALESMAN')
        
        if not store_id:
            return jsonify({'error': 'store_id required'}), 400
        
        available = AssignmentService.get_available_staff(
            store_type, store_id, role, session['user_id']
        )
        
        return jsonify({
            'success': True,
            'available': available
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/assignments/bulk', methods=['POST'])
def bulk_assign():
    """Bulk create/remove assignments for a store"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        store_type = data.get('store_type', 'store')
        store_id = data.get('store_id')
        role = data.get('role', 'SALESMAN')
        assign_list = data.get('assign', [])
        unassign_ids = data.get('unassign', [])
        
        if not store_id:
            return jsonify({'error': 'store_id required'}), 400
        
        # Create new assignments
        created = []
        if assign_list:
            created = AssignmentService.bulk_create_assignments(
                store_type, store_id, role, assign_list, session['user_id']
            )
        
        # Remove assignments
        removed_count = 0
        if unassign_ids:
            removed_count = AssignmentService.bulk_remove_assignments(
                unassign_ids, session['user_id']
            )
        
        return jsonify({
            'success': True,
            'message': 'Assignment changes submitted for approval',
            'created': len(created),
            'removed': removed_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Admin Assignment Endpoints
@api_bp.route('/admin/assignments/pending', methods=['GET'])
def get_pending_assignments():
    """Get all pending assignments (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # TODO: Add admin permission check
    
    try:
        supervisor_id = request.args.get('supervisor_id')
        
        assignments = AssignmentService.get_pending_assignments(supervisor_id)
        
        result = []
        for assignment in assignments:
            details = AssignmentService.get_assignment_details(assignment.id)
            if details:
                result.append(details)
        
        return jsonify({
            'success': True,
            'pending_count': len(result),
            'assignments': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/assignments/approve', methods=['PATCH'])
def approve_assignments():
    """Approve pending assignments (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # TODO: Add admin permission check
    
    try:
        data = request.get_json()
        assignment_ids = data.get('assignment_ids', [])
        
        if not assignment_ids:
            return jsonify({'error': 'assignment_ids required'}), 400
        
        updated = AssignmentService.approve_assignments(assignment_ids, session['user_id'])
        
        return jsonify({
            'success': True,
            'message': f'{updated} assignments approved',
            'approved_count': updated
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/assignments/reject', methods=['PATCH'])
def reject_assignments():
    """Reject pending assignments (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # TODO: Add admin permission check
    
    try:
        data = request.get_json()
        assignment_ids = data.get('assignment_ids', [])
        reason = data.get('reason', 'No reason provided')
        
        if not assignment_ids:
            return jsonify({'error': 'assignment_ids required'}), 400
        
        updated = AssignmentService.reject_assignments(assignment_ids, session['user_id'], reason)
        
        return jsonify({
            'success': True,
            'message': f'{updated} assignments rejected',
            'rejected_count': updated
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/assignments/mark-synced', methods=['PATCH'])
def mark_synced():
    """Mark assignments as synced to ERP (admin only)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # TODO: Add admin permission check
    
    try:
        data = request.get_json()
        assignment_ids = data.get('assignment_ids', [])
        
        if not assignment_ids:
            return jsonify({'error': 'assignment_ids required'}), 400
        
        updated = AssignmentService.mark_synced_to_erp(assignment_ids)
        
        return jsonify({
            'success': True,
            'message': f'{updated} assignments marked as synced',
            'synced_count': updated
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


