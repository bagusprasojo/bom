import functools
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .models import Role, UserProfile, RoleMenuPermission, AppMenu

def login_view(request):
    """
    Halaman Login Pengguna Modern
    """
    if request.user.is_authenticated:
        return redirect("project_list")

    next_url = request.GET.get("next") or request.POST.get("next") or "/"

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Harap masukkan username dan kata sandi.")
            return render(request, "hpp/auth/login.html", {"username": username, "next": next_url})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, "Akun Anda dinonaktifkan. Silakan hubungi Super Admin.")
                return render(request, "hpp/auth/login.html", {"username": username, "next": next_url})

            login(request, user)
            
            # Ensure UserProfile exists
            profile = getattr(user, "profile", None)
            if not profile:
                role = Role.objects.filter(code="SUPERADMIN").first() if user.is_superuser else None
                profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": role})

            role_name = profile.role_name if profile else ("Super Admin" if user.is_superuser else "User")
            messages.success(request, f"Selamat datang kembali, {user.first_name or user.username}! Masuk sebagai {role_name}.")
            return redirect(next_url)
        else:
            messages.error(request, "Username atau kata sandi yang Anda masukkan salah.")
            return render(request, "hpp/auth/login.html", {"username": username, "next": next_url})

    return render(request, "hpp/auth/login.html", {"next": next_url})


def logout_view(request):
    """
    Logout pengguna dan kembali ke halaman login
    """
    username = request.user.username if request.user.is_authenticated else ""
    logout(request)
    messages.info(request, "Anda telah berhasil keluar dari sistem.")
    return redirect("login")


def profile_view(request):
    """
    Profil Pengguna & Ganti Password
    """
    if not request.user.is_authenticated:
        return redirect(f"/login/?next={request.path}")

    user = request.user
    profile = getattr(user, "profile", None)
    if not profile:
        role = Role.objects.filter(code="SUPERADMIN").first() if user.is_superuser else None
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": role})

    password_form = PasswordChangeForm(user=user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_info":
            full_name = request.POST.get("full_name", "").strip()
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("phone", "").strip()

            user.first_name = full_name
            user.email = email
            user.save(update_fields=["first_name", "email"])

            profile.phone = phone
            profile.save(update_fields=["phone"])

            messages.success(request, "Informasi profil berhasil diperbarui.")
            return redirect("profile")

        elif action == "change_password":
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user_updated = password_form.save()
                update_session_auth_hash(request, user_updated)
                messages.success(request, "Kata sandi Anda berhasil diperbarui!")
                return redirect("profile")
            else:
                messages.error(request, "Gagal mengubah kata sandi. Periksa ketentuan kata sandi.")

    return render(request, "hpp/auth/profile.html", {
        "user_profile": profile,
        "password_form": password_form,
    })


def menu_permission_required(menu_code):
    """
    Decorator untuk memproteksi view berdasarkan hak akses menu dinamis role.
    Penggunaan: @menu_permission_required("MENU_PROJECT_LIST")
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next={request.path}")

            user = request.user
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(user, "profile", None)
            if profile and profile.role:
                if profile.role.code == "SUPERADMIN":
                    return view_func(request, *args, **kwargs)

                has_perm = RoleMenuPermission.objects.filter(
                    role=profile.role,
                    menu_id=menu_code,
                    can_view=True
                ).exists()

                if has_perm:
                    return view_func(request, *args, **kwargs)

            # Access Denied
            menu_obj = AppMenu.objects.filter(code=menu_code).first()
            menu_name = menu_obj.name if menu_obj else menu_code
            return render(request, "hpp/auth/403.html", {
                "menu_name": menu_name,
                "menu_code": menu_code,
                "user_role": profile.role_name if profile else "Tanpa Role",
            }, status=403)

        return _wrapped_view
    return decorator
