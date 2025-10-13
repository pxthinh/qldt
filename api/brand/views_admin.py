from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from ..core.decorators import staff_required
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import status
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import Brand
from .schema import (
    brand_name_query, brand_list_response, brand_post_request_body,
    brand_response, brand_id_param
)


# Using the centralized staff_required decorator from core.decorators

@swagger_auto_schema(
    method='get',
    operation_id="brand_list",
    manual_parameters=[brand_name_query],
    responses={status.HTTP_200_OK: brand_list_response},
    security=[{"Bearer": []}],
    tags=['Admin Brands'],
    operation_summary='List Brands (Admin)',
    operation_description='Returns a list of all brands, optionally filtered by name.'
)
@swagger_auto_schema(
    method='post',
    operation_id="brand_create",
    request_body=brand_post_request_body,
    responses={
        status.HTTP_201_CREATED: brand_response,
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
    tags=['Admin Brands'],
    operation_summary='Create Brand (Admin)',
    operation_description='Create a new brand by providing brand_name.'
)
@api_view(['GET', 'POST'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
@staff_required()
def brand_admin_list(request):
    if request.method == 'GET':
        # GET method - List all brands
        q = request.GET.get("name")
        qs = Brand.active_objects.all()
        if q:
            qs = qs.filter(brand_name__icontains=q)
        data = list(qs.order_by("-created_at").values(
            "brand_id", "brand_name", "created_at", "updated_at"
        ))
        return Response(data)
    
    elif request.method == 'POST':
        # POST method - Create a new brand
        try:
            # Get data from request
            data = request.data
            if hasattr(data, 'dict'):  # Handle QueryDict from form data
                data = data.dict()
            
            brand_name = data.get('brand_name')
            
            if not brand_name:
                return Response({
                    "status": "error",
                    "message": "brand_name is required"
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if Brand.objects.filter(brand_name__iexact=brand_name).exists():
                return Response({
                    "status": "error",
                    "message": f"Brand with name '{brand_name}' already exists"
                }, status=status.HTTP_400_BAD_REQUEST)
                
            brand = Brand.objects.create(
                brand_name=brand_name,
                created_at=now(),
                updated_at=now()
            )
            
            return Response({
                "status": "success",
                "message": "Brand created successfully",
                "data": {
                    "brand_id": brand.brand_id,
                    "brand_name": brand.brand_name,
                    "created_at": brand.created_at,
                    "updated_at": brand.updated_at
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to create brand: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_id="brand_retrieve",
    manual_parameters=[brand_id_param],
    responses={
        status.HTTP_200_OK: brand_response,
        status.HTTP_404_NOT_FOUND: 'Brand not found'
    },
    security=[{"Bearer": []}],
    tags=['Admin Brands'],
    operation_summary='Retrieve Brand (Admin)',
    operation_description='Retrieve details of a specific brand by ID.'
)
@swagger_auto_schema(
    methods=['put', 'patch'],
    operation_id="brand_update",
    manual_parameters=[brand_id_param],
    request_body=brand_post_request_body,
    responses={
        status.HTTP_200_OK: brand_response,
        status.HTTP_400_BAD_REQUEST: 'Invalid input',
        status.HTTP_404_NOT_FOUND: 'Brand not found',
    },
    security=[{"Bearer": []}],
    tags=['Admin Brands'],
    operation_summary='Update Brand (Admin)',
    operation_description='Update a brand by ID.'
)
@swagger_auto_schema(
    method='delete',
    operation_id="brand_delete",
    manual_parameters=[brand_id_param],
    responses={
        status.HTTP_204_NO_CONTENT: 'Brand successfully deleted',
        status.HTTP_404_NOT_FOUND: 'Brand not found',
    },
    security=[{"Bearer": []}],
    tags=['Admin Brands'],
    operation_summary='Delete Brand (Admin)',
    operation_description='Delete a brand by ID.'
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
@csrf_exempt
@staff_required
def brand_admin_detail(request, id: int):
    try:
        obj = Brand.objects.get(pk=id, deleted_at__isnull=True)
    except Brand.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)

    if request.method == "GET":
        return Response({
            "brand_id": obj.brand_id,
            "brand_name": obj.brand_name,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at
        })

    if request.method in ("PUT", "PATCH"):
        try:
            # Get data from request
            data = request.data
            if hasattr(data, 'dict'):  # Handle QueryDict from form data
                data = data.dict()

            if not data or 'brand_name' not in data:
                return Response(
                    {
                        "status": "error",
                        "message": "brand_name is required in request body",
                        "example": {"brand_name": "Your Brand Name"}
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            name = data['brand_name'].strip() if isinstance(data['brand_name'], str) else str(data['brand_name']).strip()

            if not name:
                return Response(
                    {"status": "error", "message": "brand_name cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Brand.objects.exclude(pk=obj.pk).filter(brand_name__iexact=name).exists():
                return Response(
                    {"status": "error", "message": f"Brand with name '{name}' already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update the brand
            obj.brand_name = name
            obj.updated_at = now()
            obj.save()

            return Response({
                "status": "success",
                "message": "Brand updated successfully",
                "data": {
                    "brand_id": obj.brand_id,
                    "brand_name": obj.brand_name,
                    "created_at": obj.created_at,
                    "updated_at": obj.updated_at
                }
            })

        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to update brand: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        obj.brand_name = name
        obj.updated_at = now()
        obj.save()
        return Response({
            "brand_id": obj.brand_id,
            "brand_name": obj.brand_name,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at
        })

    if request.method == "DELETE":
        # Check if brand is already deleted
        if obj.deleted_at:
            return Response(
                {"status": "error", "message": "Brand is already deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Perform soft delete
        obj.delete()
        return Response(
            {"status": "success", "message": "Brand deleted successfully"},
            status=status.HTTP_200_OK
        )

    return HttpResponseNotAllowed(["GET", "PUT", "PATCH", "DELETE"])
