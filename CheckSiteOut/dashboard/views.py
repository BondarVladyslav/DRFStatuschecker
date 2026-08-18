from rest_framework.decorators import action
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .services import add_site_for_user
from .serializers import SiteDetailSerializer, SiteSerializer, SiteResponseSerializer
from .models import Site
from rest_framework.pagination import PageNumberPagination


class DashBoardViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SiteDetailSerializer
        if self.action == "responses":
            return SiteResponseSerializer
        return SiteSerializer

    def get_queryset(self):
        qs = Site.objects.filter(owners=self.request.user)
        return qs

    def perform_create(self, serializer):
        link = serializer.validated_data["link"]

        site = add_site_for_user(
            link=link,
            user=self.request.user,
        )

        serializer.instance = site

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        site = self.get_object()
        site.owners.remove(self.request.user)
        if not site.owners.exists():
            site.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def responses(self, request, pk=None):
        site = self.get_object()
        qs = site.responses.all()
        page = self.paginate_queryset(qs)
        serializer = SiteResponseSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
