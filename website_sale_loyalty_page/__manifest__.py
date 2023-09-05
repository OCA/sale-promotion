# Copyright 2021 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Website Sale Loyalty Page",
    "version": "16.0.1.0.0",
    "category": "Website",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["website_sale_loyalty"],
    "data": [
        "views/sale_loyalty_program_views.xml",
        "templates/promotion_templates.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "/website_sale_loyalty_page/static/src/js/website_sale_loyalty_page_portal.js",
        ]
    },
}
