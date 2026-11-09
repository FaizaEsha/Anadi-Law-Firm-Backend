from django.db import IntegrityError, transaction
from rest_framework import mixins, serializers, viewsets

from accounts.permissions import IsFirmMemberOrClientReadOnly, is_firm_member
from .models import Client
from .serializers import OwnClientSerializer, StaffClientSerializer


class ClientViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    permission_classes = [IsFirmMemberOrClientReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        queryset = Client.objects.all()
        if is_firm_member(self.request.user):
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        return StaffClientSerializer if is_firm_member(self.request.user) else OwnClientSerializer

    def save_client(self, serializer, **kwargs):
        try:
            with transaction.atomic():
                serializer.save(**kwargs)
        except IntegrityError:
            # The unique DB constraint also protects simultaneous linking requests.
            user = serializer.validated_data.get('user')
            if user is not None:
                matches = Client.objects.filter(user=user)
                if serializer.instance:
                    matches = matches.exclude(pk=serializer.instance.pk)
                if matches.exists():
                    raise serializers.ValidationError({'user': 'This user is already linked to a client.'})
            raise

    def perform_create(self, serializer):
        self.save_client(serializer, created_by=self.request.user)

    def perform_update(self, serializer):
        self.save_client(serializer)
