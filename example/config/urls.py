"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from config.views import SupportChatView, UsersChatView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chatbot/", include("dj_chatbot.urls")),
    path("models/send/", SupportChatView.as_view(), name="models_send"),
    path("models/", TemplateView.as_view(template_name="override_model.html"), name="models"),
    path("tools/send/", UsersChatView.as_view(), name="tools_send"),
    path("tools/", TemplateView.as_view(template_name="override_tools.html"), name="tools"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
