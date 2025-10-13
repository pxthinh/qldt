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


class StaffAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing staff members.
    
    This endpoint allows admin users to manage staff accounts in the system.
    All operations require admin privileges.
    
    ## Available Actions
    - **List Staff**: GET /api/admin/staff/
    - **Create Staff**: POST /api/admin/staff/
    - **Retrieve Staff**: GET /api/admin/staff/{id}/
    - **Update Staff**: PUT /api/admin/staff/{id}/
    - **Delete Staff**: DELETE /api/admin/staff/{id}/ (soft delete)
    - **Activate Staff**: POST /api/admin/staff/{id}/activate/
    """
    queryset = Staff.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete']
    
    def get_permissions(self):
        # No permission classes needed as we're using the staff_required decorator
        return []
    
    @method_decorator(staff_required(require_manager=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffCreateUpdateSerializer
        return StaffSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add filtering if needed
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # The creator field is handled in the serializer
        serializer.save()

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
