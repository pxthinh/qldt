from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Staff
from .serializers import StaffSerializer, StaffCreateUpdateSerializer


class StaffAdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing staff members.
    
    ## Permissions
    - Only admin users can access these endpoints
    
    ## Actions
    - `list`: Get all staff members
    - `create`: Create a new staff member
    - `retrieve`: Get a specific staff member
    - `update`: Update a staff member
    - `destroy`: Deactivate a staff member (soft delete)
    - `activate`: Reactivate a deactivated staff member
    """
    queryset = Staff.objects.all()
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get', 'post', 'put', 'delete']

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
        tags=['Admin Staff'],
        operation_summary="List all staff members",
        operation_description="""
        Returns a paginated list of staff members.
        Only accessible by admin users.
        """,
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search by username, email, or name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_active',
                openapi.IN_QUERY,
                description="Filter by active status (true/false)",
                type=openapi.TYPE_BOOLEAN
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
                default=20
            )
        ],
        responses={
            200: openapi.Response(
                description="List of staff members",
                schema=StaffSerializer(many=True)
            ),
            401: 'Authentication credentials were not provided.',
            403: 'You do not have permission to perform this action.'
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    @swagger_auto_schema(
        tags=['Admin Staff'],
        operation_summary="Get staff member details",
        operation_description="""
        Retrieve details of a specific staff member by ID.
        Only accessible by admin users.
        """,
        responses={
            200: openapi.Response(
                description="Staff member details",
                schema=StaffSerializer()
            ),
            401: 'Authentication credentials were not provided.',
            403: 'You do not have permission to perform this action.',
            404: 'Staff member not found.'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Staff'],
        operation_summary="Create a new staff member",
        operation_description="""
        Create a new staff member with the provided details.
        The creator field will be automatically set to the current user.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'first_name', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Unique username'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, default=''),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, default=''),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', min_length=8),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                'store_id': openapi.Schema(type=openapi.TYPE_INTEGER, default=None),
                'manager_id': openapi.Schema(type=openapi.TYPE_INTEGER, default=None)
            }
        ),
        responses={
            201: openapi.Response(
                description="Staff member created successfully",
                schema=StaffSerializer()
            ),
            400: 'Invalid input data',
            401: 'Authentication credentials were not provided.',
            403: 'You do not have permission to perform this action.'
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Staff'],
        operation_summary="Update a staff member",
        operation_description="""
        Update an existing staff member's details.
        Only the staff member themselves or an admin can update the profile.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', min_length=8),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'store_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'manager_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: openapi.Response(
                description="Staff member updated successfully",
                schema=StaffSerializer()
            ),
            400: 'Invalid input data',
            401: 'Authentication credentials were not provided.',
            403: 'You do not have permission to perform this action.',
            404: 'Staff member not found.'
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin Staff'],
        operation_summary="Deactivate a staff member",
        operation_description="""
        Soft deletes a staff member by setting is_active=False.
        Only admins can deactivate staff members.
        """,
        responses={
            204: 'Staff member deactivated successfully',
            401: 'Authentication credentials were not provided.',
            403: 'You do not have permission to perform this action.',
            404: 'Staff member not found.'
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        tags=['Admin Staff'],
        method='post',
        operation_summary="Activate a staff member",
        operation_description="""
        Reactivates a deactivated staff member by setting is_active=True.
        Only admins can activate staff members.
        """,
        responses={
            200: openapi.Response(
                description="Staff member activated successfully",
                schema=StaffSerializer()
            ),
            400: "Staff member is already active",
            401: 'Authentication credentials were not provided.',
            403: 'You do not have permission to perform this action.',
            404: 'Staff member not found.'
        }
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a deactivated staff member."""
        staff = self.get_object()
        staff.is_active = True
        staff.save()
        return Response({'status': 'staff activated'}, status=status.HTTP_200_OK)
