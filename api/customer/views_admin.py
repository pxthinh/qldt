from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q

from api.customer.models import Customer
from api.customer.serializers import CustomerSerializer
from api.core.decorators import staff_required

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
                description="Search by user_name, email, or name",
                type=openapi.TYPE_STRING
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

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user_name__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        serializer = CustomerSerializer(queryset[start:end], many=True)
        return Response({
            'count': len(queryset),
            'next': f"?page={page + 1}&page_size={page_size}" if end < len(queryset) else None,
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
        user_name = request.data.get('user_name')
        
        # Check if a customer with this username already exists
        if user_name and Customer.objects.filter(user_name=user_name).exists():
            return Response(
                {'user_name': 'A customer with this username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(staff_required(), name='dispatch')
class CustomerAdminDetail(APIView):

    def get_object(self, pk):
        try:
            return Customer.objects.get(customer_id=pk)
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
            
        # Check if the username is being updated and if it's already taken
        new_username = request.data.get('user_name')
        if new_username and new_username != customer.user_name:
            if Customer.objects.filter(user_name=new_username).exists():
                return Response(
                    {'user_name': 'A customer with this username already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
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
