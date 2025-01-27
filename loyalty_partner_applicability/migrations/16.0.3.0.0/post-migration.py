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
    for program in programs:
        program_partner_domains = []
        for rule in program.rule_ids:
            domain = rule.partner_domain
            py_domain = ast.literal_eval(domain)
            if py_domain and py_domain not in program_partner_domains:
                program_partner_domains.append(py_domain)
                _logger.info(
                    f"Adding domain {py_domain} to program {program.name} "
                    "from rule {rule.display_name}"
                )
            rule.write({"partner_domain": "[]"})
        if program_partner_domains:
            program.write(
                {"partner_domain": str(expression.OR(program_partner_domains))}
            )
            _logger.info(
                f"Set domain {program.partner_domain} to program {program.name}"
            )
