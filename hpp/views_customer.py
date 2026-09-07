from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Customer

def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.all().order_by("name")
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(code__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    return render(request, "hpp/customer_list.html", {
        "customers": customers,
        "query": query,
    })

def customer_create(request):
    if request.method == "POST":
        is_ajax = (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or request.POST.get("is_ajax") == "1"
            or request.GET.get("format") == "json"
        )
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        company_name = request.POST.get("company_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not name:
            if is_ajax:
                return JsonResponse({"status": "error", "message": "Nama customer wajib diisi."}, status=400)
            messages.error(request, "Nama customer wajib diisi.")
            return redirect("customer_list")

        if not code:
            last_cust = Customer.objects.order_by("-id").first()
            next_id = (last_cust.id + 1) if last_cust else 1
            code = f"CUST-{next_id:03d}"

        if Customer.objects.filter(code=code).exists():
            if is_ajax:
                return JsonResponse({"status": "error", "message": f"Kode customer {code} sudah digunakan."}, status=400)
            messages.error(request, f"Kode customer {code} sudah digunakan.")
            return redirect("customer_list")

        customer = Customer.objects.create(
            code=code,
            name=name,
            company_name=company_name,
            phone=phone,
            email=email,
            address=address,
            notes=notes,
        )

        if is_ajax:
            return JsonResponse({
                "status": "success",
                "message": f"Customer '{name}' berhasil didaftarkan.",
                "customer": {
                    "uuid": str(customer.uuid),
                    "code": customer.code,
                    "name": customer.name,
                    "company_name": customer.company_name,
                    "label": str(customer),
                }
            })

        messages.success(request, f"Customer '{name}' berhasil ditambahkan.")
    return redirect("customer_list")

def customer_update(request, uuid):
    customer = get_object_or_404(Customer, uuid=uuid)
    if request.method == "POST":
        customer.code = request.POST.get("code", customer.code).strip()
        customer.name = request.POST.get("name", customer.name).strip()
        customer.company_name = request.POST.get("company_name", "").strip()
        customer.phone = request.POST.get("phone", "").strip()
        customer.email = request.POST.get("email", "").strip()
        customer.address = request.POST.get("address", "").strip()
        customer.notes = request.POST.get("notes", "").strip()
        customer.save()
        messages.success(request, f"Data customer '{customer.name}' berhasil diperbarui.")
    return redirect("customer_list")

def customer_delete(request, uuid):
    customer = get_object_or_404(Customer, uuid=uuid)
    if customer.projects.exists():
        messages.error(request, f"Customer '{customer.name}' tidak dapat dihapus karena masih digunakan di {customer.projects.count()} project.")
    else:
        name = customer.name
        customer.delete()
        messages.success(request, f"Customer '{name}' berhasil dihapus.")
    return redirect("customer_list")
