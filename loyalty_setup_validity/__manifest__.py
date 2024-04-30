# Copyright 2024 Moka Tourisme (https://www.mokatourisme.fr/).
# @author Damien Horvat <ultrarushgame@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Loyalty Setup Validity",
    "version": "16.0.1.0.0",
    "category": "Sale",
    "author": "Moka, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-promotion",
    "summary": (
        "Allow to define a fixed validity or a validity after"
        " the generation date of a loyalty card."
    ),
    "depends": ["loyalty"],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "data": ["views/loyalty_program_inherit.xml"],
}
