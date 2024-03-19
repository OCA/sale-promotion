You can set this feature on or off in every company. To do so:

#. Go to *Sales > Configuration > Settings*
#. In the *Pricing* section you'll find the option *Auto refresh promotions*.

The auto-refresh in the backend is triggered over a minimum set of fields changes. If
you want to extend the list of that fields:

#. Go to *Settings > Technical > Config parameters*
#. Add or update the key:

   - For `sale.order`: `sale_loyalty_auto_refresh.sale_order_triggers`
   - For `sale.order.line`: `sale_loyalty_auto_refresh.sale_order_line_triggers`
#. In every add the fields seperated by commas that you want to add to the recomputation
   triggers.

⚠️ After configuring or removing a trigger a restart of Odoo is recommended so the
depends are reloaded properly. Anyway it isn't mandatory and the module detects the
new triggers so the auto-refresh works as expected as soon as they are set.
