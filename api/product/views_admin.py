from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from ..core.decorators import staff_required
from .models import Product
from .schema import (
    product_list_get_schema, product_create_schema,
    product_retrieve_schema, product_update_schema, product_delete_schema,
    product_name_query, brand_id_query, category_id_query
)

# Using the centralized staff_required decorator from core.decorators

def _get_paginated_response(queryset, request):
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 10)
    show_deleted = request.query_params.get('show_deleted', '').lower() == 'true'
    
    try:
        page = int(page)
        page_size = int(page_size)
        page_size = min(100, page_size)  # Limit page size to 100
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    # Only show non-deleted items by default
    if not show_deleted:
        queryset = queryset.filter(deleted_at__isnull=True)
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return {
        'count': paginator.count,
        'next': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'results': list(page_obj.object_list.values(
            'product_id', 'product_name',
            'brand__brand_name', 'category__category_name',
            'model_year', 'list_price', 'created_at', 'updated_at', 'deleted_at'
        ))
    }

@product_list_get_schema
@product_create_schema
@api_view(['GET', 'POST'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
@staff_required()
def product_admin_list(request):
    if request.method == 'GET':
        # Handle GET request - List products (non-deleted by default)
        queryset = Product.active_objects.select_related('brand', 'category').all()
        
        # Apply filters
        name = request.query_params.get('name')
        brand_id = request.query_params.get('brand_id')
        category_id = request.query_params.get('category_id')
        show_deleted = request.query_params.get('show_deleted', '').lower() == 'true'
        
        # If showing deleted items, use the default manager
        if show_deleted:
            queryset = Product.objects.select_related('brand', 'category').all()
        
        if name:
            queryset = queryset.filter(product_name__icontains=name)
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Order and paginate
        queryset = queryset.order_by('-product_id')
        paginated_data = _get_paginated_response(queryset, request)
        return Response(paginated_data)
        
    elif request.method == 'POST':
        # Handle POST request - Create product
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data
        
        # Validate required fields
        required_fields = ['product_name', 'model_year', 'list_price']
        for field in required_fields:
            if field not in data:
                return Response(
                    {"status": "error", "message": f"{field} is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Check if product with same name exists (including soft-deleted)
            existing = Product.objects.filter(
                product_name__iexact=data['product_name'].strip(),
                deleted_at__isnull=False
            ).first()
            
            if existing:
                # Restore the soft-deleted product
                existing.deleted_at = None
                existing.model_year = data['model_year']
                existing.list_price = data['list_price']
                existing.brand_id = data.get('brand_id')
                existing.category_id = data.get('category_id')
                existing.save()
                product = existing
            else:
                # Create new product
                product = Product.objects.create(
                    product_name=data['product_name'].strip(),
                    brand_id=data.get('brand_id'),
                    category_id=data.get('category_id'),
                    model_year=data['model_year'],
                    list_price=data['list_price']
                )
            
            # Prepare response
            response_data = {
                'product_id': product.product_id,
                'product_name': product.product_name,
                'brand': {
                    'id': product.brand_id,
                    'name': product.brand.brand_name if product.brand else None
                } if product.brand_id else None,
                'category': {
                    'id': product.category_id,
                    'name': product.category.category_name if product.category else None
                } if product.category_id else None,
                'model_year': product.model_year,
                'list_price': str(product.list_price),
                'created_at': product.created_at,
                'updated_at': product.updated_at,
                'deleted_at': product.deleted_at
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@product_retrieve_schema
@product_update_schema
@product_delete_schema
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
@staff_required()
def product_admin_detail(request, id):
    # Get product including soft-deleted ones
    product = get_object_or_404(Product.objects.all(), pk=id)
    
    if request.method == 'GET':
        # Handle GET request - Get product details
        response_data = {
            'product_id': product.product_id,
            'product_name': product.product_name,
            'brand': {
                'id': product.brand_id,
                'name': product.brand.brand_name if product.brand else None
            } if product.brand_id else None,
            'category': {
                'id': product.category_id,
                'name': product.category.category_name if product.category else None
            } if product.category_id else None,
            'model_year': product.model_year,
            'list_price': str(product.list_price),
            'created_at': product.created_at,
            'updated_at': product.updated_at,
            'deleted_at': product.deleted_at
        }
        return Response(response_data)
        
    elif request.method in ['PUT', 'PATCH']:
        # Check if product is soft-deleted
        if product.deleted_at:
            return Response(
                {"status": "error", "message": "Cannot update a deleted product"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Handle PUT/PATCH request - Update product
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data
        
        try:
            # Update fields
            if 'product_name' in data:
                product.product_name = data['product_name'].strip()
                
                # Check for duplicate name (case-insensitive)
                if Product.objects.filter(
                    product_name__iexact=product.product_name,
                    deleted_at__isnull=True
                ).exclude(pk=product.pk).exists():
                    return Response(
                        {"status": "error", "message": "Product with this name already exists"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            if 'brand_id' in data:
                product.brand_id = data['brand_id'] or None
            if 'category_id' in data:
                product.category_id = data['category_id'] or None
            if 'model_year' in data:
                product.model_year = data['model_year']
            if 'list_price' in data:
                product.list_price = data['list_price']
                
            product.save()
            
            # Prepare response
            response_data = {
                'product_id': product.product_id,
                'product_name': product.product_name,
                'brand': {
                    'id': product.brand_id,
                    'name': product.brand.brand_name if product.brand else None
                } if product.brand_id else None,
                'category': {
                    'id': product.category_id,
                    'name': product.category.category_name if product.category else None
                } if product.category_id else None,
                'model_year': product.model_year,
                'list_price': str(product.list_price),
                'created_at': product.created_at,
                'updated_at': product.updated_at,
                'deleted_at': product.deleted_at
            }
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    elif request.method == 'DELETE':
        # Check if already deleted
        if product.deleted_at:
            return Response(
                {"status": "error", "message": "Product is already deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Handle DELETE request - Soft delete product
        try:
            product.deleted_at = timezone.now()
            product.save()
            return Response(
                {
                    "status": "success", 
                    "message": "Product deleted successfully",
                    "deleted_at": product.deleted_at
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
