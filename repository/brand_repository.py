from typing import Mapping, List, Dict
from api.brand.models import Brand

def list_brands(params: Mapping[str, str]) -> List[Dict]:
    qs = Brand.objects.all()
    name = (params.get('name') or '').strip()
    if name:
        qs = qs.filter(brand_name__icontains=name)

    order = (params.get('order') or 'desc').lower()
    order_field = 'brand_name'
    if order == 'desc':
        order_field = '-' + order_field
    qs = qs.order_by(order_field)

    return list(qs.values('brand_id', 'brand_name', 'created_at', 'updated_at'))
