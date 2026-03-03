from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Profile


# ─────────────────────────────────────────
# PROFILE INLINE (shown inside User page)
# ─────────────────────────────────────────

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['age', 'weight', 'height', 'fitness_goal', 'profile_picture', 'bmi_display']
    readonly_fields = ['bmi_display']

    def bmi_display(self, obj):
        bmi = obj.get_bmi()
        if bmi is None:
            return "—"
        if bmi < 18.5:
            return "%.1f — Underweight" % bmi
        elif bmi < 25:
            return "%.1f — Normal" % bmi
        elif bmi < 30:
            return "%.1f — Overweight" % bmi
        else:
            return "%.1f — Obese" % bmi
    bmi_display.short_description = 'BMI'


# ─────────────────────────────────────────
# USER ADMIN
# ─────────────────────────────────────────

class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    date_hierarchy = None  # Disable inherited date_hierarchy from UserAdmin

    list_display = ['email', 'username', 'account_status', 'is_staff', 'date_joined', 'workout_count', 'meal_count']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        ('Account', {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff']

    def account_status(self, obj):
        if obj.is_active:
            return "Active"
        return "Banned"
    account_status.short_description = 'Status'

    def workout_count(self, obj):
        return obj.workouts.count()
    workout_count.short_description = 'Workouts'

    def meal_count(self, obj):
        return obj.nutrition_logs.count()
    meal_count.short_description = 'Meals Logged'

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, "%d user(s) activated." % updated)
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.filter(is_superuser=False).update(is_active=False)
        self.message_user(request, "%d user(s) deactivated (superusers skipped)." % updated)
    deactivate_users.short_description = "Deactivate / Ban selected users"

    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, "%d user(s) granted staff access." % updated)
    make_staff.short_description = "Grant staff (admin) access"

    def remove_staff(self, request, queryset):
        updated = queryset.filter(is_superuser=False).update(is_staff=False)
        self.message_user(request, "%d user(s) had staff access removed." % updated)
    remove_staff.short_description = "Remove staff access"


# ─────────────────────────────────────────
# PROFILE ADMIN (standalone view)
# ─────────────────────────────────────────

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'age', 'weight_display', 'height_display', 'bmi_display', 'fitness_goal', 'has_picture']
    search_fields = ['user__email', 'user__username', 'fitness_goal']
    list_filter = ['fitness_goal']
    readonly_fields = ['bmi_display']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def weight_display(self, obj):
        return "%s kg" % obj.weight if obj.weight else "—"
    weight_display.short_description = 'Weight'

    def height_display(self, obj):
        return "%s cm" % obj.height if obj.height else "—"
    height_display.short_description = 'Height'

    def bmi_display(self, obj):
        bmi = obj.get_bmi()
        if bmi is None:
            return "—"
        if bmi < 18.5:
            return "%.1f (Underweight)" % bmi
        elif bmi < 25:
            return "%.1f (Normal)" % bmi
        elif bmi < 30:
            return "%.1f (Overweight)" % bmi
        else:
            return "%.1f (Obese)" % bmi
    bmi_display.short_description = 'BMI'

    def has_picture(self, obj):
        return "Yes" if obj.profile_picture else "No"
    has_picture.short_description = 'Photo'


# ─────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)