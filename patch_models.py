with open("hpp/models.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

# Tambahkan model Customer
customer_model = """class Customer(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.CharField(max_length=100, blank=True, default="")
    address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"[{self.code}] {self.name}"
"""

# Sisipkan sebelum class Project
if "class Customer" not in text:
    text = text.replace("class Project(models.Model):", customer_model + "\n\nclass Project(models.Model):\n    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')")

with open("hpp/models.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

print("Customer model added to models.py")
