from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import DashBoardViewSet

router = SimpleRouter()
router.register("dashboard", DashBoardViewSet, basename="dashboard")
urlpatterns = [path("", include(router.urls))]
