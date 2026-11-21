from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fns_vendor_price_ids = fields.One2many(
        "fns.vendor.price", "product_tmpl_id", "Vendor Source Prices", groups="base.group_user",
    )
    fns_current_vendor_price_id = fields.Many2one(
        "fns.vendor.price", "Current Vendor Price", compute="_compute_fns_current_vendor_price",
        groups="base.group_user",
        help="Most recent vendor price whose effective date is today or earlier.",
    )
    fns_price_effective_date = fields.Date(
        "Price Effective Date", compute="_compute_fns_current_vendor_price", groups="base.group_user",
        help="Effective date of the vendor price sheet that sets the current source prices.",
    )
    fns_vendor_currency_id = fields.Many2one(
        "res.currency", "Vendor Price Currency", compute="_compute_fns_current_vendor_price",
        groups="base.group_user",
    )
    fns_map_price = fields.Monetary(
        "Current MAP Price", compute="_compute_fns_current_vendor_price",
        currency_field="fns_vendor_currency_id", groups="base.group_user",
    )
    fns_dealer_price = fields.Monetary(
        "Current Dealer Price", compute="_compute_fns_current_vendor_price",
        currency_field="fns_vendor_currency_id", groups="base.group_user",
    )

    @api.depends(
        "fns_vendor_price_ids.effective_date", "fns_vendor_price_ids.currency_id",
        "fns_vendor_price_ids.map_price", "fns_vendor_price_ids.dealer_price",
    )
    @api.depends_context("tz")
    def _compute_fns_current_vendor_price(self):
        today = fields.Date.context_today(self)
        for product in self:
            effective = product.fns_vendor_price_ids.filtered(lambda price: price.effective_date <= today)
            current = max(
                effective, key=lambda price: (price.effective_date, price.sheet_id.id, price.id),
                default=self.env["fns.vendor.price"],
            )
            product.fns_current_vendor_price_id = current
            product.fns_price_effective_date = current.effective_date
            product.fns_vendor_currency_id = current.currency_id
            product.fns_map_price = current.map_price
            product.fns_dealer_price = current.dealer_price
