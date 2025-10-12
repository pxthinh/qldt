"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework.permissions import AllowAny

# Swagger configuration
def schema_exclude_path(path, method, path_regex, method_regex):
    # Include all paths in schema
    return True

schema_view = get_schema_view(
    openapi.Info(
        title="E-commerce API",
        default_version='v1',
        description="""
        Ecommerce API documentation
        
        ## Authentication
        1. Get your token from `/api/staff/auth/login/`
        2. Click 'Authorize' button (🔒) in top right
        3. Enter: `Token <your_token_here>`
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@ecommerce.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
    authentication_classes=(),
    validators=['flex', 'ssv'],
    urlconf='ecommerce.urls',
    patterns=[
        path('api/admin/category/', include('api.category.urls_admin')),
        path('api/admin/brand/', include('api.brand.urls_admin')),
        path('api/admin/customer/', include('api.customer.urls_admin')),
        path('api/admin/product/', include('api.product.urls_admin')),
        path('api/admin/staff/', include('api.staff.urls_admin')),
        path('api/admin/orders/', include('api.order.urls_admin')),  # Include admin orders in schema
    ]
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', RedirectView.as_view(url='/swagger/', permanent=False), name='swagger-redirect'),

    # API Endpoints
    path('api/customer/', include('api.customer.urls')),
    path('api/product/', include('api.product.urls')),
    path('api/category/', include('api.category.urls')),
    path('api/brand/', include('api.brand.urls')),
    path('api/orders/', include('api.order.urls')),  # Regular customer order endpoints

    # Staff authentication endpoints
    path('api/staff/auth/', include('api.staff.urls')),

    # Admin API Endpoints
    path('api/admin/category/', include('api.category.urls_admin')),
    path('api/admin/brand/', include('api.brand.urls_admin')),
    path('api/admin/customer/', include('api.customer.urls_admin')),
    path('api/admin/product/', include('api.product.urls_admin')),
    path('api/admin/staff/', include('api.staff.urls_admin')),  # Staff admin endpoints
    path('api/admin/orders/', include('api.order.urls_admin')),  # Admin order management endpoints

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
