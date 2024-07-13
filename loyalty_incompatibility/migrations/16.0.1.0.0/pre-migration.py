# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_tables(
        env.cr,
        [
            (
                "sale_coupon_program_incompatibility_rel",
                "sale_loyalty_program_incompatibility_rel",
            )
        ],
    )
