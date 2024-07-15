# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Coupons Selection for eCommerce",
    "summary": "Allows to apply and configure promotions directly from the website",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "category": "eCommerce",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": [
        "sale_coupon_selection_wizard",
        "sale_coupon_order_suggestion",
        "website_sale_coupon_page",
    ],
    "data": ["templates/promotion_templates.xml"],
    "assets": {
        "web.assets_frontend": [
            "/website_sale_coupon_selection_wizard/static/src/scss/"
            "website_sale_coupon_selection.scss",
            "/sale_coupon_selection_wizard/static/src/js/"
            "coupon_selection_wizard_mixin.js",
            "/website_sale_coupon_selection_wizard/static/src/js/"
            "website_sale_coupon_selection_wizard.js",
        ]
    },
}
