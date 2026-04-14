from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token  
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Video API",
        default_version='v1',
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],  
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),
    path("accounts", include("accounts.urls")),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('api/token/', obtain_auth_token), 
]