import json, time, hashlib
from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Customer, RevokedAuthToken
from .schemas import login_request, login_response, user_profile_response, update_profile_request, update_password_request
from .authentication import CustomerTokenAuthentication

AUTH_SALT = "customer-auth-token"
AUTH_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}

def _issue_token(customer_id: int) -> str:
    return signing.dumps({"id": customer_id, "iat": int(time.time())}, salt=AUTH_SALT)

def _get_bearer_token(request) -> str | None:
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()

def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def _customer_from_token(request):
    token = _get_bearer_token(request)
    if not token:
        return None, JsonResponse({"detail": "Missing Bearer token"}, status=401)

    fp = _token_fingerprint(token)
    if RevokedAuthToken.objects.filter(fingerprint=fp, expires_at__gt=timezone.now()).exists():
        return None, JsonResponse({"detail": "Token revoked"}, status=401)

    try:
        data = signing.loads(token, salt=AUTH_SALT, max_age=AUTH_MAX_AGE)
        obj = Customer.objects.get(pk=data.get("id"))
        return obj, None
    except signing.SignatureExpired:
        return None, JsonResponse({"detail": "Token expired"}, status=401)
    except (signing.BadSignature, Customer.DoesNotExist):
        return None, JsonResponse({"detail": "Invalid token"}, status=401)

class CustomerLoginView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        tags=['Auth Customer'],
        operation_summary="Customer Login",
        operation_description="Authenticate customer and get access token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_name', 'password'],
            properties={
                'user_name': openapi.Schema(type=openapi.TYPE_STRING, description='Customer username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Customer password', format='password')
            },
            example={
                'user_name': 'customer1',
                'password': 'yourpassword123'
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT token for authentication'),
                        'expires_in': openapi.Schema(type=openapi.TYPE_INTEGER, description='Token expiration time in seconds'),
                        'customer': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                                'street': openapi.Schema(type=openapi.TYPE_STRING),
                                'city': openapi.Schema(type=openapi.TYPE_STRING),
                                'state': openapi.Schema(type=openapi.TYPE_STRING),
                                'zip_code': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            400: 'Invalid input',
            401: 'Invalid credentials',
            403: 'Account is not active'
        }
    )
    
    def post(self, request, *args, **kwargs):
        data = request.data
        user_name = (data.get("user_name") or "").strip()
        password = (data.get("password") or "").strip()

        if not user_name or not password:
            return Response(
                {"detail": "user_name and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            obj = Customer.objects.get(user_name=user_name)
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not obj.check_password(password):
            return Response(
                {"detail": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not obj.is_email_verified:
            return Response(
                {"detail": "Account is not active"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        token = _issue_token(obj.customer_id)
        return Response({
            "token": token,
            "expires_in": AUTH_MAX_AGE,
            "customer": {
                "customer_id": obj.customer_id,
                "user_name": obj.user_name,
                "first_name": obj.first_name,
                "last_name": obj.last_name,
                "email": obj.email,
                "phone": obj.phone,
                "street": obj.street,
                "city": obj.city,
                "state": obj.state,
                "zip_code": obj.zip_code,
            }
        }, status=status.HTTP_200_OK)

class CustomerProfileView(APIView):
    authentication_classes = [CustomerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Auth Customer'],
        operation_summary="Get Profile",
        operation_description="Get current customer profile",
        responses={
            200: openapi.Response(
               description="Customer profile",
               schema=openapi.Schema(
                   type=openapi.TYPE_OBJECT,
                   properties={
                       'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                       'user_name': openapi.Schema(type=openapi.TYPE_STRING),
                       'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                       'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                       'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                       'phone': openapi.Schema(type=openapi.TYPE_STRING),
                       'street': openapi.Schema(type=openapi.TYPE_STRING),
                       'city': openapi.Schema(type=openapi.TYPE_STRING),
                       'state': openapi.Schema(type=openapi.TYPE_STRING),
                       'zip_code': openapi.Schema(type=openapi.TYPE_STRING),
                       'is_email_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                       'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                       'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                   }
               )
           ),
           401: 'Authentication credentials were not provided or invalid.',
           403: 'Authentication failed.'
        },
        security=[{'Bearer': []}]
    )
    
    def get(self, request, *args, **kwargs):
        customer = request.user
        return Response({
            "customer_id": customer.customer_id,
            "user_name": customer.user_name,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "phone": customer.phone,
            "street": customer.street,
            "city": customer.city,
            "state": customer.state,
            "zip_code": customer.zip_code,
            "is_email_verified": customer.is_email_verified,
        })

class CustomerLogoutView(APIView):
    authentication_classes = [CustomerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Auth Customer'],
        operation_summary="Customer Logout",
        operation_description="Logout the currently authenticated customer.",
        responses={
            200: openapi.Response(
                description="Successfully logged out",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example='Successfully logged out')
                    }
                )
            ),
            400: 'Bad request',
            401: 'Authentication credentials were not provided or invalid.',
            403: 'Authentication failed.'
        },
        security=[{'Bearer': []}]
    )
    
    def post(self, request, *args, **kwargs):
        token = _get_bearer_token(request)
        if not token:
            return Response(
                {"detail": "No authentication token provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Create a record of the revoked token
            fp = _token_fingerprint(token)
            expires_at = timezone.now() + timedelta(seconds=AUTH_MAX_AGE)
            
            # Check if this token is already revoked
            if not RevokedAuthToken.objects.filter(fingerprint=fp).exists():
                RevokedAuthToken.objects.create(
                    fingerprint=fp,
                    expires_at=expires_at
                )
                
            # Invalidate the session
            request.session.flush()
            
            return Response(
                {"detail": "Successfully logged out"}, 
                status=status.HTTP_200_OK
            )
            
        except signing.SignatureExpired:
            # If token is expired, still add it to revocation list
            fp = _token_fingerprint(token)
            expires_at = timezone.now() + timedelta(seconds=AUTH_MAX_AGE)
            RevokedAuthToken.objects.create(
                fingerprint=fp,
                expires_at=expires_at
            )
            return Response(
                {"detail": "Token already expired"}, 
                status=status.HTTP_200_OK
            )
            
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid token"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )


class CustomerUpdateProfileView(APIView):
    authentication_classes = [CustomerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Customer'],
        operation_summary="Update Profile",
        operation_description="Update customer profile information",
        request_body=update_profile_request,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                        'customer': user_profile_response
                    },
                    example={
                        'detail': 'Profile updated successfully',
                        'customer': {
                            'customer_id': 1,
                            'user_name': 'johndoe',
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'email': 'john@example.com',
                            'is_email_verified': True
                        }
                    }
                )
            ),
            400: 'Invalid data'
        },
        security=[{'Bearer': []}]
    )
    
    def put(self, request, *args, **kwargs):
        customer = request.user
        data = request.data
        
        # Update fields if they are provided in the request
        if 'first_name' in data:
            customer.first_name = data['first_name'].strip()
        if 'last_name' in data:
            customer.last_name = data['last_name'].strip()
        if 'email' in data and data['email'].strip().lower() != customer.email:
            new_email = data['email'].strip().lower()
            if Customer.objects.filter(email__iexact=new_email).exists():
                return Response(
                    {"detail": "Email already in use"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            customer.email = new_email
            customer.is_email_verified = False
            # TODO: Send verification email for the new email
        if 'phone' in data:
            customer.phone = data['phone'].strip()
        if 'street' in data:
            customer.street = data['street']
        if 'city' in data:
            customer.city = data['city']
        if 'state' in data:
            customer.state = data['state']
        if 'zip_code' in data:
            customer.zip_code = data['zip_code']
        
        customer.save()
        
        return Response({
            'detail': 'Profile updated successfully',
            'customer': {
                'customer_id': customer.customer_id,
                'user_name': customer.user_name,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'email': customer.email,
                'is_email_verified': customer.is_email_verified,
                'phone': customer.phone,
                'street': customer.street,
                'city': customer.city,
                'state': customer.state,
                'zip_code': customer.zip_code
            }
        }, status=status.HTTP_200_OK)


class CustomerUpdatePasswordView(APIView):
    authentication_classes = [CustomerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=['Customer'],
        operation_summary="Update Password",
        operation_description="Update customer password",
        request_body=update_password_request,
        responses={
            200: openapi.Response(
                description="Password updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    },
                    example={
                        'detail': 'Password updated successfully'
                    }
                )
            ),
            400: 'Invalid current password or new password does not meet requirements'
        },
        security=[{'Bearer': []}]
    )
    
    def put(self, request, *args, **kwargs):
        customer = request.user
        data = request.data
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return Response(
                {"detail": "Both current_password and new_password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify current password
        if not customer.check_password(current_password):
            return Response(
                {"detail": "Current password is incorrect"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if new password is different from current password
        if current_password == new_password:
            return Response(
                {"detail": "New password must be different from current password"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update password
        customer.set_password(new_password)
        customer.save()
        
        # Invalidate all existing tokens
        RevokedAuthToken.objects.filter(
            fingerprint__startswith=f"{customer.customer_id}:"
        ).delete()
        
        return Response(
            {"detail": "Password updated successfully"}, 
            status=status.HTTP_200_OK
        )
