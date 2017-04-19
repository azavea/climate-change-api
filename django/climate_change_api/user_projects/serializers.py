from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from .models import Project
from .validators import validate_user_project


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    owner = serializers.HiddenField(default=CurrentUserDefault())

    created = serializers.DateTimeField(read_only=True)
    modified = serializers.DateTimeField(read_only=True)

    project_data = serializers.JSONField(validators=[validate_user_project])

    class Meta:
        model = Project
        fields = ('id', 'owner', 'created', 'modified', 'project_data')
