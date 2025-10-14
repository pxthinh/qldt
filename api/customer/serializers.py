from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Customer model.
    Handles serialization and deserialization of Customer instances.
    """
    user_name = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = [
            'customer_id', 'user_name', 'email', 'first_name', 'last_name',
            'phone', 'password'
        ]
        read_only_fields = ['customer_id']
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
