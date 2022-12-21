# Copyright 2021 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Website Sale Coupon Page",
    "version": "15.0.1.0.0",
    "category": "Website",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["website_sale_coupon"],
    "data": [
        "views/sale_coupon_program_views.xml",
        "templates/promotion_templates.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "/website_sale_coupon_page/static/src/js/website_sale_coupon_page_admin.js",
            "/website_sale_coupon_page/static/src/js/website_sale_coupon_page_portal.js",
        ]
    },
}
