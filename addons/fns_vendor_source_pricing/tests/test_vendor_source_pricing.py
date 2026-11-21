from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestVendorSourcePricing(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor", "is_company": True})
        cls.product = cls.env["product.template"].create({"name": "Test Regulator"})
        cls.usd = cls.env.ref("base.USD")

    def _sheet(self, days, name):
        return self.env["fns.vendor.price.sheet"].create({
            "name": name, "partner_id": self.vendor.id, "currency_id": self.usd.id,
            "effective_date": self.today + timedelta(days=days),
        })

    def _price(self, sheet, map_price, dealer_price):
        return self.env["fns.vendor.price"].create({
            "sheet_id": sheet.id, "product_tmpl_id": self.product.id,
            "map_price": map_price, "dealer_price": dealer_price,
        })

    def test_current_price_uses_latest_effective_sheet_and_keeps_history(self):
        old = self._price(self._sheet(-60, "Old"), 100, 60)
        current = self._price(self._sheet(-1, "Current"), 110, 66)
        future = self._price(self._sheet(30, "Future"), 120, 72)
        self.assertEqual(self.product.fns_vendor_price_ids, old | current | future)
        self.assertEqual(self.product.fns_current_vendor_price_id, current)
        self.assertEqual(self.product.fns_price_effective_date, self.today - timedelta(days=1))
        self.assertEqual(self.product.fns_map_price, 110)
        self.assertEqual(self.product.fns_dealer_price, 66)
        self.assertEqual(current.partner_id, self.vendor)

    def test_only_future_sheet_has_no_current_price(self):
        self._price(self._sheet(1, "Future"), 120, 72)
        self.assertFalse(self.product.fns_current_vendor_price_id)
        self.assertFalse(self.product.fns_price_effective_date)

    def test_product_appears_once_per_sheet(self):
        sheet = self._sheet(0, "Today")
        self._price(sheet, 100, 60)
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._price(sheet, 101, 61)

    def test_negative_price_rejected(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError), self.cr.savepoint():
            self._price(self._sheet(0, "Today"), -1, 60)
