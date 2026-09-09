from django.contrib.auth.models import User
from .models import Role, UserProfile, AppMenu, RoleMenuPermission

def auth_menu_context(request):
    """
    Context Processor to supply dynamic menu visibility and role data to all templates.
    """
    if not request.user.is_authenticated:
        return {
            "current_user_role": None,
            "current_user_profile": None,
            "allowed_menu_codes": set(),
            "allowed_modules": set(),
        }

    user = request.user
    
    # Retrieve or auto-create UserProfile
    profile = getattr(user, "profile", None)
    if not profile:
        role = None
        if user.is_superuser:
            role = Role.objects.filter(code="SUPERADMIN").first()
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": role})

    role = profile.role
    is_super = user.is_superuser or (role and role.code == "SUPERADMIN")

    if is_super:
        # Superadmin gets 100% of all registered active menus
        all_menus = AppMenu.objects.filter(is_active=True)
        allowed_menu_codes = set(all_menus.values_list("code", flat=True))
        allowed_modules = set(all_menus.values_list("module", flat=True))
    else:
        if role:
            allowed_perms = RoleMenuPermission.objects.filter(
                role=role,
                can_view=True,
                menu__is_active=True
            ).select_related("menu")
            allowed_menu_codes = set(p.menu_id for p in allowed_perms)
            allowed_modules = set(p.menu.module for p in allowed_perms)
        else:
            allowed_menu_codes = set()
            allowed_modules = set()

    return {
        "current_user_role": role,
        "current_user_profile": profile,
        "allowed_menu_codes": allowed_menu_codes,
        "allowed_modules": allowed_modules,
        "is_superadmin_user": is_super,
    }
