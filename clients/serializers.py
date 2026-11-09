from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Client


class StaffClientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(role='client', is_active=True),
        required=False, allow_null=True,
    )

    class Meta:
        model = Client
        fields = (
            'id', 'user', 'full_name', 'phone', 'email', 'address',
            'nid_or_reference', 'status', 'notes', 'created_by', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def validate_user(self, user):
        if user is not None:
            matches = Client.objects.filter(user=user)
            if self.instance:
                matches = matches.exclude(pk=self.instance.pk)
            if matches.exists():
                raise serializers.ValidationError('This user is already linked to a client.')
        return user


class OwnClientSerializer(serializers.ModelSerializer):
    """Deliberately omit staff notes, identity references and staff-account IDs."""
    class Meta:
        model = Client
        fields = ('id', 'full_name', 'phone', 'email', 'address', 'status', 'created_at', 'updated_at')
        read_only_fields = fields
