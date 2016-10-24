from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from models import Project


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    owner = serializers.HiddenField(default=CurrentUserDefault())

    created = serializers.DateTimeField(read_only=True)
    modified = serializers.DateTimeField(read_only=True)

    project_data = serializers.JSONField()

    class Meta:
        model = Project
        fields = ('id', 'owner', 'created', 'modified', 'project_data')
