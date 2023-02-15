# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Coupons Suggestions",
    "summary": "Suggest promotions in the sale order line",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": ["sale_coupon_selection_wizard"],
    "data": ["views/sale_order_views.xml"],
    "assets": {
        "web.assets_backend": [
            "/sale_coupon_order_suggestion/static/src/js/suggest_promotion_widget.esm.js",
        ],
        "web.assets_qweb": [
            "/sale_coupon_order_suggestion/static/src/xml/suggest_promotion.xml",
        ],
    },
    "installable": True,
}
