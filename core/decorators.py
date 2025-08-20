from django.contrib.auth.decorators import user_passes_test

def admin_check(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'admin'

def admin_or_moderator(user):
    return user.is_authenticated and getattr(user, 'role', None) in ('admin', 'moderator')

def user_only(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'user'

def moderator_only(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'moderator'

user_required = user_passes_test(user_only)
moderator_required = user_passes_test(moderator_only)
admin_required = user_passes_test(admin_check)
admin_or_moderator_required = user_passes_test(admin_or_moderator)
