from django.contrib import admin
from .models import Workout, Exercise, Set, NutritionLog,ContactMessage


class SetInline(admin.TabularInline):
    model = Set
    extra = 3  # shows 3 empty set rows by default


class ExerciseInline(admin.StackedInline):
    model = Exercise
    extra = 1
    show_change_link = True


class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'workout', 'get_total_sets', 'get_volume']
    inlines = [SetInline]

    def get_volume(self, obj):
        return f"{obj.get_volume()} kg"
    get_volume.short_description = 'Total Volume'

    def get_total_sets(self, obj):
        return obj.get_total_sets()
    get_total_sets.short_description = 'Total Sets'


class WorkoutAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'date', 'get_total_exercises', 'get_total_volume']
    search_fields = ['user__email', 'title']
    list_filter = ['date']
    inlines = [ExerciseInline]

    def get_total_volume(self, obj):
        return f"{obj.get_total_volume()} kg"
    get_total_volume.short_description = 'Total Volume'

    def get_total_exercises(self, obj):
        return obj.get_total_exercises()
    get_total_exercises.short_description = 'Exercises'


class NutritionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'meal_name', 'calories', 'protein', 'carbs', 'fat', 'date']
    search_fields = ['user__email', 'meal_name']
    list_filter = ['date']

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    ordering = ['-created_at']


    def change_view(self, request, object_id, form_url='', extra_context=None):
        msg = self.get_object(request, object_id)
        if msg and not msg.is_read:
            msg.is_read = True
            msg.save()
        return super().change_view(request, object_id, form_url, extra_context)

admin.site.register(Workout, WorkoutAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(NutritionLog, NutritionLogAdmin)