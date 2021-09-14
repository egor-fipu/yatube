from rest_framework import viewsets, mixins


class ListCreateDestroyViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.DestroyModelMixin, viewsets.GenericViewSet):
    pass
