from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'clinic', 'created_by', 'date_created', 'deadline', 'is_done', 'done_by', 'is_overdue')
    list_filter = ('is_done', 'clinic', 'created_by', 'done_by', 'date_created')
    search_fields = ('title', 'description')
    ordering = ('-date_created',)
