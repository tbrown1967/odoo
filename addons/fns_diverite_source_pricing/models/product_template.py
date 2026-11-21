from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_fns_diverite_map_price = fields.Float(
        "MAP Price", groups="base.group_user", readonly=True, copy=False,
    )
    x_fns_diverite_partner_price = fields.Float(
        "Partner Price", groups="base.group_user", readonly=True, copy=False,
    )
    x_fns_diverite_source = fields.Char(
        "Price Source and Currency", groups="base.group_user", readonly=True, copy=False,
    )
