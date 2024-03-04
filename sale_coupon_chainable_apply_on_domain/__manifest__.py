# Copyright 2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Coupon Chainable Apply On Domain",
    "summary": "This allows to use chainable discounts on product domain discounts.",
    "version": "14.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": [
        "sale_coupon_apply_on_domain",
        "sale_coupon_chainable",
    ],
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "data": [
        "views/coupon_program_views.xml",
    ],
    "auto_install": True,
}
