{
    "name": "Sale coupon free shipping default product",
    "summary": """avoids creating multiple free shipping products and
    creating multiple discount products if a coupon program is duplicated""",
    "version": "14.0.1.0.0",
    "category": "Hidden/Tools",
    "author": "Ooops, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-promotion",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["sale", "coupon", "sale_coupon_delivery"],
    "data": ["views/res_config_settings_views.xml"],
    "auto_install": False,
}
