from django.contrib import admin
from .models import Recipe, Category, Comment, Rating, Feedback, UserProfile, SystemErrorLog, DeveloperInviteCode

admin.site.register(Recipe)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Rating)
admin.site.register(Feedback)
admin.site.register(UserProfile)

@admin.register(SystemErrorLog)
class SystemErrorLogAdmin(admin.ModelAdmin):
    list_display = ('error_message', 'user', 'path', 'created_at', 'resolved')
    list_filter = ('resolved', 'created_at')
    readonly_fields = ('traceback',)

@admin.register(DeveloperInviteCode)
class DeveloperInviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_active', 'used_by', 'created_at')
    list_filter = ('is_active',)
