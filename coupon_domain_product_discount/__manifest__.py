# Copyright 2022 Ooops404
# Copyright 2022 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Stefan Ungureanu
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Coupon Promotion Product Domain Discount",
    "version": "15.0.1.0.0",
    "summary": "Apply discount only to the domain matching products",
    "author": "Ooops, Cetmix, Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Sales Management",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["sale_coupon"],
    "data": ["views/coupon_program_views.xml"],
    "installable": True,
    "application": False,
}
