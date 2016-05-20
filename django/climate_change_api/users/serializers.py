"""Serializers for Users, Organizations, and other models in app"""

from rest_framework import serializers
from users.models import APIUser


class APIUserSerializer(serializers.ModelSerializer):
    """ Serializer for user """

    class Meta:
        model = APIUser
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'password', 'is_staff',
            'is_superuser', 'organization',)
        read_only_fields = ('id',)
        write_only_fields = ('password',)
