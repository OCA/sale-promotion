# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Loyalty Multi Gift",
    "summary": "Allows to configure multiple gift rewards per promotion in sales",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "AGPL-3",
    "depends": ["sale_loyalty_order_line_link", "loyalty_multi_gift"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sale_loyalty_reward_wizard_views.xml",
    ],
}
