import ast
import logging

from odoo import SUPERUSER_ID, api
from odoo.osv import expression

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "Migrating loyalty partners applicability domain from rules to programs"
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    programs = env["loyalty.program"].search([])
    cr.execute(
        """
        SELECT
            id,
            rule_partners_domain
        FROM loyalty_rule
        WHERE rule_partners_domain IS NOT NULL AND rule_partners_domain != '[]'
        """
    )
    domain_by_rule = {row[0]: row[1] for row in cr.fetchall()}
    for program in programs:
        program_partner_domains = []
        for rule in program.rule_ids:
            domain = domain_by_rule.get(rule.id, "[]")
            py_domain = ast.literal_eval(domain)
            if py_domain and py_domain not in program_partner_domains:
                program_partner_domains.append(py_domain)
                _logger.info(
                    f"Adding domain {py_domain} to program {program.name} "
                    "from rule {rule.display_name}"
                )
        if program_partner_domains:
            domain = (
                expression.OR(program_partner_domains)
                if len(program_partner_domains) > 1
                else program_partner_domains[0]
            )
            program.write({"partner_domain": str(domain)})
            _logger.info(
                f"Set domain {program.partner_domain} to program {program.name}"
            )
