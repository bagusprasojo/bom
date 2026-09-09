"""
Script Verifikasi Komprehensif: Sistem Autentikasi & RBAC Dinamis
- Menguji otentikasi login & logout
- Menguji proteksi anonymous -> login redirect
- Menguji superadmin full access & menu registry
- Menguji pembatasan role operasional (Supervisor, Storekeeper, HRD)
- Menguji proteksi view 403 Forbidden
- Menguji perubahan matriks hak akses dinamis secara real-time
"""
import os
import sys
import django

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.abspath("."))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from hpp.models import Role, UserProfile, AppMenu, RoleMenuPermission
from hpp.menu_registry import sync_menu_registry, SYSTEM_MENUS, DEFAULT_ROLES

def run_tests():
    print("=" * 70)
    print("MEMULAI VERIFIKASI SISTEM LOGIN & RBAC DINAMIS")
    print("=" * 70)

    client = Client()

    # 1. Sync Menu Registry
    print("\n[TEST 1] Verifikasi Sinkronisasi Menu Registry...")
    sync_menu_registry()
    total_roles = Role.objects.count()
    total_menus = AppMenu.objects.count()
    total_perms = RoleMenuPermission.objects.count()
    print(f"  -> Total Role di DB: {total_roles}")
    print(f"  -> Total AppMenu di DB: {total_menus}")
    print(f"  -> Total RoleMenuPermission di DB: {total_perms}")
    assert total_roles >= 6, f"Expected at least 6 roles, found {total_roles}"
    assert total_menus >= 19, f"Expected at least 19 menus, found {total_menus}"
    print("  [PASS] Menu Registry berhasil disinkronkan.")

    # 2. Setup Superadmin User
    print("\n[TEST 2] Verifikasi Akun Superadmin 'admin'...")
    admin_user, created = User.objects.get_or_create(username="admin", defaults={"is_superuser": True, "is_staff": True})
    admin_user.set_password("admin123")
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.save()

    role_super = Role.objects.filter(code="SUPERADMIN").first()
    profile, _ = UserProfile.objects.get_or_create(user=admin_user, defaults={"role": role_super})
    profile.role = role_super
    profile.save()
    print(f"  -> Admin user ready: username='admin', role='{profile.role.name if profile.role else None}'")
    print("  [PASS] Akun Superadmin terverifikasi.")

    # 3. Anonymous User Redirection
    print("\n[TEST 3] Verifikasi Proteksi Anonymous User...")
    resp = client.get("/")
    print(f"  -> GET / tanpa login -> Status {resp.status_code}")
    assert resp.status_code == 302, f"Expected 302 redirect, got {resp.status_code}"
    assert "/login/" in resp.url, f"Expected redirect to login, got {resp.url}"

    resp_login = client.get("/login/")
    print(f"  -> GET /login/ -> Status {resp_login.status_code}")
    assert resp_login.status_code == 200, f"Expected 200 OK, got {resp_login.status_code}"
    print("  [PASS] Anonymous user dialihkan ke halaman login dengan benar.")

    # 4. Superadmin Login
    print("\n[TEST 4] Verifikasi Login Superadmin...")
    login_success = client.login(username="admin", password="admin123")
    assert login_success, "Login superadmin 'admin' gagal!"
    print("  -> Login admin berhasil.")

    # Test Superadmin accessing home & settings
    resp_home = client.get("/")
    assert resp_home.status_code == 200, f"Expected 200, got {resp_home.status_code}"
    assert b"HPP" in resp_home.content, "Halaman utama tidak memuat konten HPP"
    print(f"  -> GET / sebagai superadmin: 200 OK. Konten terverifikasi.")

    resp_matrix = client.get("/settings/permissions/")
    assert resp_matrix.status_code == 200, f"Expected 200, got {resp_matrix.status_code}"
    print(f"  -> GET /settings/permissions/ sebagai superadmin: 200 OK")

    resp_users = client.get("/settings/users/")
    assert resp_users.status_code == 200, f"Expected 200, got {resp_users.status_code}"
    print(f"  -> GET /settings/users/ sebagai superadmin: 200 OK")

    resp_roles = client.get("/settings/roles/")
    assert resp_roles.status_code == 200, f"Expected 200, got {resp_roles.status_code}"
    print(f"  -> GET /settings/roles/ sebagai superadmin: 200 OK")
    print("  [PASS] Superadmin memiliki akses penuh ke seluruh area.")

    # 5. Role Operasional: Supervisor / Mandor
    print("\n[TEST 5] Setup & Verifikasi User Role SUPERVISOR (Mandor)...")
    role_mandor = Role.objects.get(code="SUPERVISOR")
    mandor_user, _ = User.objects.get_or_create(username="mandor_budi", defaults={"first_name": "Budi Mandor"})
    mandor_user.set_password("mandor123")
    mandor_user.is_superuser = False
    mandor_user.is_staff = False
    mandor_user.save()
    p_mandor, _ = UserProfile.objects.get_or_create(user=mandor_user, defaults={"role": role_mandor})
    p_mandor.role = role_mandor
    p_mandor.save()

    client_mandor = Client()
    mandor_login = client_mandor.login(username="mandor_budi", password="mandor123")
    assert mandor_login, "Login mandor_budi gagal!"

    # Mandor can access attendance & work_log
    resp_att = client_mandor.get("/attendance/")
    print(f"  -> Mandor GET /attendance/ -> Status {resp_att.status_code}")
    assert resp_att.status_code == 200, f"Mandor should access /attendance/, got {resp_att.status_code}"

    resp_worklog = client_mandor.get("/work-logs/")
    print(f"  -> Mandor GET /work-logs/ -> Status {resp_worklog.status_code}")
    assert resp_worklog.status_code == 200, f"Mandor should access /work-logs/, got {resp_worklog.status_code}"

    # Mandor cannot access raw materials (Bahan Baku)
    resp_rm = client_mandor.get("/raw-materials/")
    print(f"  -> Mandor GET /raw-materials/ (Terlarang) -> Status {resp_rm.status_code}")
    assert resp_rm.status_code == 403, f"Mandor should be blocked from /raw-materials/ with 403, got {resp_rm.status_code}"

    # Mandor cannot access settings matrix
    resp_settings = client_mandor.get("/settings/permissions/")
    print(f"  -> Mandor GET /settings/permissions/ (Terlarang) -> Status {resp_settings.status_code}")
    assert resp_settings.status_code == 302, f"Mandor should be redirected from settings, got {resp_settings.status_code}"
    print("  [PASS] Hak akses Role SUPERVISOR terisolasi dengan aman.")

    # 6. Role Operasional: Storekeeper (Gudang)
    print("\n[TEST 6] Setup & Verifikasi User Role STOREKEEPER (Gudang)...")
    role_gudang = Role.objects.get(code="STOREKEEPER")
    gudang_user, _ = User.objects.get_or_create(username="gudang_agus", defaults={"first_name": "Agus Gudang"})
    gudang_user.set_password("gudang123")
    gudang_user.is_superuser = False
    gudang_user.is_staff = False
    gudang_user.save()
    p_gudang, _ = UserProfile.objects.get_or_create(user=gudang_user, defaults={"role": role_gudang})
    p_gudang.role = role_gudang
    p_gudang.save()

    client_gudang = Client()
    gudang_login = client_gudang.login(username="gudang_agus", password="gudang123")
    assert gudang_login, "Login gudang_agus gagal!"

    # Gudang can access raw materials
    resp_gudang_rm = client_gudang.get("/raw-materials/")
    print(f"  -> Gudang GET /raw-materials/ -> Status {resp_gudang_rm.status_code}")
    assert resp_gudang_rm.status_code == 200, f"Gudang should access /raw-materials/, got {resp_gudang_rm.status_code}"

    # Gudang cannot access attendance
    resp_gudang_att = client_gudang.get("/attendance/")
    print(f"  -> Gudang GET /attendance/ (Terlarang) -> Status {resp_gudang_att.status_code}")
    assert resp_gudang_att.status_code == 403, f"Gudang should be blocked from /attendance/, got {resp_gudang_att.status_code}"
    print("  [PASS] Hak akses Role STOREKEEPER terisolasi dengan aman.")

    # 7. Dynamic Permission Modification (Superadmin alters matrix)
    print("\n[TEST 7] Pengujian Perubahan Matriks Hak Akses Dinamis...")
    # Give SUPERVISOR access to MENU_RAW_MATERIAL
    perm_obj = RoleMenuPermission.objects.get(role=role_mandor, menu__code="MENU_RAW_MATERIAL")
    perm_obj.can_view = True
    perm_obj.save()
    print("  -> Superadmin memberikan izin MENU_RAW_MATERIAL ke role SUPERVISOR.")

    # Now Mandor can access raw materials immediately!
    resp_rm_after = client_mandor.get("/raw-materials/")
    print(f"  -> Mandor GET /raw-materials/ setelah izin dibuka -> Status {resp_rm_after.status_code}")
    assert resp_rm_after.status_code == 200, f"Expected 200 OK after granting permission, got {resp_rm_after.status_code}"

    # Revoke it back
    perm_obj.can_view = False
    perm_obj.save()
    print("  -> Superadmin mencabut izin MENU_RAW_MATERIAL dari role SUPERVISOR.")

    resp_rm_revoked = client_mandor.get("/raw-materials/")
    print(f"  -> Mandor GET /raw-materials/ setelah izin dicabut -> Status {resp_rm_revoked.status_code}")
    assert resp_rm_revoked.status_code == 403, f"Expected 403 after revoking permission, got {resp_rm_revoked.status_code}"
    print("  [PASS] Perubahan izin pada matriks langsung berlaku secara real-time tanpa restart!")

    # 8. User Management View actions
    print("\n[TEST 8] Pengujian Aksi Manajemen Pengguna via Web...")
    # Test superadmin creating a new user via POST
    resp_create_u = client.post("/settings/users/", {
        "action": "create_user",
        "username": "test_estimator",
        "password": "estimator123",
        "full_name": "Estimator Rian",
        "email": "rian@perusahaan.com",
        "role_uuid": str(Role.objects.get(code="ESTIMATOR").uuid),
        "phone": "08123456789",
    }, follow=True)
    assert resp_create_u.status_code == 200
    est_user = User.objects.filter(username="test_estimator").first()
    assert est_user is not None, "Pengguna test_estimator gagal dibuat via POST"
    assert est_user.profile.role.code == "ESTIMATOR", f"Expected role ESTIMATOR, got {est_user.profile.role.code}"
    print("  -> User 'test_estimator' berhasil dibuat melalui form web.")

    # Test update role of test_estimator to PROJECT_MANAGER
    pm_role = Role.objects.get(code="PROJECT_MANAGER")
    resp_update_r = client.post("/settings/users/", {
        "action": "update_role",
        "user_id": est_user.id,
        "role_uuid": str(pm_role.uuid),
    }, follow=True)
    est_user.profile.refresh_from_db()
    assert est_user.profile.role.code == "PROJECT_MANAGER"
    print(f"  -> Role 'test_estimator' berhasil diupdate menjadi '{est_user.profile.role.name}'.")

    # Clean up test user
    est_user.delete()
    print("  [PASS] Manajemen pengguna via form web berfungsi sempurna.")

    # 9. Logout Test
    print("\n[TEST 9] Verifikasi Logout...")
    resp_logout = client.get("/logout/", follow=True)
    print(f"  -> GET /logout/ -> Redirect to {resp_logout.redirect_chain[0][0]} -> Status {resp_logout.status_code}")
    assert resp_logout.status_code == 200
    assert "/login" in resp_logout.redirect_chain[0][0]
    print("  [PASS] Logout berhasil dan session dibersihkan.")

    print("\n" + "=" * 70)
    print("SELURUH TEST RBAC & LOGIN DINAMIS (9/9) BERHASIL DILALUI DENGAN SUKSES!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
