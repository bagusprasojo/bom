from django.utils import timezone
from .models import Project

def generate_project_code():
    now = timezone.now()
    prefix = f"PRJ-{now.strftime('%Y%m')}-"
    last_project = Project.objects.filter(code__startswith=prefix).order_by("-code").first()
    if last_project:
        try:
            last_seq = int(last_project.code.split("-")[-1])
            new_seq = last_seq + 1
        except ValueError:
            new_seq = 1
    else:
        new_seq = 1
    return f"{prefix}{new_seq:04d}"


def get_ordered_bom(project):
    """
    Mengurutkan BOM secara hierarki Tree (Depth-First Search):
    Parent / Sub-Assembly selalu tampil teratas sebelum seluruh child/anaknya.
    Menyematkan atribut `tree_depth` untuk keperluan indentasi visual di template.
    """
    all_items = list(project.bom_items.all().select_related("material_master", "parent"))
    children_map = {}
    roots = []

    for item in all_items:
        p_id = item.parent_id
        if p_id is None:
            roots.append(item)
        else:
            if p_id not in children_map:
                children_map[p_id] = []
            children_map[p_id].append(item)

    ordered = []
    def traverse(node, depth=0):
        node.tree_depth = depth
        ordered.append(node)
        for child in children_map.get(node.id, []):
            traverse(child, depth + 1)

    for root in roots:
        traverse(root, 0)

    return ordered
