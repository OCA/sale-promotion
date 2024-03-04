# Copyright 2021-2023 Akretion France (http://www.akretion.com)
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Coupon Chainable",
    "summary": "This module add a new chainable option in coupon/promotion "
    "programs that allows to apply the current discount on the discounted "
    "price from previous programs and respect discount order.",
    "version": "14.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-promotion",
    "depends": ["sale_coupon", "base_sale_coupon_chainable"],
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "data": [
        "views/coupon_program_views.xml",
        "views/res_config_settings_views.xml",
    ],
}
