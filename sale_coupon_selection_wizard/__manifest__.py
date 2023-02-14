# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Coupons Selection Wizard",
    "summary": "A wizard that allows salesmen to easily pick the best promotions",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": ["sale_coupon_criteria_multi_product", "sale_coupon_multi_gift"],
    "data": [
        "wizards/coupon_selection_wizard_views.xml",
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/sale_coupon_selection_wizard/static/src/scss/*.scss",
            "/sale_coupon_selection_wizard/static/src/js/*.js",
        ],
    },
}
