from django.contrib import admin
from .models import Workout, Exercise, Set, NutritionLog, ContactMessage


# ─────────────────────────────────────────
# INLINE CLASSES
# ─────────────────────────────────────────

class SetInline(admin.TabularInline):
    model = Set
    extra = 0
    fields = ['set_number', 'reps', 'weight']


class ExerciseInline(admin.StackedInline):
    model = Exercise
    extra = 0
    show_change_link = True
    fields = ['name', 'notes']


# ─────────────────────────────────────────
# WORKOUT ADMIN
# ─────────────────────────────────────────

class WorkoutAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'title', 'date', 'get_total_exercises', 'get_total_volume_display', 'has_image']
    search_fields = ['user__email', 'user__username', 'title']
    list_filter = ['date']
    inlines = [ExerciseInline]
    readonly_fields = ['created_at', 'get_total_volume_display', 'get_total_exercises', 'get_total_sets_display']

    fieldsets = (
        ('Workout Info', {
            'fields': ('user', 'title', 'date', 'notes', 'image')
        }),
        ('Stats (Read Only)', {
            'fields': ('get_total_exercises', 'get_total_sets_display', 'get_total_volume_display', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def get_total_volume_display(self, obj):
        return f"{obj.get_total_volume()} kg"
    get_total_volume_display.short_description = 'Total Volume'

    def get_total_exercises(self, obj):
        return obj.get_total_exercises()
    get_total_exercises.short_description = 'Exercises'

    def get_total_sets_display(self, obj):
        return obj.get_total_sets()
    get_total_sets_display.short_description = 'Total Sets'

    def has_image(self, obj):
        return "Yes" if obj.image else "No"
    has_image.short_description = 'Image'


# ─────────────────────────────────────────
# EXERCISE ADMIN
# ─────────────────────────────────────────

class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'workout_title', 'workout_user', 'get_total_sets', 'get_volume_display']
    search_fields = ['name', 'workout__title', 'workout__user__email']
    inlines = [SetInline]
    readonly_fields = ['get_volume_display', 'get_total_sets']

    def workout_title(self, obj):
        return obj.workout.title
    workout_title.short_description = 'Workout'

    def workout_user(self, obj):
        return obj.workout.user.email
    workout_user.short_description = 'User'

    def get_volume_display(self, obj):
        return f"{obj.get_volume()} kg"
    get_volume_display.short_description = 'Total Volume'

    def get_total_sets(self, obj):
        return obj.get_total_sets()
    get_total_sets.short_description = 'Total Sets'


# ─────────────────────────────────────────
# NUTRITION LOG ADMIN
# ─────────────────────────────────────────

class NutritionLogAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'meal_name', 'date', 'calories', 'protein_display', 'carbs_display', 'fat_display']
    search_fields = ['user__email', 'meal_name']
    list_filter = ['date']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Log Info', {
            'fields': ('user', 'date', 'meal_name')
        }),
        ('Nutrition Breakdown', {
            'fields': ('calories', 'protein', 'carbs', 'fat')
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def protein_display(self, obj):
        return f"{obj.protein}g"
    protein_display.short_description = 'Protein'

    def carbs_display(self, obj):
        return f"{obj.carbs}g"
    carbs_display.short_description = 'Carbs'

    def fat_display(self, obj):
        return f"{obj.fat}g"
    fat_display.short_description = 'Fat'


# ─────────────────────────────────────────
# CONTACT MESSAGE ADMIN
# ─────────────────────────────────────────

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['status_badge', 'name', 'email', 'subject', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Sender', {
            'fields': ('name', 'email')
        }),
        ('Message', {
            'fields': ('subject', 'message', 'created_at')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
    )

    def status_badge(self, obj):
        if obj.is_read:
            return "Read"
        return "Unread"
    status_badge.short_description = 'Status'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        msg = self.get_object(request, object_id)
        if msg and not msg.is_read:
            msg.is_read = True
            msg.save()
        return super().change_view(request, object_id, form_url, extra_context)

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} message(s) marked as read.")
    mark_as_read.short_description = "Mark selected as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} message(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"


# ─────────────────────────────────────────
# ADMIN SITE BRANDING
# ─────────────────────────────────────────

admin.site.site_header = "Fitness Tracker Admin"
admin.site.site_title = "Fitness Tracker"
admin.site.index_title = "Welcome to the Admin Panel"


# ─────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────

admin.site.register(Workout, WorkoutAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(NutritionLog, NutritionLogAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)