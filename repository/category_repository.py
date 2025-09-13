from typing import Mapping, List, Dict
from api.category.models import Category

def list_categories(params: Mapping[str, str]) -> List[Dict]:
    qs = Category.objects.all()
    name = (params.get('name') or '').strip()
    if name:
        qs = qs.filter(category_name__icontains=name)

    order = (params.get('order') or 'desc').lower()
    order_field = 'category_name'
    if order == 'desc':
        order_field = '-' + order_field
    qs = qs.order_by(order_field)

    return list(qs.values('category_id', 'category_name', 'created_at', 'updated_at'))
