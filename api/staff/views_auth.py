from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import StaffToken
from .serializers import StaffAuthTokenSerializer, StaffSerializer
from .authentication import StaffTokenAuthentication


class StaffLoginView(APIView):
    """
    API endpoint for staff login.
    
    ## Request Body
    - `username`: Staff username (required)
    - `password`: Staff password (required)
    
    ## Response
    - `token`: Authentication token
    - `user`: Staff user data
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Authenticate staff and get token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Staff username', example='admin'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Staff password', format='password', example='yourpassword'),
            },
            example={
                'username': 'admin',
                'password': 'yourpassword'
            }
        ),
        responses={
            200: openapi.Response(
                description="Successful authentication",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'staff_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'phone': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        )
                    }
                )
            ),
            400: 'Invalid input',
            401: 'Invalid credentials',
        }
    )
    def post(self, request, *args, **kwargs):
        print("Login attempt with data:", request.data)
        serializer = StaffAuthTokenSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            staff = serializer.validated_data['user']
            
            # Create or get token using our custom StaffToken model
            token, created = StaffToken.objects.get_or_create(staff=staff)
            
            # If token exists but is expired, create a new one
            if not created and token.is_expired():
                token.delete()
                token = StaffToken.objects.create(staff=staff)
                
            user_serializer = StaffSerializer(staff)
            return Response({
                'token': token.key,
                'user': user_serializer.data,
                'expires': token.expires
            })
            
        except Exception as e:
            print("Login error:", str(e))
            return Response(
                {'error': 'An error occurred during login'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StaffLogoutView(APIView):
    """
    API endpoint for staff logout.
    
    ## Authentication
    Requires a valid authentication token in the header:
    ```
    Authorization: Token <token>
    ```
    """
    authentication_classes = [StaffTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Logout staff by deleting the authentication token",
        responses={
            200: 'Successfully logged out',
            401: 'Unauthorized - Invalid or expired token',
        },
        security=[{'Token': []}]
    )
    def post(self, request):
        try:
            # Get the token from the request header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
            if len(auth_header) == 2 and auth_header[0].lower() == 'token':
                token_key = auth_header[1]
                try:
                    token = StaffToken.objects.get(key=token_key)
                    token.delete()
                    return Response(
                        {'detail': 'Successfully logged out.'}, 
                        status=status.HTTP_200_OK
                    )
                except StaffToken.DoesNotExist:
                    return Response(
                        {'error': 'Invalid token'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return Response(
                {'error': 'Authentication credentials were not provided.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        except Exception as e:
            print("Logout error:", str(e))
            return Response(
                {'error': 'An error occurred during logout'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StaffProfileView(APIView):
    """
    API endpoint to get the profile of the currently authenticated staff member.
    
    ## Authentication
    Requires a valid authentication token in the header:
    ```
    Authorization: Token <token>
    ```
    """
    authentication_classes = [StaffTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get the profile of the currently authenticated staff member",
        responses={
            200: StaffSerializer(),
            401: 'Unauthorized - Invalid or expired token',
        },
        security=[{'Token': []}]
    )
    def get(self, request):
        try:
            # The StaffTokenAuthentication already verifies the token and sets request.user
            serializer = StaffSerializer(request.user)
            return Response(serializer.data)
            
        except Exception as e:
            print("Profile view error:", str(e))
            return Response(
                {'error': 'An error occurred while fetching profile'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
