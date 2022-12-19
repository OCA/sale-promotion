# Copyright 2022 Dinar Gabbasov
# Copyright 2022 Ooops404
# Copyright 2022 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Coupon Promotion Product Exclude",
    "version": "14.0.1.0.0",
    "summary": "Apply a discount to the order, excluding products matching the domain",
    "author": "Ooops, Cetmix, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Sales Management",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["sale_coupon"],
    "data": ["views/coupon_program_views.xml"],
    "installable": True,
    "application": False,
}
