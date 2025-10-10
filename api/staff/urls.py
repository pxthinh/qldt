from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views_auth

app_name = 'staff_auth'

# Schema view for staff API documentation
staff_schema_view = get_schema_view(
   openapi.Info(
      title="Staff API",
      default_version='v1',
      description="""
      Staff API documentation for managing staff members and authentication.
      
      ## Authentication
      - Login at `/api/staff/auth/login/`
      - Use the token in the header: `Token <token>`
      - Logout at `/api/staff/auth/logout/`
      """,
      contact=openapi.Contact(email="staff@example.com"),
      license=openapi.License(name="Proprietary"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   patterns=[
       path('api/staff/', include('api.staff.urls')),
   ],
)

urlpatterns = [
    # Authentication endpoints
    path('login/', views_auth.StaffLoginView.as_view(), name='login'),
    path('logout/', views_auth.StaffLogoutView.as_view(), name='logout'),
    path('profile/', views_auth.StaffProfileView.as_view(), name='profile'),
    
    # Swagger documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', staff_schema_view.without_ui(cache_timeout=0), name='staff-schema-json'),
    path('swagger/', staff_schema_view.with_ui('swagger', cache_timeout=0), name='staff-schema-swagger-ui'),
    path('redoc/', staff_schema_view.with_ui('redoc', cache_timeout=0), name='staff-schema-redoc'),
]
