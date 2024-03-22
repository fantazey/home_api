from django.urls import path, include
from rest_framework import routers
from .views import PlaceViewSet, index


router = routers.DefaultRouter()
router.register(r'places', PlaceViewSet)

app_name = 'travel'
urlpatterns = [
    path('', index, name='index'),
    path('api/', include(router.urls)),
]