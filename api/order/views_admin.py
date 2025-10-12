from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import status
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer
from .schema import (
    order_status_query, date_after_query, date_before_query,
    order_create_request, order_update_request,
    order_detail_response, order_list_response, order_id_param
)


def _staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))


@swagger_auto_schema(
    method='get',
    operation_id="order_list",
    manual_parameters=[order_status_query, date_after_query, date_before_query],
    responses={
        status.HTTP_200_OK: order_list_response,
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "Bad Request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    security=[{"Bearer": []}],
    tags=['Admin Orders'],
    operation_summary='List Orders (Admin)',
    operation_description='Returns a list of all orders, optionally filtered by status and date range.'
)
@swagger_auto_schema(
    method='post',
    operation_id="order_create",
    request_body=order_create_request,
    responses={
        status.HTTP_201_CREATED: order_detail_response,
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            "Bad Request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    security=[{"Bearer": []}],
    tags=['Admin Orders'],
    operation_summary='Create Order (Admin)',
    operation_description='Create a new order with the provided data.'
)
@api_view(['GET', 'POST'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
@_staff_required
def order_admin_list(request):
    """
    Handle GET and POST requests for the admin orders endpoint.
    """
    if request.method == 'GET':
        try:
            qs = Order.objects.all()
            
            # Apply filters
            status_filter = request.query_params.get('status')
            if status_filter:
                statuses = [s.strip().lower() for s in status_filter.split(',')]
                qs = qs.filter(status__in=statuses)
                
            date_after = request.query_params.get('date_after')
            if date_after:
                qs = qs.filter(created_at__gte=date_after)
                
            date_before = request.query_params.get('date_before')
            if date_before:
                qs = qs.filter(created_at__lte=date_before)
            
            serializer = OrderSerializer(qs.order_by("-created_at"), many=True)
            return Response({
                'count': qs.count(),
                'next': None,
                'previous': None,
                'results': serializer.data
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'POST':
        try:
            data = request.data
            if hasattr(data, 'dict'):  # Handle QueryDict from form data
                data = data.dict()
                
            serializer = OrderCreateSerializer(data=data)
            if serializer.is_valid():
                order = serializer.save()
                return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
                
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_id="order_retrieve",
    manual_parameters=[order_id_param],
    responses={
        status.HTTP_200_OK: order_detail_response,
        status.HTTP_404_NOT_FOUND: 'Order not found',
        status.HTTP_401_UNAUTHORIZED: 'Unauthorized',
        status.HTTP_403_FORBIDDEN: 'Forbidden',
    },
    security=[[{"Bearer": []}]],
    tags=['Admin Orders'],
    operation_summary='Retrieve Order (Admin)',
    operation_description='Retrieve details of a specific order by ID.'
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    operation_id="order_update",
    manual_parameters=[order_id_param],
    request_body=order_update_request,
    responses={
        status.HTTP_200_OK: order_detail_response,
        status.HTTP_400_BAD_REQUEST: 'Invalid input',
        status.HTTP_404_NOT_FOUND: 'Order not found',
        status.HTTP_401_UNAUTHORIZED: 'Unauthorized',
        status.HTTP_403_FORBIDDEN: 'Forbidden',
    },
    security=[[{"Bearer": []}]],
    tags=['Admin Orders'],
    operation_summary='Update Order (Admin)',
    operation_description='Update an order by ID.'
)
@swagger_auto_schema(
    method='delete',
    operation_id="order_delete",
    manual_parameters=[order_id_param],
    responses={
        status.HTTP_204_NO_CONTENT: 'Order successfully deleted',
        status.HTTP_404_NOT_FOUND: 'Order not found',
        status.HTTP_401_UNAUTHORIZED: 'Unauthorized',
        status.HTTP_403_FORBIDDEN: 'Forbidden',
    },
    security=[[{"Bearer": []}]],
    tags=['Admin Orders'],
    operation_summary='Delete Order (Admin)',
    operation_description='Delete an order by ID.'
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
@_staff_required
def order_admin_detail(request, id):
    """
    Handle GET, PUT, PATCH, and DELETE requests for a specific order.
    """
    try:
        order = Order.objects.get(pk=id)
    except Order.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        try:
            partial = request.method == 'PATCH'
            serializer = OrderUpdateSerializer(order, data=request.data, partial=partial)
            if serializer.is_valid():
                updated_order = serializer.save()
                return Response(OrderSerializer(updated_order).data)
                
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# Additional endpoints for order items and status can be added as separate function-based views
# following the same pattern as above, using @api_view and @swagger_auto_schema decorators