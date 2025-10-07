from drf_yasg import openapi

# Common responses
error_response = openapi.Response(
    description='Error response',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'error': openapi.Schema(type=openapi.TYPE_STRING),
            'details': openapi.Schema(type=openapi.TYPE_OBJECT, additional_properties=True)
        }
    )
)

# Register
register_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'password', 'first_name', 'last_name'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
        'phone': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
    }
)

register_response = {
    201: openapi.Response(
        description='User registered successfully',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        )
    ),
    400: error_response
}

# Login
login_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'password'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, format='password')
    }
)

login_response = {
    200: openapi.Response(
        description='Login successful',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING),
                'user': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            }
        )
    ),
    400: error_response,
    401: openapi.Response(
        description='Invalid credentials',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    )
}

# User Profile
user_profile_response = {
    200: openapi.Response(
        description='User profile',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'is_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        )
    ),
    401: openapi.Response(
        description='Authentication credentials were not provided',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    )
}

# Password Reset
password_reset_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email')
    }
)

password_reset_confirm_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['token', 'new_password'],
    properties={
        'token': openapi.Schema(type=openapi.TYPE_STRING),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING, format='password')
    }
)

password_reset_response = {
    200: openapi.Response(
        description='Password reset successful',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    ),
    400: error_response
}
