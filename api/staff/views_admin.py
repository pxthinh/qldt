from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
from django.utils.decorators import method_decorator
from ..core.decorators import staff_required
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import csv
import io
from datetime import datetime
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser

class IsStaffUser(BasePermission):
    """
    Allows access only to staff users.
    Returns 403 for both unauthenticated and non-staff users.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_403_FORBIDDEN
            )
        if not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        return True

from .models import Staff
from .serializers import StaffSerializer, StaffCreateUpdateSerializer


def _get_export_filename(base_name, format_type):
    """Generate a filename with timestamp for exports"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.{format_type}"

class StaffAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing staff members with store associations.
    
    This endpoint allows admin users to manage staff accounts and their store associations.
    All operations require admin privileges.
    
    ## Available Actions
    - **List Staff**: GET /api/admin/staff/
    - **Create Staff**: POST /api/admin/staff/
    - **Export Staff**: GET /api/admin/staff/export/
    - **Import Staff**: POST /api/admin/staff/import/
    - **Download Template**: GET /api/admin/staff/import/template/
    - **Retrieve Staff**: GET /api/admin/staff/{id}/
    - **Update Staff**: PUT /api/admin/staff/{id}/
    - **Delete Staff**: DELETE /api/admin/staff/{id}/ (soft delete)
    - **Activate Staff**: POST /api/admin/staff/{id}/activate/
    - **Get Staff by Store**: GET /api/admin/staff/by-store/{store_id}/
    - **Update Store Assignment**: POST /api/admin/staff/{id}/update-store/
    """
    queryset = Staff.objects.all().select_related('manager')
    http_method_names = ['get', 'post', 'put', 'delete']
    
    def get_permissions(self):
        # No permission classes needed as we're using the staff_required decorator
        return []
    
    @method_decorator(staff_required(require_manager=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'update_store']:
            return StaffCreateUpdateSerializer
        return StaffSerializer

    def get_queryset(self):
        from api.store.models import Store
        
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        store_id = self.request.query_params.get('store_id')
        
        # Apply search filter
        if search:
            # Get store IDs that match the search
            store_ids = Store.objects.filter(
                store_name__icontains=search
            ).values_list('id', flat=True)
            
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(store_id__in=store_ids)
            )
            
        # Filter by store if store_id is provided
        if store_id:
            queryset = queryset.filter(store_id=store_id)
            
        # Order by store name by joining with Store model
        return queryset.order_by('store_id', 'last_name', 'first_name')
        
    def perform_create(self, serializer):
        """Handle staff creation with store assignment."""
        # The store_id is now handled directly in the serializer
        serializer.save()
            
    def perform_update(self, serializer):
        """Handle staff update with store assignment."""
        # The store_id is now handled directly in the serializer
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def update_store(self, request, pk=None):
        """
        Update store assignment for a staff member.
        
        Request body should contain 'store_id' (can be null to unassign from store).
        """
        staff = self.get_object()
        store_id = request.data.get('store_id')
        
        if store_id is not None:
            from store.models import Store
            try:
                store = Store.objects.get(pk=store_id)
                staff.store = store
            except Store.DoesNotExist:
                return Response(
                    {"detail": f"Store with ID {store_id} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            staff.store = None
            
        staff.save()
        return Response(StaffSerializer(staff).data)
    
    @action(detail=False, methods=['get'], url_path='by-store/(?P<store_id>[^/.]+)')
    def by_store(self, request, store_id=None):
        """
        List all staff members assigned to a specific store.
        """
        staff_list = self.get_queryset().filter(store_id=store_id, is_active=True)
        page = self.paginate_queryset(staff_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(staff_list, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary='Export Staff Data',
        operation_description='''
        Export all staff data to CSV format.
        
        The exported file will include:
        - Staff details (username, email, name, phone, status)
        - Manager information (username, email, name)
        - Store information (name, contact details, address)
        
        Returns a CSV file download.
        ''',
        responses={
            200: openapi.Response(
                description='CSV file with staff data',
                schema=openapi.Schema(type=openapi.TYPE_FILE),
                examples={
                    'application/csv': {
                        'summary': 'Sample CSV export',
                        'value': (
                            'username,email,first_name,last_name,phone,is_active,manager_username,manager_email,manager_first_name,manager_last_name,store_id,store_name,store_email,store_phone,store_street,store_city,store_state,store_zip_code\n'
                        )
                    }
                }
            ),
            400: 'Error exporting data',
            403: 'Permission denied. User must be an admin.'
        },
        tags=['Data Integration Staff']
    )
    def export(self, request):
        """
        Export all staff data to CSV format.
        Includes staff details, manager information, and store details.
        """
        try:
            # Get all staff with related data
            staff_list = self.get_queryset().select_related('manager').all()
            
            # Pre-fetch store data
            from django.db.models import Prefetch
            from ..store.models import Store
            
            # Get all store IDs from staff
            store_ids = [s.store_id for s in staff_list if s.store_id is not None]
            
            # Create a dictionary of store data for quick lookup
            stores = {store.id: store for store in Store.objects.filter(id__in=store_ids)}
            
            # Define CSV headers with all staff, manager, and store fields
            field_names = [
                # Staff details
                'username', 'email', 'first_name', 'last_name',
                'phone', 'is_active',
                
                # Manager details
                'manager_username', 'manager_email', 'manager_first_name', 'manager_last_name',
                
                # Store details
                'store_id', 'store_name', 'store_email', 'store_phone',
                'store_street', 'store_city', 'store_state', 'store_zip_code',
            ]
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename={_get_export_filename("staff_export", "csv")}'
            
            writer = csv.DictWriter(response, fieldnames=field_names)
            writer.writeheader()
            
            # Write data rows with all fields
            for staff in staff_list:
                # Get manager details if exists
                manager = staff.manager
                store = stores.get(staff.store_id) if staff.store_id else None
                
                row_data = {
                    # Staff details
                    'username': staff.username or '',
                    'email': staff.email or '',
                    'first_name': staff.first_name or '',
                    'last_name': staff.last_name or '',
                    'phone': staff.phone or '',
                    'is_active': 'Yes' if staff.is_active else 'No',

                    # Manager details
                    'manager_username': manager.username if manager else '',
                    'manager_email': manager.email if manager else '',
                    'manager_first_name': manager.first_name if manager else '',
                    'manager_last_name': manager.last_name if manager else '',
                    
                    # Store details
                    'store_id': str(store.id) if store else '',
                    'store_name': store.store_name if store else '',
                    'store_email': store.email if store else '',
                    'store_phone': store.phone if store else '',
                    'store_street': store.street if store else '',
                    'store_city': store.city if store else '',
                    'store_state': store.state if store else '',
                    'store_zip_code': store.zip_code if store else '',
                }
                
                writer.writerow(row_data)
                
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Error exporting staff data: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        # The creator field is handled in the serializer
        serializer.save()
        
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary='Download Import Template',
        operation_description='''
        Download a CSV template for importing staff data.
        
        The template includes all possible fields with example values.
        Required fields are marked with (*).
        
        Required fields:
        - username (*): Unique username for the staff member
        - email (*): Email address (must be unique)
        - first_name (*): First name
        
        Optional fields:
        - last_name: Last name
        - phone: Phone number
        - password: Required for new users
        - is_active: 'yes' or 'no' (default: 'yes')
        - manager_username: Username of the manager
        - manager_email: Alternative to manager_username
        - store_id: ID of the store (if exists)
        - store_name: Name of the store (will create new if ID not provided)
        - store_email: Store email
        - store_phone: Store phone number
        - store_street: Store street address
        - store_city: Store city
        - store_state: Store state/province
        - store_zip_code: Store ZIP/postal code
        - store_is_active: 'yes' or 'no' (default: 'yes')
        ''',
        responses={
            200: openapi.Response(
                description='CSV template file',
                schema=openapi.Schema(type=openapi.TYPE_FILE),
                examples={
                    'text/csv': {
                        'summary': 'Sample CSV template',
                        'value': (
                            'username,email,first_name,last_name,phone,password,is_active,manager_username,manager_email,store_id,store_name,store_email,store_phone,store_street,store_city,store_state,store_zip_code,store_is_active\n'
                        )
                    }
                }
            ),
            400: 'Error generating template',
            403: 'Permission denied. User must be an admin.'
        },
        tags=['Data Integration Staff']
    )
    def template(self, request):
        """
        Download a CSV template for importing staff data.
        The template includes all required and optional fields with example values.
        """
        try:
            # Define all possible fields for import
            field_names = [
                # Staff details (required)
                'username', 'email', 'first_name', 'last_name', 'password',
                # Staff details (optional)
                'phone', 'is_active',
                # Manager details (optional)
                'manager_username', 'manager_email', 'manager_first_name', 'manager_last_name',
                # Store details (optional)
                'store_id', 'store_name', 'store_email', 'store_phone',
                'store_street', 'store_city', 'store_state', 'store_zip_code',
            ]
            
            # Sample data with all fields
            sample_data = {
                # Staff details
                'username': 'john_doe',
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'SecurePass123!',
                'phone': '+1234567890',
                'is_active': 'Yes',
                
                # Manager details (must exist in the system)
                'manager_username': 'jane_smith',
                'manager_email': 'jane.smith@example.com',
                'manager_first_name': 'Jane',
                'manager_last_name': 'Smith',
                
                # Store details (will be created if doesn't exist)
                'store_id': '',  # Leave empty to create new store
                'store_name': 'Main Store',
                'store_email': 'store@example.com',
                'store_phone': '+1234567891',
                'store_street': '123 Main St',
                'store_city': 'New York',
                'store_state': 'NY',
                'store_zip_code': '10001',
            }
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=staff_import_template.csv'
            
            writer = csv.DictWriter(response, fieldnames=field_names)
            writer.writeheader()
            writer.writerow(sample_data)
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Error generating template: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        tags=['Admin - Staff Management'],
        operation_summary="List all staff members",
        operation_description="""
        Returns a paginated list of staff members with optional filtering.
        
        ### Permissions
        - Only accessible by admin users
        
        ### Filtering
        - Search by username, email, or name using the `search` parameter
        - Filter by active status using `is_active`
        
        ### Pagination
        - Results are paginated (default: 20 per page)
        - Use `page` parameter to navigate through pages
        """,
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search term (searches in username, email, first_name, last_name)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'is_active',
                openapi.IN_QUERY,
                description="Filter by active status (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of results per page (max 100)",
                type=openapi.TYPE_INTEGER,
                default=20,
                required=False
            )
        ],
        responses={
            200: openapi.Response('Success', StaffSerializer(many=True)),
            403: 'Forbidden - User does not have permission',
            500: 'Internal server error'
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin - Staff Management'],
        operation_summary="Create a new staff member",
        operation_description="""
        Create a new staff member with the provided details.
        
        ### Required Fields
        - `username`: Unique username for the staff member
        - `email`: Valid email address
        - `first_name`: First name of the staff member
        - `password`: Password (min 8 characters)
        
        ### Optional Fields
        - `last_name`: Last name
        - `phone`: Contact number
        - `is_active`: Account status (default: true)
        - `store_id`: ID of the store to associate with
        - `manager_id`: ID of the manager
        """,
        request_body=StaffCreateUpdateSerializer,
        responses={
            201: openapi.Response('Staff created successfully', StaffSerializer),
            400: 'Invalid input data',
            403: 'Forbidden - User does not have permission',
            409: 'Conflict - Username or email already exists'
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin - Staff Management'],
        operation_summary="Retrieve a staff member",
        operation_description="""
        Retrieve details of a specific staff member by ID.
        """,
        responses={
            200: openapi.Response('Success', StaffSerializer),
            403: 'Forbidden - User does not have permission',
            404: 'Staff member not found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin - Staff Management'],
        operation_summary="Update a staff member",
        operation_description="""
        Update an existing staff member's details.
        
        ### Notes
        - All fields are optional (partial updates are supported)
        - To update password, include the new password in the request
        """,
        request_body=StaffCreateUpdateSerializer,
        responses={
            200: openapi.Response('Staff updated successfully', StaffSerializer),
            400: 'Invalid input data',
            403: 'Forbidden - User does not have permission',
            404: 'Staff member not found'
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin - Staff Management'],
        operation_summary="Delete a staff member",
        operation_description="""
        Soft delete a staff member (sets is_active=False).
        
        ### Notes
        - This is a soft delete operation
        - The record remains in the database but is marked as inactive
        """,
        responses={
            204: 'Staff member deactivated successfully',
            403: 'Forbidden - User does not have permission',
            404: 'Staff member not found'
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        methods=['post'],
        tags=['Admin - Staff Management'],
        operation_summary="Activate a staff member",
        operation_description="""
        Reactivate a deactivated staff member (sets is_active=True).
        
        ### Notes
        - This will allow the staff member to log in again
        - The staff member will retain their previous permissions
        """,
        request_body=None,
        responses={
            200: openapi.Response('Staff member activated successfully', StaffSerializer),
            403: 'Forbidden - User does not have permission',
            404: 'Staff member not found'
        }
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        staff = self.get_object()
        staff.is_active = True
        staff.save()
        serializer = self.get_serializer(staff)
        return Response(serializer.data)
