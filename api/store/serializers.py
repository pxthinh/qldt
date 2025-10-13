from rest_framework import serializers
from .models import Store


class StoreSerializer(serializers.ModelSerializer):
    """Serializer for the Store model."""
    class Meta:
        model = Store
        fields = [
            'id',
            'store_name',
            'phone',
            'email',
            'street',
            'city',
            'state',
            'zip_code',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
