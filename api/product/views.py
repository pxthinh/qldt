from django.http import JsonResponse
from .models import Product

def get_all(request):
    qs = Product.objects.select_related('brand', 'category').all()

    name = (request.GET.get('name') or '').strip()
    if name:
        qs = qs.filter(product_name__icontains=name)

    brand_id = (request.GET.get('brand_id') or '').strip()
    if brand_id:
        ids = [int(x) for x in brand_id.split(',') if x.strip().isdigit()]
        if ids:
            qs = qs.filter(brand_id__in=ids)

    category_id = (request.GET.get('category_id') or '').strip()
    if category_id:
        ids = [int(x) for x in category_id.split(',') if x.strip().isdigit()]
        if ids:
            qs = qs.filter(category_id__in=ids)

    min_price = request.GET.get('min_price')
    if min_price not in (None, ''):
        qs = qs.filter(list_price__gte=min_price)

    max_price = request.GET.get('max_price')
    if max_price not in (None, ''):
        qs = qs.filter(list_price__lte=max_price)

    min_year = request.GET.get('min_year')
    if min_year not in (None, ''):
        qs = qs.filter(model_year__gte=min_year)

    max_year = request.GET.get('max_year')
    if max_year not in (None, ''):
        qs = qs.filter(model_year__lte=max_year)

    field_map = {
        'id': 'product_id',
        'product_id': 'product_id',
        'name': 'product_name',
        'product_name': 'product_name',
        'price': 'list_price',
        'list_price': 'list_price',
        'year': 'model_year',
        'model_year': 'model_year',
        'brand': 'brand__brand_name',
        'brand_name': 'brand__brand_name',
        'brand_id': 'brand_id',
        'category': 'category__category_name',
        'category_name': 'category__category_name',
        'category_id': 'category_id',
    }

    order_by_key = (request.GET.get('order_by') or 'id').strip().lstrip('+').lower()
    direction = (request.GET.get('order') or 'desc').strip().lower()
    order_field = field_map.get(order_by_key, 'product_id')
    if direction == 'desc':
        order_field = '-' + order_field

    qs = qs.order_by(order_field)

    data = list(qs.values(
        'product_id',
        'product_name',
        'brand_id', 'brand__brand_name',
        'category_id', 'category__category_name',
        'model_year',
        'list_price',
    ))

    for d in data:
        d['brand_name'] = d.pop('brand__brand_name', None)
        d['category_name'] = d.pop('category__category_name', None)

    return JsonResponse(data, safe=False)
