# Copyright 2024 Moka Tourisme (https://www.mokatourisme.fr/).
# @author Damien Horvat <ultrarushgame@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Loyalty Partner Birthdate",
    "version": "16.0.1.0.0",
    "category": "Sale",
    "author": "Moka",
    "website": "https://github.com/OCA/sale-promotion",
    "summary": "Implement a cron job to launch the generation of loyalty where conditions are set on the partner's birthdate.",
    "depends": ["loyalty", "loyalty_setup_validity", "partner_contact_birthdate"],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "data": ["views/loyalty_program_views_inherit.xml", "data/ir_cron_data.xml"],
}