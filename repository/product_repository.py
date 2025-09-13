from typing import Mapping, List, Dict
from math import ceil
from api.product.models import Product

_FIELD_MAP = {
    'id': 'product_id', 'product_id': 'product_id',
    'name': 'product_name', 'product_name': 'product_name',
    'price': 'list_price', 'list_price': 'list_price',
    'year': 'model_year', 'model_year': 'model_year',
    'brand': 'brand__brand_name', 'brand_name': 'brand__brand_name',
    'brand_id': 'brand_id',
    'category': 'category__category_name', 'category_name': 'category__category_name',
    'category_id': 'category_id',
}

def _csv_ints(s: str | None) -> list[int]:
    if not s:
        return []
    return [int(x) for x in s.split(',') if x.strip().isdigit()]

def _to_int(x, default=0, min_val=None, max_val=None):
    try:
        v = int(x)
    except Exception:
        v = default
    if min_val is not None and v < min_val: v = min_val
    if max_val is not None and v > max_val: v = max_val
    return v

def list_products(params: Mapping[str, str]) -> Dict:
    qs = Product.objects.select_related('brand', 'category').all()

    name = (params.get('name') or '').strip()
    if name:
        qs = qs.filter(product_name__icontains=name)

    b_ids = _csv_ints(params.get('brand_id'))
    if b_ids:
        qs = qs.filter(brand_id__in=b_ids)

    c_ids = _csv_ints(params.get('category_id'))
    if c_ids:
        qs = qs.filter(category_id__in=c_ids)

    min_price = params.get('min_price')
    if min_price not in (None, ''):
        qs = qs.filter(list_price__gte=min_price)

    max_price = params.get('max_price')
    if max_price not in (None, ''):
        qs = qs.filter(list_price__lte=max_price)

    min_year = params.get('min_year')
    if min_year not in (None, ''):
        qs = qs.filter(model_year__gte=min_year)

    max_year = params.get('max_year')
    if max_year not in (None, ''):
        qs = qs.filter(model_year__lte=max_year)

    order_by_key = (params.get('order_by') or 'id').strip().lstrip('+').lower()
    direction = (params.get('order') or 'desc').strip().lower()
    order_field = _FIELD_MAP.get(order_by_key, 'product_id')
    if direction == 'desc':
        order_field = '-' + order_field
    qs = qs.order_by(order_field)

    page = params.get('page')
    page_size = params.get('page_size')
    if page or page_size:
        page = _to_int(page, default=1, min_val=1)
        page_size = _to_int(page_size, default=20, min_val=1, max_val=100)
        total = qs.count()
        total_pages = ceil(total / page_size) if page_size else 1
        offset = (page - 1) * page_size
        limit = page_size
        qs = qs[offset: offset + limit]
        has_next = page < total_pages
        has_prev = page > 1
    else:
        offset = _to_int(params.get('offset'), default=0, min_val=0)
        limit = _to_int(params.get('limit'), default=0, min_val=0, max_val=100)
        total = qs.count()
        if limit > 0:
            qs = qs[offset: offset + limit]

        page_size = limit if limit > 0 else total or 1
        page = (offset // page_size) + 1 if page_size else 1
        total_pages = ceil(total / page_size) if page_size else 1
        has_next = (offset + page_size) < total
        has_prev = offset > 0

    items = list(qs.values(
        'product_id',
        'product_name',
        'brand_id', 'brand__brand_name',
        'category_id', 'category__category_name',
        'model_year',
        'list_price',
    ))
    for d in items:
        d['brand_name'] = d.pop('brand__brand_name', None)
        d['category_name'] = d.pop('category__category_name', None)

    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "offset": offset,
            "limit": limit,
        },
        "ordering": {
            "order_by": order_by_key,
            "direction": direction if direction in ("asc", "desc") else "desc",
        },
    }
