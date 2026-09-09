"""
Menu Registry & RBAC Initial Presets
Centralized Source-of-Truth for Application Menus and Default Role Configurations.
Provides auto-sync functionality into database tables (AppMenu, Role, RoleMenuPermission).
"""

DEFAULT_ROLES = [
    {
        "code": "SUPERADMIN",
        "name": "Super Admin",
        "description": "Akses penuh ke seluruh modul, manajemen akun pengguna, dan pengaturan hak akses role.",
        "badge_color": "bg-purple-100 text-purple-800 border-purple-300",
        "is_system_role": True,
    },
    {
        "code": "PROJECT_MANAGER",
        "name": "Project Manager & Direksi",
        "description": "Pengawasan profitabilitas, pemantauan deviasi biaya HPP, closing proyek, BAP, dan laporan.",
        "badge_color": "bg-blue-100 text-blue-800 border-blue-300",
        "is_system_role": False,
    },
    {
        "code": "ESTIMATOR",
        "name": "Sales & Estimator",
        "description": "Penyusunan penawaran harga, estimasi HPP (BOM, labor, FG, overhead), salin BOM, dan customer.",
        "badge_color": "bg-indigo-100 text-indigo-800 border-indigo-300",
        "is_system_role": False,
    },
    {
        "code": "SUPERVISOR",
        "name": "Supervisor Produksi / Mandor",
        "description": "Pelaksanaan di lapangan, input & verifikasi log kinerja harian tim, realisasi proyek.",
        "badge_color": "bg-amber-100 text-amber-800 border-amber-300",
        "is_system_role": False,
    },
    {
        "code": "STOREKEEPER",
        "name": "Gudang & Logistik",
        "description": "Penerimaan & pengeluaran bahan/barang jadi, pemantauan stok fisik, dan kartu stok persediaan.",
        "badge_color": "bg-teal-100 text-teal-800 border-teal-300",
        "is_system_role": False,
    },
    {
        "code": "HRD",
        "name": "HRD & Personalia",
        "description": "Pengelolaan data induk karyawan, rekapitulasi absensi harian, dan master izin/cuti/sakit.",
        "badge_color": "bg-rose-100 text-rose-800 border-rose-300",
        "is_system_role": False,
    },
]


SYSTEM_MENUS = [
    # 1. Project & HPP
    {
        "code": "MENU_PROJECT_LIST",
        "name": "Daftar Project & HPP",
        "module": "Project & HPP",
        "url_name": "project_list",
        "icon_svg": "M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2",
        "sort_order": 10,
        "default_roles": ["SUPERADMIN", "PROJECT_MANAGER", "ESTIMATOR"],
    },
    {
        "code": "MENU_PROJECT_CREATE",
        "name": "Buat Project Baru",
        "module": "Project & HPP",
        "url_name": "project_create",
        "icon_svg": "M12 4v16m8-8H4",
        "sort_order": 11,
        "default_roles": ["SUPERADMIN", "PROJECT_MANAGER", "ESTIMATOR"],
    },
    {
        "code": "MENU_PROJECT_REALIZATION",
        "name": "Realisasi Project",
        "module": "Project & HPP",
        "url_name": "project_realization_list",
        "icon_svg": "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
        "sort_order": 12,
        "default_roles": ["SUPERADMIN", "PROJECT_MANAGER", "SUPERVISOR"],
    },
    {
        "code": "MENU_CUSTOMER_LIST",
        "name": "Master Customer",
        "module": "Project & HPP",
        "url_name": "customer_list",
        "icon_svg": "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
        "sort_order": 13,
        "default_roles": ["SUPERADMIN", "PROJECT_MANAGER", "ESTIMATOR"],
    },

    # 2. Bahan Baku
    {
        "code": "MENU_RAW_MATERIAL",
        "name": "Daftar Bahan Baku",
        "module": "Bahan Baku",
        "url_name": "raw_material_list",
        "icon_svg": "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
        "sort_order": 20,
        "default_roles": ["SUPERADMIN", "STOREKEEPER", "PROJECT_MANAGER"],
    },
    {
        "code": "MENU_RM_MUTATION",
        "name": "Mutasi Bahan Baku",
        "module": "Bahan Baku",
        "url_name": "raw_material_stock_mutation_list",
        "icon_svg": "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4",
        "sort_order": 21,
        "default_roles": ["SUPERADMIN", "STOREKEEPER", "PROJECT_MANAGER"],
    },
    {
        "code": "MENU_RM_STOCK_CARD",
        "name": "Kartu Stok Bahan",
        "module": "Bahan Baku",
        "url_name": "raw_material_stock_card_index",
        "icon_svg": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
        "sort_order": 22,
        "default_roles": ["SUPERADMIN", "STOREKEEPER", "PROJECT_MANAGER"],
    },

    # 3. Barang Jadi
    {
        "code": "MENU_FINISHED_GOOD",
        "name": "Daftar Barang Jadi",
        "module": "Barang Jadi",
        "url_name": "finished_good_list",
        "icon_svg": "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4",
        "sort_order": 30,
        "default_roles": ["SUPERADMIN", "STOREKEEPER", "PROJECT_MANAGER"],
    },
    {
        "code": "MENU_FG_MUTATION",
        "name": "Mutasi Barang Jadi",
        "module": "Barang Jadi",
        "url_name": "finished_good_mutation_list",
        "icon_svg": "M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4",
        "sort_order": 31,
        "default_roles": ["SUPERADMIN", "STOREKEEPER", "PROJECT_MANAGER"],
    },
    {
        "code": "MENU_FG_STOCK_CARD",
        "name": "Kartu Stok Barang",
        "module": "Barang Jadi",
        "url_name": "finished_good_stock_card_index",
        "icon_svg": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
        "sort_order": 32,
        "default_roles": ["SUPERADMIN", "STOREKEEPER", "PROJECT_MANAGER"],
    },

    # 4. SDM & Tenaga Kerja
    {
        "code": "MENU_ATTENDANCE",
        "name": "Rekap Absensi Harian",
        "module": "SDM & Tenaga Kerja",
        "url_name": "attendance_list",
        "icon_svg": "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
        "sort_order": 40,
        "default_roles": ["SUPERADMIN", "HRD", "SUPERVISOR", "PROJECT_MANAGER"],
    },
    {
        "code": "MENU_WORK_LOG",
        "name": "Log Kinerja & Kegiatan",
        "module": "SDM & Tenaga Kerja",
        "url_name": "work_log_list",
        "icon_svg": "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
        "sort_order": 41,
        "default_roles": ["SUPERADMIN", "SUPERVISOR", "PROJECT_MANAGER"],
    },
    {
        "code": "MENU_EMPLOYEE",
        "name": "Master Data Karyawan",
        "module": "SDM & Tenaga Kerja",
        "url_name": "employee_list",
        "icon_svg": "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
        "sort_order": 42,
        "default_roles": ["SUPERADMIN", "HRD"],
    },
    {
        "code": "MENU_ABSENCE_TYPE",
        "name": "Master Jenis Tidak Masuk",
        "module": "SDM & Tenaga Kerja",
        "url_name": "absence_type_list",
        "icon_svg": "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
        "sort_order": 43,
        "default_roles": ["SUPERADMIN", "HRD"],
    },

    # 5. Master Satuan
    {
        "code": "MENU_UNIT_MASTER",
        "name": "Master Satuan",
        "module": "Master Satuan",
        "url_name": "unit_list",
        "icon_svg": "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
        "sort_order": 50,
        "default_roles": ["SUPERADMIN", "PROJECT_MANAGER", "ESTIMATOR", "STOREKEEPER"],
    },

    # 6. Panduan & Sistem
    {
        "code": "MENU_USER_JOURNEY",
        "name": "User Journey & Alur",
        "module": "Panduan & Sistem",
        "url_name": "user_journey",
        "icon_svg": "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
        "sort_order": 60,
        "default_roles": ["SUPERADMIN", "PROJECT_MANAGER", "ESTIMATOR", "SUPERVISOR", "STOREKEEPER", "HRD"],
    },
    {
        "code": "MENU_ADVANTAGES",
        "name": "Keunggulan Sistem",
        "module": "Panduan & Sistem",
        "url_name": "app_advantages",
        "icon_svg": "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z",
        "sort_order": 61,
        "default_roles": ["SUPERADMIN", "PROJECT_MANAGER", "ESTIMATOR", "SUPERVISOR", "STOREKEEPER", "HRD"],
    },

    # 7. Pengaturan & Hak Akses (Khusus Superadmin)
    {
        "code": "MENU_ROLE_MATRIX",
        "name": "Matriks Hak Akses",
        "module": "Pengaturan & Hak Akses",
        "url_name": "role_permission_matrix",
        "icon_svg": "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
        "sort_order": 70,
        "default_roles": ["SUPERADMIN"],
    },
    {
        "code": "MENU_USER_MANAGE",
        "name": "Manajemen Pengguna",
        "module": "Pengaturan & Hak Akses",
        "url_name": "user_manage_list",
        "icon_svg": "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
        "sort_order": 71,
        "default_roles": ["SUPERADMIN"],
    },
]


def sync_menu_registry():
    """
    Auto-Sync helper:
    1. Creates/Updates Roles in DEFAULT_ROLES.
    2. Creates/Updates AppMenu entries from SYSTEM_MENUS.
    3. Seeds initial RoleMenuPermission for any newly registered menus.
    Safe to call repeatedly on startup, view, or migration.
    """
    from .models import Role, AppMenu, RoleMenuPermission

    role_objs = {}
    for r_data in DEFAULT_ROLES:
        role, _ = Role.objects.get_or_create(
            code=r_data["code"],
            defaults={
                "name": r_data["name"],
                "description": r_data["description"],
                "badge_color": r_data["badge_color"],
                "is_system_role": r_data["is_system_role"],
            }
        )
        role_objs[r_data["code"]] = role

    for m_data in SYSTEM_MENUS:
        menu, created = AppMenu.objects.get_or_create(
            code=m_data["code"],
            defaults={
                "name": m_data["name"],
                "module": m_data["module"],
                "url_name": m_data["url_name"],
                "icon_svg": m_data.get("icon_svg", ""),
                "sort_order": m_data.get("sort_order", 0),
                "is_active": True,
            }
        )
        if not created:
            # Update attributes if modified in code
            menu.name = m_data["name"]
            menu.module = m_data["module"]
            menu.url_name = m_data["url_name"]
            menu.icon_svg = m_data.get("icon_svg", "")
            menu.sort_order = m_data.get("sort_order", 0)
            menu.save(update_fields=["name", "module", "url_name", "icon_svg", "sort_order"])

        # Seed default permissions for roles
        default_roles = m_data.get("default_roles", ["SUPERADMIN"])
        for role_code, role in role_objs.items():
            # If role is superadmin, always True. If in default_roles, True.
            should_have_access = (role_code == "SUPERADMIN") or (role_code in default_roles)
            if created:
                RoleMenuPermission.objects.get_or_create(
                    role=role,
                    menu=menu,
                    defaults={"can_view": should_have_access}
                )
            else:
                # Ensure record exists without overwriting existing customized settings
                RoleMenuPermission.objects.get_or_create(
                    role=role,
                    menu=menu,
                    defaults={"can_view": should_have_access}
                )
