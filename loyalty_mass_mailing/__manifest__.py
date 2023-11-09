# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Loyalty Mass Mailing",
    "version": "16.0.1.0.0",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-promotion",
    "license": "AGPL-3",
    "category": "Marketing",
    "depends": ["loyalty_partner_applicability", "mass_mailing"],
    "data": ["views/mailing_mailing_view.xml", "views/loyalty_program_view.xml"],
    "installable": True,
}
