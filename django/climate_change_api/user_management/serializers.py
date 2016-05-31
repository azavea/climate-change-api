from rest_framework import serializers
from django.contrib.auth import get_user_model
from user_management.models import UserProfile
from django.contrib.auth.models import User
from datetime import datetime


class APIUserSerializer(serializers.ModelSerializer):
    """ Serializer for user """

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_staff',
            'is_superuser', 'date_joined')
        read_only_fields = ('id')


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    is_staff = serializers.BooleanField(source='user.is_staff')
    is_superuser = serializers.BooleanField(source='user.is_superuser')

    class Meta:
        model = UserProfile
        fields = ('email', 'username', 'first_name', 'last_name', 'organization', 'is_superuser', 'is_staff',)


    def create(self, validated_data):
            # create user
            user_data = validated_data.pop('user')

            user = User.objects.create(
                email = user_data['email'],
                username = user_data['username'],
                first_name = user_data['first_name'],
                last_name = user_data['last_name'],
                is_staff = user_data['is_staff'],
                is_superuser = user_data['is_superuser'],
                date_joined = datetime.now(),
            )

            # create profile
            profile = UserProfile.objects.create(
                user = user,
                organization = validated_data['organization'],
            )

            return profile
