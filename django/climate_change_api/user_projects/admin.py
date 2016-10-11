from django.contrib import admin
from models import Project


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'created', 'modified')
    ordering = ('created', )

admin.site.register(Project, ProjectAdmin)
