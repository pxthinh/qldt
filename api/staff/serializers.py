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


class StaffCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.'
        }
    )

    class Meta:
        model = Staff
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'phone', 'password', 'is_active', 'store_id', 'manager_id')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
        }

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
        password = validated_data.pop('password')
        staff = Staff(**validated_data)
        staff.set_password(password)
        staff.save()
        return staff

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance
        read_only_fields = ('staff_id',)
