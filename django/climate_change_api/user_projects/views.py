from rest_framework import viewsets

from models import Project
from serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        """
        Ensures users are only able to view their own projects
        """
        user = self.request.user
        return Project.objects.filter(owner=user)
