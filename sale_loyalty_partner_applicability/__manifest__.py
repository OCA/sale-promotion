# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Loyalty Partner Applicability",
    "summary": "Enables the definition of a customer filter for promotion rules that will "
    "only be applied to customers who meet the specified conditions in the filter.",
    "version": "16.0.1.0.2",
    "category": "Sale",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["sale_loyalty", "loyalty_partner_applicability"],
    "data": [
        "views/res_config_settings.xml",
    ],
}
