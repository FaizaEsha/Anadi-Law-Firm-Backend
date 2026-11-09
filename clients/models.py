from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.permissions import has_role


class Client(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        ARCHIVED = 'archived', _('Archived')

    # A client may exist before receiving a portal login.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='client_profile', limit_choices_to={'role': 'client'},
    )
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    nid_or_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True, help_text=_('Internal staff notes; never exposed to clients.'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_clients', editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def clean(self):
        super().clean()
        if self.user_id and not has_role(self.user, 'client'):
            # Deactivating a login must not block editing its existing client record.
            existing_link = (
                self.user.role == 'client' and not self._state.adding
                and type(self).objects.filter(pk=self.pk, user_id=self.user_id).exists()
            )
            if not existing_link:
                raise ValidationError({'user': _('Choose an active user with the client role.')})

    def __str__(self):
        return self.full_name
