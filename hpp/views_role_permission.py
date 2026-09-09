from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .models import Role, UserProfile, AppMenu, RoleMenuPermission
from .menu_registry import sync_menu_registry, SYSTEM_MENUS, DEFAULT_ROLES

def _require_superadmin(request):
    """Helper to check if current user is Superadmin"""
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True
    profile = getattr(request.user, "profile", None)
    return bool(profile and profile.role and profile.role.code == "SUPERADMIN")


def role_permission_matrix(request):
    """
    Halaman Matriks Hak Akses Dinamis Role vs Menu
    Hanya dapat diakses oleh Superadmin
    """
    if not _require_superadmin(request):
        messages.error(request, "Akses Terbatas: Hanya Super Admin yang dapat mengelola hak akses role.")
        return redirect("project_list")

    # Auto-sync menus and roles with menu_registry
    sync_menu_registry()

    roles = list(Role.objects.all().order_by("-is_system_role", "name"))
    menus = list(AppMenu.objects.filter(is_active=True).order_by("module", "sort_order"))

    # Group menus by module for structured table presentation
    modules_dict = {}
    for m in menus:
        if m.module not in modules_dict:
            modules_dict[m.module] = []
        modules_dict[m.module].append(m)

    # Fetch existing permissions into a fast lookup dict: (role_uuid, menu_code) -> bool
    perms_qs = RoleMenuPermission.objects.all()
    perms_map = {(p.role_id, p.menu_id): p.can_view for p in perms_qs}

    if request.method == "POST":
        action = request.POST.get("action", "save_matrix")

        if action == "save_matrix":
            with transaction.atomic():
                for role in roles:
                    if role.code == "SUPERADMIN":
                        # Superadmin always has full access
                        for menu in menus:
                            RoleMenuPermission.objects.update_or_create(
                                role=role,
                                menu=menu,
                                defaults={"can_view": True}
                            )
                        continue

                    for menu in menus:
                        field_name = f"perm_{role.uuid}_{menu.code}"
                        is_checked = field_name in request.POST
                        RoleMenuPermission.objects.update_or_create(
                            role=role,
                            menu=menu,
                            defaults={"can_view": is_checked}
                        )

            messages.success(request, "Matriks hak akses role berhasil diperbarui secara real-time!")
            return redirect("role_permission_matrix")

        elif action == "reset_defaults":
            with transaction.atomic():
                # Re-apply defaults from registry
                for m_data in SYSTEM_MENUS:
                    menu = AppMenu.objects.filter(code=m_data["code"]).first()
                    if not menu:
                        continue
                    default_roles = m_data.get("default_roles", ["SUPERADMIN"])
                    for role in roles:
                        can_view = (role.code == "SUPERADMIN") or (role.code in default_roles)
                        RoleMenuPermission.objects.update_or_create(
                            role=role,
                            menu=menu,
                            defaults={"can_view": can_view}
                        )

            messages.success(request, "Hak akses seluruh role berhasil direset ke konfigurasi standar pabrik.")
            return redirect("role_permission_matrix")

    return render(request, "hpp/auth/role_permission_matrix.html", {
        "roles": roles,
        "modules_dict": modules_dict,
        "perms_map": perms_map,
        "total_menus": len(menus),
    })


def user_manage_list(request):
    """
    Manajemen Akun Pengguna & Penugasan Role
    """
    if not _require_superadmin(request):
        messages.error(request, "Akses Terbatas: Hanya Super Admin yang dapat mengelola akun pengguna.")
        return redirect("project_list")

    users = User.objects.all().select_related("profile", "profile__role").order_by("-is_superuser", "username")
    roles = Role.objects.all().order_by("-is_system_role", "name")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_user":
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "").strip()
            full_name = request.POST.get("full_name", "").strip()
            email = request.POST.get("email", "").strip()
            role_uuid = request.POST.get("role_uuid", "").strip()
            phone = request.POST.get("phone", "").strip()

            if not username or not password:
                messages.error(request, "Username dan kata sandi wajib diisi.")
                return redirect("user_manage_list")

            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' sudah digunakan.")
                return redirect("user_manage_list")

            with transaction.atomic():
                role = Role.objects.filter(uuid=role_uuid).first() if role_uuid else None
                is_super = (role and role.code == "SUPERADMIN")
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=full_name,
                    is_superuser=is_super,
                    is_staff=is_super,
                )
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    phone=phone
                )
            messages.success(request, f"Pengguna '{username}' berhasil dibuat dengan role {role.name if role else 'GUEST'}.")
            return redirect("user_manage_list")

        elif action == "update_role":
            user_id = request.POST.get("user_id")
            role_uuid = request.POST.get("role_uuid", "").strip()
            target_user = get_object_or_404(User, id=user_id)

            role = Role.objects.filter(uuid=role_uuid).first() if role_uuid else None
            is_super = (role and role.code == "SUPERADMIN")

            target_user.is_superuser = is_super
            target_user.is_staff = is_super
            target_user.save(update_fields=["is_superuser", "is_staff"])

            profile, _ = UserProfile.objects.get_or_create(user=target_user)
            profile.role = role
            profile.save(update_fields=["role"])

            messages.success(request, f"Role untuk pengguna '{target_user.username}' berhasil diubah menjadi {role.name if role else 'GUEST'}.")
            return redirect("user_manage_list")

        elif action == "reset_password":
            user_id = request.POST.get("user_id")
            new_password = request.POST.get("new_password", "").strip()
            target_user = get_object_or_404(User, id=user_id)

            if len(new_password) < 6:
                messages.error(request, "Kata sandi minimal 6 karakter.")
                return redirect("user_manage_list")

            target_user.set_password(new_password)
            target_user.save()
            messages.success(request, f"Kata sandi untuk '{target_user.username}' berhasil diperbarui.")
            return redirect("user_manage_list")

        elif action == "toggle_active":
            user_id = request.POST.get("user_id")
            target_user = get_object_or_404(User, id=user_id)

            if target_user == request.user:
                messages.error(request, "Anda tidak dapat menonaktifkan akun Anda sendiri.")
                return redirect("user_manage_list")

            target_user.is_active = not target_user.is_active
            target_user.save(update_fields=["is_active"])
            status_text = "diaktifkan" if target_user.is_active else "dinonaktifkan"
            messages.info(request, f"Akun '{target_user.username}' telah {status_text}.")
            return redirect("user_manage_list")

        elif action == "delete_user":
            user_id = request.POST.get("user_id")
            target_user = get_object_or_404(User, id=user_id)

            if target_user == request.user:
                messages.error(request, "Anda tidak dapat menghapus akun Anda sendiri.")
                return redirect("user_manage_list")

            username = target_user.username
            target_user.delete()
            messages.success(request, f"Akun pengguna '{username}' telah dihapus.")
            return redirect("user_manage_list")

    return render(request, "hpp/auth/user_manage_list.html", {
        "users": users,
        "roles": roles,
    })


def role_manage_list(request):
    """
    Manajemen Master Role Pengguna (Tambah & Edit Role Kustom)
    """
    if not _require_superadmin(request):
        messages.error(request, "Akses Terbatas: Hanya Super Admin yang dapat mengelola role.")
        return redirect("project_list")

    roles = Role.objects.all().order_by("-is_system_role", "name")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_role":
            code = request.POST.get("code", "").strip().upper()
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            badge_color = request.POST.get("badge_color", "bg-slate-100 text-slate-700 border-slate-300").strip()

            if not code or not name:
                messages.error(request, "Kode dan Nama Role wajib diisi.")
                return redirect("role_manage_list")

            if Role.objects.filter(code=code).exists():
                messages.error(request, f"Role dengan kode '{code}' sudah ada.")
                return redirect("role_manage_list")

            Role.objects.create(
                code=code,
                name=name,
                description=description,
                badge_color=badge_color,
                is_system_role=False,
            )
            sync_menu_registry()
            messages.success(request, f"Role baru '{name}' ({code}) berhasil ditambahkan.")
            return redirect("role_manage_list")

        elif action == "delete_role":
            role_uuid = request.POST.get("role_uuid")
            role = get_object_or_404(Role, uuid=role_uuid)

            if role.is_system_role:
                messages.error(request, f"Role sistem '{role.name}' dilindungi dan tidak dapat dihapus.")
                return redirect("role_manage_list")

            if role.users.exists():
                messages.error(request, f"Role '{role.name}' tidak dapat dihapus karena masih digunakan oleh {role.users.count()} pengguna.")
                return redirect("role_manage_list")

            role_name = role.name
            role.delete()
            messages.success(request, f"Role '{role_name}' telah dihapus.")
            return redirect("role_manage_list")

    return render(request, "hpp/auth/role_manage_list.html", {
        "roles": roles,
    })


def menu_register_custom(request):
    """
    Form Web bagi Superadmin untuk mendaftarkan menu eksternal / menu kustom baru
    """
    if not _require_superadmin(request):
        messages.error(request, "Akses Terbatas.")
        return redirect("project_list")

    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        name = request.POST.get("name", "").strip()
        module = request.POST.get("module", "").strip()
        url_name = request.POST.get("url_name", "").strip()
        icon_svg = request.POST.get("icon_svg", "").strip()

        if not code or not name or not module or not url_name:
            messages.error(request, "Kode, Nama, Modul, dan URL Name wajib diisi.")
            return redirect("role_permission_matrix")

        if not code.startswith("MENU_"):
            code = f"MENU_{code}"

        AppMenu.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "module": module,
                "url_name": url_name,
                "icon_svg": icon_svg,
                "is_active": True,
            }
        )
        sync_menu_registry()
        messages.success(request, f"Menu '{name}' ({code}) berhasil didaftarkan dan dapat diatur hak aksesnya.")
        return redirect("role_permission_matrix")

    return redirect("role_permission_matrix")
