import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from .models import Category
from .schema import (
    category_list_get_schema, category_create_schema,
    category_retrieve_schema, category_update_schema, category_delete_schema,
    category_name_query
)
from repository.category_repository import list_categories

def _get_paginated_response(queryset, request):
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 10)

    try:
        page = int(page)
        page_size = int(page_size)
        page_size = min(100, page_size)  # Limit page size to 100
    except (ValueError, TypeError):
        page = 1
        page_size = 10

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    return {
        'count': paginator.count,
        'next': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'results': list(page_obj.object_list.values(
            'category_id', 'category_name', 'created_at', 'updated_at'
        ))
    }

@category_list_get_schema
@category_create_schema
@api_view(['GET', 'POST'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
def category_admin_list(request):
    if request.method == 'GET':
        # Handle GET request - List categories
        show_deleted = request.query_params.get('show_deleted', '').lower() == 'true'
        sort_order = request.query_params.get('sort', '-created_at')
        
        # Validate sort order
        if sort_order not in ['-created_at', 'created_at']:
            sort_order = '-created_at'
        
        # Use active_objects manager by default, or all objects if show_deleted is True
        queryset = Category.objects.all() if show_deleted else Category.active_objects.all()

        # Apply filters
        name = request.query_params.get('name')
        if name:
            queryset = queryset.filter(category_name__icontains=name)

        # Order and paginate
        queryset = queryset.order_by(sort_order)
        
        # Include deleted_at in the response if showing deleted items
        fields = ['category_id', 'category_name', 'created_at', 'updated_at']
        if show_deleted:
            fields.append('deleted_at')
            
        paginated_data = _get_paginated_response(queryset, request)
        
        # Add sort information to response
        paginated_data['sort'] = sort_order
        
        return Response(paginated_data)
        
    elif request.method == 'POST':
        # Handle POST request - Create category
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data
        
        # Validate required fields
        if 'category_name' not in data or not data['category_name'].strip():
            return Response(
                {"status": "error", "message": "category_name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if category with same name already exists
            if Category.objects.filter(category_name__iexact=data['category_name'].strip()).exists():
                return Response(
                    {"status": "error", "message": "A category with this name already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Create category
            category = Category.objects.create(
                category_name=data['category_name'].strip(),
            )
            
            # Prepare response
            response_data = {
                'category_id': category.category_id,
                'category_name': category.category_name,
                'created_at': category.created_at,
                'updated_at': category.updated_at
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@category_retrieve_schema
@category_update_schema
@category_delete_schema
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
def category_admin_detail(request, id):
    try:
        category = Category.objects.get(pk=id)
    except Category.DoesNotExist:
        return Response(
            {"status": "error", "message": "Category not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        # Handle GET request - Retrieve category
        response_data = {
            'category_id': category.category_id,
            'category_name': category.category_name,
            'created_at': category.created_at,
            'updated_at': category.updated_at
        }
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Handle PUT/PATCH request - Update category
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data
        
        # Validate required fields
        if 'category_name' not in data or not data['category_name'].strip():
            return Response(
                {"status": "error", "message": "category_name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if another category with the same name already exists
        if Category.objects.filter(
            ~Q(pk=category.category_id),
            category_name__iexact=data['category_name'].strip()
        ).exists():
            return Response(
                {"status": "error", "message": "A category with this name already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update category
        category.category_name = data['category_name'].strip()
        category.save()
        
        # Prepare response
        response_data = {
            'category_id': category.category_id,
            'category_name': category.category_name,
            'created_at': category.created_at,
            'updated_at': category.updated_at
        }
        
        return Response(response_data)
    
    elif request.method == 'DELETE':
        # Handle DELETE request - Soft delete category
        if category.deleted_at:
            return Response(
                {"status": "error", "message": "Category is already deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        category.delete()  # This will perform a soft delete (sets deleted_at)
        return Response(
            {"status": "success", "message": "Category deleted successfully"},
            status=status.HTTP_200_OK
        )

    # This should never be reached as all methods are handled above
    return Response(
        {"status": "error", "message": "Method not allowed"},
        status=status.HTTP_405_METHOD_NOT_ALLOWED
    )
