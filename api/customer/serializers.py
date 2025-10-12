from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Customer model.
    Handles serialization and deserialization of Customer instances.
    """
    username = serializers.CharField(source='user_name')
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'customer_id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['customer_id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        """
        Create and return a new Customer instance, given the validated data.
        """
        # Extract password and username from validated_data
        password = validated_data.pop('password', None)
        username = validated_data.pop('user_name')
        
        # Create the user
        user = Customer.objects.create_user(
            user_name=username,
            password=password,
            **validated_data
        )
        return user

    def update(self, instance, validated_data):
        """
        Update and return an existing Customer instance, given the validated data.
        """
        # Handle password update if provided
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
            
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance
