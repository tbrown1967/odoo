from odoo import api, fields, models


class FnsVendorPriceSheet(models.Model):
    _name = "fns.vendor.price.sheet"
    _description = "Vendor Price Sheet"
    _order = "effective_date desc, id desc"

    name = fields.Char(required=True)
    partner_id = fields.Many2one(
        "res.partner", "Vendor", required=True, index=True, ondelete="restrict",
    )
    effective_date = fields.Date(
        required=True, index=True,
        help="Date from which the vendor's prices on this sheet apply.",
    )
    currency_id = fields.Many2one("res.currency", required=True, ondelete="restrict")
    source_document = fields.Char(help="Vendor document the prices were read from.")
    source_sha256 = fields.Char("Source SHA-256", help="Checksum of the source document.")
    line_ids = fields.One2many("fns.vendor.price", "sheet_id", "Prices")
    line_count = fields.Integer("Products", compute="_compute_line_count")

    @api.depends("line_ids")
    def _compute_line_count(self):
        counts = dict(self.env["fns.vendor.price"]._read_group(
            [("sheet_id", "in", self.ids)], ["sheet_id"], ["__count"],
        ))
        for sheet in self:
            sheet.line_count = counts.get(sheet, 0)
