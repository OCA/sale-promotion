# Copyright 2021 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Website Sale Coupon Page",
    "version": "13.0.2.0.0",
    "category": "Website",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["website_sale_coupon"],
    "data": [
        "templates/assets.xml",
        "views/sale_coupon_program_views.xml",
        "templates/promotion_templates.xml",
    ],
}
