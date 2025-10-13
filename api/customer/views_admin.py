from typing import Mapping
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q

# Absolute imports for better reliability
from api.customer.models import Customer
from api.customer.serializers import CustomerSerializer
from api.core.decorators import staff_required

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

def _to_int(x, default=0, min_val=None, max_val=None):
    try:
        v = int(x)
    except Exception:
        v = default
    if min_val is not None and v < min_val: v = min_val
    if max_val is not None and v > max_val: v = max_val
    return v

_FIELD_MAP = {
    "id": "customer_id",
    "customer_id": "customer_id",
    "username": "user_name",
    "user_name": "user_name",
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "phone": "phone",
}

def _sanitize_update(body: Mapping[str, str]) -> dict:
    """Only allow updating specific fields (prevent client from setting id)."""
    allowed = [
        "user_name", "password",
        "first_name", "last_name",
        "phone", "email", "street", "city", "state", "zip_code",
    ]
    out = {}
    for k in allowed:
        if k in body:
            out[k] = body.get(k)
    return out

# ================== LIST + CREATE ==================
@method_decorator(staff_required(), name='dispatch')
class CustomerAdminListCreate(APIView):
    
    @swagger_auto_schema(
        tags=['Admin Customer'],
        operation_summary="List all customers",
        operation_description="Retrieve a list of all customers (admin only)",
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
                description="Filter by active status", 
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
            200: openapi.Response('List of customers', CustomerSerializer(many=True)),
            403: 'You do not have permission to perform this action.'
        }
    )
    def get(self, request, format=None):
        queryset = Customer.objects.all()
        
        # Apply filters
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user_name__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
            
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = CustomerSerializer(queryset[start:end], many=True)
        return Response({
            'count': queryset.count(),
            'next': f"?page={page + 1}&page_size={page_size}" if end < queryset.count() else None,
            'previous': f"?page={page - 1}&page_size={page_size}" if start > 0 else None,
            'results': serializer.data
        })
        
    @swagger_auto_schema(
        tags=['Admin Customer'],
        operation_summary="Create a new customer",
        operation_description="Create a new customer (admin only)",
        request_body=CustomerSerializer,
        responses={
            201: openapi.Response('Customer created successfully', CustomerSerializer),
            400: 'Invalid input data',
            403: 'You do not have permission to perform this action.'
        }
    )
    def post(self, request, format=None):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(staff_required(), name='dispatch')
class CustomerAdminDetail(APIView):
    
    def get_object(self, pk):
        try:
            return Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return None
    
    @swagger_auto_schema(
        tags=['Admin Customer'],
        operation_summary="Retrieve a customer",
        operation_description="Retrieve details of a specific customer (admin only)",
        responses={
            200: openapi.Response('Customer details', CustomerSerializer),
            403: 'You do not have permission to perform this action.',
            404: 'Customer not found.'
        }
    )
    def get(self, request, pk, format=None):
        customer = self.get_object(pk)
        if not customer:
            return Response(
                {"detail": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        tags=['Admin Customer'],
        operation_summary="Update a customer",
        operation_description="Update details of a specific customer (admin only)",
        request_body=CustomerSerializer,
        responses={
            200: openapi.Response('Customer updated successfully', CustomerSerializer),
            400: 'Invalid input data',
            403: 'You do not have permission to perform this action.',
            404: 'Customer not found.'
        }
    )
    def put(self, request, pk, format=None):
        customer = self.get_object(pk)
        if not customer:
            return Response(
                {"detail": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        tags=['Admin Customer'],
        operation_summary="Delete a customer",
        operation_description="Delete a specific customer (admin only)",
        responses={
            204: 'Customer deleted successfully',
            403: 'You do not have permission to perform this action.',
            404: 'Customer not found.'
        }
    )
    def delete(self, request, pk, format=None):
        customer = self.get_object(pk)
        if not customer:
            return Response(
                {"detail": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
