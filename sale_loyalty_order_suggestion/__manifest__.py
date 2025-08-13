# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Loyalty Suggestions",
    "summary": "Suggest promotions in the sale order line",
    "version": "18.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["pilarvargas-tecnativa"],
    "license": "AGPL-3",
    "depends": ["sale_loyalty"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "wizard/sale_loyalty_reward_wizard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/sale_loyalty_order_suggestion/static/src/js/suggest_promotion_widget.esm.js",
            "/sale_loyalty_order_suggestion/static/src/xml/suggest_promotion.xml",
        ],
    },
    "installable": True,
}
