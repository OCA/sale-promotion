import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Rename rule_partners_domain to partner_domain in loyalty rule")
    cr.execute(
        "ALTER TABLE loyalty_rule RENAME COLUMN rule_partners_domain TO partner_domain"
    )
