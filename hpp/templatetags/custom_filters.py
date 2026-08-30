from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name="rupiah")
def rupiah_format(value):
    """
    Format angka format Indonesia:
    - Pemisah ribuan: titik (.)
    - Pemisah desimal: koma (,)
    - Jika desimal 00 -> tampil bulat tanpa desimal
    - Maks 2 desimal jika ada pecahan
    """
    if value is None or value == "":
        return "0"
    try:
        val = Decimal(str(value))
    except Exception:
        return value

    # Cek jika bilangan bulat
    if val % 1 == 0:
        formatted = f"{int(val):,}".replace(",", ".")
        return formatted
    
    # Ada pecahan desimal (maks 2 digit)
    formatted = f"{val:,.2f}"
    # Ubah format US (1,234.56) -> ID (1.234,56)
    main_part, dec_part = formatted.split(".")
    main_part = main_part.replace(",", ".")
    return f"{main_part},{dec_part}"
