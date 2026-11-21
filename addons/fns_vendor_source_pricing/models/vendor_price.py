from odoo import fields, models


class FnsVendorPrice(models.Model):
    _name = "fns.vendor.price"
    _description = "Vendor Source Price"
    _order = "effective_date desc, sheet_id desc, id desc"
    _rec_name = "product_tmpl_id"

    sheet_id = fields.Many2one(
        "fns.vendor.price.sheet", "Price Sheet", required=True, index=True, ondelete="cascade",
    )
    product_tmpl_id = fields.Many2one(
        "product.template", "Product", required=True, index=True, ondelete="cascade",
    )
    partner_id = fields.Many2one(related="sheet_id.partner_id", store=True, index=True)
    effective_date = fields.Date(related="sheet_id.effective_date", store=True, index=True)
    currency_id = fields.Many2one(related="sheet_id.currency_id", store=True)
    vendor_sku = fields.Char("Vendor SKU")
    map_price = fields.Monetary(
        "MAP Price", currency_field="currency_id",
        help="Minimum advertised price published by the vendor.",
    )
    dealer_price = fields.Monetary(
        "Dealer Price", currency_field="currency_id",
        help="Price the vendor charges the shop (Dive Rite calls it Partner Price).",
    )
    source_note = fields.Char("Source Detail", help="Where on the source document the price appears.")

    _sheet_product_unique = models.Constraint(
        "unique(sheet_id, product_tmpl_id)",
        "A product can appear only once on a vendor price sheet.",
    )
    _prices_not_negative = models.Constraint(
        "CHECK(coalesce(map_price, 0) >= 0 AND coalesce(dealer_price, 0) >= 0)",
        "Vendor prices cannot be negative.",
    )
