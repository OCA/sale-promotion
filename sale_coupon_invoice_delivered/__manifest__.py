# Copyright 2022 Akretion - Florian Mounier
{
    "name": "Sale Coupon Invoice Delivered",
    "summary": "This module handle partial promotion quantity on "
    "partially delivered sale order",
    "version": "14.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["sale_coupon", "sale_stock"],
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "data": [
        "views/coupon_program_views.xml",
    ],
    "auto_install": True,
}
