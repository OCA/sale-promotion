# Copyright 2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env["loyalty.rule"].search([("loyalty_criteria", "=", "multi_product")]).write(
        {"minimum_qty": 0.0}
    )
