# Copyright 2024 (APSL-Nagarro) - Antoni Marroig
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Loyalty Card Fixed Expiration Date",
    "summary": "Set a fixed expiration date for loyalty cards",
    "version": "17.0.1.0.0",
    "category": "POS",
    "author": "(APSL-Nagarro), Odoo Community Association (OCA)",
    "maintainers": ["peluko00", "BernatObrador"],
    "website": "https://github.com/OCA/sale-promotion",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "loyalty",
    ],
    "data": [
        "views/loyalty_program_views.xml",
    ],
}
