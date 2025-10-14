from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for the Product model"""
    category = serializers.StringRelatedField(source='category.category_name', read_only=True)
    brand = serializers.StringRelatedField(source='brand.brand_name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'product_id',
            'product_name',
            'list_price',
            'model_year',
            'category',
            'brand',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['product_id', 'created_at', 'updated_at']
