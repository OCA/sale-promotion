# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def _fill_reward_id_field(env):
    for line in env["sale.order.line"].filtered("loyalty_program_id"):
        line.reward_id = env["loyalty.reward"].search(
            [["program_id", "=", line.loyalty_program_id.id]]
        )


@openupgrade.migrate()
def migrate(env, version):
    _fill_reward_id_field(env)
