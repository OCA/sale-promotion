This module extends the Loyalty functionality by allowing the definition of a customer
filter for promotion rules. This module is a base to be extended.

It allows to restrict the applicability of a promotion and its rules to a subset of customers.
This is useful when you want to target a specific group of customers with a promotion.
The restriction can be defined at 2 levels:

- The program
- The rule

When a restriction is defined at the program level, the promotion will only be available to
customers that match the filter. When a restriction is defined at the rule level, the rule
will only be applied to customers that match the filter. If a restriction is defined at both
levels, the program's rules will only be applied to customers that match both filters.