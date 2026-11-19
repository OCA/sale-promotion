# Copyright 2026 INVITU (<https://www.invitu.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "POS Loyalty Order Line Change Variant",
    "summary": "Recompute loyalty rewards after changing the variant of a PoS line",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Point of Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "INVITU, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["pos_loyalty", "pos_order_line_change_variant"],
    "auto_install": True,
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_loyalty_order_line_change_variant/static/src/**/*.js",
        ],
        "web.assets_tests": [
            "pos_loyalty_order_line_change_variant/static/tests/tours/**/*",
        ],
    },
}
