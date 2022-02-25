# Copyright 2021 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "gift_card",
    "summary": "Gift Card as a payment mode",
    "version": "14.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-promotion",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["Kev-Roche"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "account",
        "base_generate_code",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/gift_card_template.xml",
        "views/res_config_setting.xml",
        "views/gift_card.xml",
        "views/gift_card_line.xml",
        "wizards/account_payment_register_views.xml",
    ],
}
