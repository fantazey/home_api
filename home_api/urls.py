"""home_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.views.static import serve

from home_api.settings import MEDIA_ROOT, STATIC_ROOT
from home_api.views import index

urlpatterns = [
    path('', index, name='index'),
    path('weather/', include('weather.urls')),
    path('wip/', include('work_in_progress.urls')),
    path('postcards/', include('postcards.urls')),
    path('todo_mobile/', include('todo_mobile.urls')),
    path('travel/', include('travel.urls')),
    path('admin/', admin.site.urls),
    re_path(r"media/(?P<path>.*)$", serve, kwargs={'document_root': MEDIA_ROOT}),
    re_path(r"static/(?P<path>.*)$", serve, kwargs={'document_root': STATIC_ROOT})
]
