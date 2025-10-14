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
    required=['email', 'password', 'user_name'],
    properties={
        'user_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Unique username for the customer account"
        ),
        'email': openapi.Schema(
            type=openapi.TYPE_STRING, 
            format='email',
            description="Customer's email address"
        ),
        'password': openapi.Schema(
            type=openapi.TYPE_STRING, 
            format='password',
            min_length=8,
            description="Account password (min 8 characters)"
        ),
        'first_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Customer's first name"
        ),
        'last_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Customer's last name"
        ),
        'phone': openapi.Schema(
            type=openapi.TYPE_STRING, 
            nullable=True,
            description="Customer's phone number (optional)"
        ),
        'street': openapi.Schema(
            type=openapi.TYPE_STRING,
            nullable=True,
            description="Street address (optional)"
        ),
        'city': openapi.Schema(
            type=openapi.TYPE_STRING,
            nullable=True,
            description="City (optional)"
        ),
        'state': openapi.Schema(
            type=openapi.TYPE_STRING,
            nullable=True,
            description="State/Province (optional)"
        ),
        'zip_code': openapi.Schema(
            type=openapi.TYPE_STRING,
            nullable=True,
            description="ZIP/Postal code (optional)"
        )
    }
)

register_response = {
    201: openapi.Response(
        description='Customer registered successfully',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'customer_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Unique identifier for the customer'),
                'user_name': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the registered customer'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the customer'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the customer'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Email address of the customer'),
                'is_email_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the email has been verified'),
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Status message')
            }
        ),
        examples={
            'application/json': {
                'customer_id': 1,
                'user_name': 'johndoe',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'is_email_verified': False,
                'detail': 'Registered. Please check your email to confirm.'
            }
        }
    ),
    400: openapi.Response(
        description='Bad Request',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
            }
        ),
        examples={
            'application/json': {
                'detail': 'user_name is required',
                'detail': 'email already in use',
                'detail': 'user_name already exists'
            }
        }
    )
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
    required=['token', 'confirm_password', 'new_password'],
    properties={
        'token': openapi.Schema(type=openapi.TYPE_STRING),
        'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
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

# Update Profile
update_profile_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Customer's first name"),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Customer's last name"),
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description="New email address"),
        'phone': openapi.Schema(type=openapi.TYPE_STRING, description="Phone number"),
        'street': openapi.Schema(type=openapi.TYPE_STRING, description="Street address"),
        'city': openapi.Schema(type=openapi.TYPE_STRING, description="City"),
        'state': openapi.Schema(type=openapi.TYPE_STRING, description="State/Province"),
        'zip_code': openapi.Schema(type=openapi.TYPE_STRING, description="ZIP/Postal code")
    }
)

# Update Password
update_password_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['current_password', 'new_password'],
    properties={
        'current_password': openapi.Schema(
            type=openapi.TYPE_STRING, 
            format='password', 
            description="Current password for verification"
        ),
        'new_password': openapi.Schema(
            type=openapi.TYPE_STRING, 
            format='password', 
            description="New password (min 8 characters, at least 1 letter and 1 number)",
            min_length=8
        )
    }
)
