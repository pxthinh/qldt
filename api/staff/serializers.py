from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext_lazy as _
from .models import Staff
from django.core.exceptions import ValidationError

class StaffAuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not (username and password):
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        print(f"Attempting to find staff with username: {username}")
        
        try:
            # Get the staff by username (case-insensitive)
            staff = Staff.objects.get(username__iexact=username)
            print(f"Found staff: {staff}")
            
            # Check if password_hash exists
            if not staff.password_hash:
                print("No password set for this user")
                msg = _('No password set for this account. Please reset your password.')
                raise serializers.ValidationError(msg, code='authorization')
            
            # Check password using the model's check_password method
            if not staff.check_password(password):
                print("Password check failed")
                msg = _('Invalid username or password.')
                raise serializers.ValidationError(msg, code='authorization')
                
            if not staff.is_active:
                msg = _('Staff account is disabled.')
                print(f"Account disabled for user: {username}")
                raise serializers.ValidationError(msg, code='authorization')
                
        except Staff.DoesNotExist:
            print(f"No staff found with username: {username}")
            msg = _('Invalid username or password.')
            raise serializers.ValidationError(msg, code='authorization')
            
        except Exception as e:
            print(f"Unexpected error during authentication: {str(e)}")
            msg = _('An error occurred during authentication. Please try again.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = staff
        return attrs


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('staff_id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                 'is_active', 'created_at', 'updated_at', 'store_id', 'manager_id')
        read_only_fields = ('staff_id', 'created_at', 'updated_at')


class StoreCreateSerializer(serializers.Serializer):
    store_name = serializers.CharField(required=True, help_text="Name of the store")
    phone = serializers.CharField(required=False, allow_blank=True, help_text="Store contact number")
    email = serializers.EmailField(required=False, allow_blank=True, help_text="Store email address")
    street = serializers.CharField(required=False, allow_blank=True, help_text="Street address")
    city = serializers.CharField(required=False, allow_blank=True, help_text="City")
    state = serializers.CharField(required=False, allow_blank=True, max_length=10, help_text="State/Province code")
    zip_code = serializers.CharField(required=False, allow_blank=True, max_length=10, help_text="ZIP/Postal code")

    class Meta:
        swagger_schema_fields = {
            'example': {
                "store_name": "Main Store",
                "email": "main@example.com",
                "phone": "123-456-7890",
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001"
            }
        }

    def validate(self, attrs):
        if not attrs.get('store_name'):
            raise serializers.ValidationError("store_name is required when creating a new store")
        return attrs

class StaffCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.',
            'required': 'Password is required'
        },
        help_text="Staff account password (min 8 characters)"
    )
    store = StoreCreateSerializer(required=False, write_only=True, help_text="Store details (required if store_id is not provided)")
    manager = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0,
        help_text="ID of the manager (0 or null for no manager)"
    )
    
    def validate_manager(self, value):
        if value == 0:
            return None
        if value is not None:
            try:
                return Staff.objects.get(pk=value)
            except Staff.DoesNotExist:
                raise serializers.ValidationError("Manager with this ID does not exist.")
        return value

    class Meta:
        swagger_schema_fields = {
            'example': {
                "username": "store_manager",
                "email": "manager@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "123-456-7890",
                "password": "securepass123",
                "is_active": True,
                "store": {
                    "store_name": "Main Store",
                    "email": "main@example.com",
                    "phone": "123-456-7890",
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001"
                },
                "manager": 0
            }
        }

    class Meta:
        model = Staff
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'phone', 'password', 'is_active', 'store_id', 'store', 'manager')
        extra_kwargs = {
            'username': {'help_text': 'Username for the staff account'},
            'email': {'required': True, 'help_text': 'Email address of the staff member'},
            'first_name': {'required': True, 'help_text': 'First name of the staff member'},
            'last_name': {'help_text': 'Last name of the staff member'},
            'phone': {'help_text': 'Contact phone number'},
            'is_active': {'help_text': 'Whether the staff account is active', 'default': True},
            'store_id': {
                'help_text': 'ID of an existing store (provide either this or store object)',
                'required': False,
                'allow_null': True
            },
            'manager': {
                'help_text': 'ID of the manager (0 for no manager)',
                'required': False,
                'allow_null': True,
                'default': 0
            },
        }

    def validate(self, attrs):
        if attrs.get('store') and attrs.get('store_id'):
            raise serializers.ValidationError({
                'non_field_errors': ["Cannot provide both 'store' and 'store_id'. Choose one."]
            })
        return attrs

    def validate_username(self, value):
        if self.instance and self.instance.username == value:
            return value
        if Staff.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A staff member with this username already exists.")
        return value.lower()

    def validate_email(self, value):
        if self.instance and self.instance.email == value:
            return value
        if value and Staff.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A staff member with this email already exists.")
        return value.lower() if value else value

    def create(self, validated_data):
        from api.store.models import Store
        
        store_data = validated_data.pop('store', None)
        password = validated_data.pop('password')
        
        # Create store if store_data is provided
        if store_data:
            store = Store.objects.create(**store_data)
            validated_data['store_id'] = store.id  # Changed from store.store_id to store.id
        
        # Create staff
        staff = Staff(**validated_data)
        staff.set_password(password)
        staff.save()
        return staff

    def update(self, instance, validated_data):
        from api.store.models import Store
        
        store_data = validated_data.pop('store', None)
        password = validated_data.pop('password', None)
        
        # Update store if store_data is provided
        if store_data and instance.store_id:
            store = instance.store
            for attr, value in store_data.items():
                setattr(store, attr, value)
            store.save()
        
        # Update staff fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance
