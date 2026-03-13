import unittest
from unittest.mock import Mock

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError

class TestPricingService(unittest.TestCase):
    
	def test_subtotal_cents_returns_unit_price_error_when_units_are_cero_or_negative(self):

		instance = PricingService()
		
		negative_price = CartItem(sku="B", unit_price_cents=-1000, qty=1)
		self.assertRaisesRegex(PricingError, "unit_price_cents must be >= 0", instance.subtotal_cents, [negative_price])

	def test_subtotal_cents_returns_qty_condition_when_qty_is_zero_or_negative(self):

		instance = PricingService()

		negative_qty = CartItem(sku="A", unit_price_cents=1000, qty=-1)
		self.assertRaisesRegex(PricingError, "qty must be > 0", instance.subtotal_cents, [negative_qty])

		cero_qty = CartItem(sku="I", unit_price_cents=1000, qty=0)
		self.assertRaisesRegex(PricingError, "qty must be > 0", instance.subtotal_cents, [cero_qty])

	def test_subtotal_cents_returns_TypeError_when_unit_price_cents_or_qty_is_none(self):

		instance = PricingService()

		no_price = CartItem(sku="F", unit_price_cents=None, qty=1)
		self.assertRaises(TypeError, instance.subtotal_cents, [no_price])

		no_qty = CartItem(sku="G", unit_price_cents=1000, qty=None)
		self.assertRaises(TypeError, instance.subtotal_cents, [no_qty])

	def test_subtotal_cents_returns_expected_value(self):

		instance = PricingService()

		self.assertEqual(instance.subtotal_cents([]), 0)

		positive = CartItem(sku="C", unit_price_cents=1000, qty=1)
		self.assertEqual(instance.subtotal_cents([positive]), 1000)
		
		decimal_qty = CartItem(sku="D", unit_price_cents=1000, qty=1.5)
		self.assertEqual(instance.subtotal_cents([decimal_qty]), 1500)

		decimal_price = CartItem(sku="E", unit_price_cents=1000.5, qty=1)
		self.assertEqual(instance.subtotal_cents([decimal_price]), 1000.5)

		cero_price = CartItem(sku="H", unit_price_cents=0, qty=1)
		self.assertEqual(instance.subtotal_cents([cero_price]), 0)


	def test_apply_coupon_SAVE10_returns_10_discount(self):

		instance = PricingService()

		self.assertEqual(instance.apply_coupon(10000, "save10"), 9000)
		self.assertEqual(instance.apply_coupon(10000, "SAVE10"), 9000)
		self.assertEqual(instance.apply_coupon(10000, "SaVe10"), 9000)
		self.assertEqual(instance.apply_coupon(-1000, "SAVE10"), -900)

	def test_apply_coupon_returns_same_value_when_coupon_is_none(self):

		instance = PricingService()

		self.assertEqual(instance.apply_coupon(10000, None), 10000)
		self.assertEqual(instance.apply_coupon(10000, ""), 10000)
		self.assertEqual(instance.apply_coupon(10000, "   "), 10000)

	def test_apply_coupon_returns_2000_discount_with_CLP_coupon(self):

		instance = PricingService()

		self.assertEqual(instance.apply_coupon(10000, "CLP2000"), 8000)
		self.assertEqual(instance.apply_coupon(10000, "clp2000"), 8000)
		self.assertEqual(instance.apply_coupon(10000, "cLp2000"), 8000)
		self.assertEqual(instance.apply_coupon(1000, "CLP2000"), 0)
		self.assertEqual(instance.apply_coupon(-1000, "CLP2000"), 0)

	def test_apply_coupon_returns_invalid_with_and_invalid_argument(self):

		instance = PricingService()

		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "INVALID")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "SALE10")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "100%")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "save20")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "SAVE20")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "SaVe20")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "CLP4000")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "clp4000")
		self.assertRaisesRegex(PricingError, "invalid coupon", instance.apply_coupon, 10000, "cLp4000")

	def test_apply_coupon_returns_cero_when_price_is_cero(self):

		instance = PricingService()

		self.assertEqual(instance.apply_coupon(0, "SAVE10"), 0)
		self.assertEqual(instance.apply_coupon(0, "CLP2000"), 0)		

	def test_tax_cents_applies_expected_discount_for_CL(self):

		instance = PricingService()

		self.assertEqual(instance.tax_cents(10000, "CL"), 1900)
		self.assertEqual(instance.tax_cents(10000, " cl "), 1900)
		self.assertEqual(instance.tax_cents(0, "CL"), 0)
		self.assertEqual(instance.tax_cents(-1000, "CL"), -190)

	def test_tax_cents_applies_expected_discount_for_EU(self):

		instance = PricingService()

		self.assertEqual(instance.tax_cents(10000, "EU"), 2100)
		self.assertEqual(instance.tax_cents(10000, "eu"), 2100)
		self.assertEqual(instance.tax_cents(0, "EU"), 0)
		self.assertEqual(instance.tax_cents(-1000, "EU"), -210)

	def test_tax_cents_applies_expected_discount_for_US(self):

		instance = PricingService()

		self.assertEqual(instance.tax_cents(10000, "US"), 0)
		self.assertEqual(instance.tax_cents(10000, " us "), 0)	

	def test_tax_cents_returns_unsupported_country_for_invalid_countries(self):

		instance = PricingService()

		self.assertRaisesRegex(PricingError, "unsupported country", instance.tax_cents, 10000, "XX")
		self.assertRaisesRegex(PricingError, "unsupported country", instance.tax_cents, 10000, "")
		self.assertRaisesRegex(PricingError, "unsupported country", instance.tax_cents, 10000, "   ")

	def test_shipping_cents_returns_unsupported_country_for_invalid_countries(self):

		instance = PricingService()

		self.assertRaisesRegex(PricingError, "unsupported country", instance.shipping_cents, 10000, "XX")
		self.assertRaisesRegex(PricingError, "unsupported country", instance.shipping_cents, 10000, "")
		self.assertRaisesRegex(PricingError, "unsupported country", instance.shipping_cents, 10000, "   ")

	def test_shipping_cents_conditions_returns_expected_value_for_CL(self):

		instance = PricingService()

		self.assertEqual(instance.shipping_cents(10000, "CL"), 2500)
		self.assertEqual(instance.shipping_cents(10000, " cl "), 2500)
		self.assertEqual(instance.shipping_cents(20000, "CL"), 0)
		self.assertEqual(instance.shipping_cents(20000, " cl "), 0)
		self.assertEqual(instance.shipping_cents(0, "CL"), 2500)
		self.assertEqual(instance.shipping_cents(-1000, "CL"), 2500)

	def test_shipping_cents_conditions_returns_expected_value_for_EU(self):
		
		instance = PricingService()

		self.assertEqual(instance.shipping_cents(10000, "EU"), 5000)
		self.assertEqual(instance.shipping_cents(10000, "eu"), 5000)
		self.assertEqual(instance.shipping_cents(0, "EU"), 5000)
		self.assertEqual(instance.shipping_cents(-1000, "EU"), 5000)

	def test_shipping_cents_conditions_returns_expected_value_for_US(self):

		instance = PricingService()

		self.assertEqual(instance.shipping_cents(10000, "US"), 5000)
		self.assertEqual(instance.shipping_cents(10000, " us "), 5000)
		self.assertEqual(instance.shipping_cents(0, "US"), 5000)
		self.assertEqual(instance.shipping_cents(-1000, "US"), 5000)

	def test_total_cents_conditions(self):

		instance = PricingService()
		mock_instance = Mock()
		
		mock_instance.subtotal_cents.return_value = 10000
		mock_instance.apply_coupon.return_value = 9000
		mock_instance.tax_cents.return_value = 1900
		mock_instance.shipping_cents.return_value = 2500

		instance.subtotal_cents = mock_instance.subtotal_cents
		instance.apply_coupon = mock_instance.apply_coupon
		instance.tax_cents = mock_instance.tax_cents
		instance.shipping_cents = mock_instance.shipping_cents

		items = [CartItem(sku="A", unit_price_cents=1000, qty=1)]
		coupon = "SAVE10"
		country = "CL"

		total = instance.total_cents(items, coupon, country)

		self.assertEqual(total, 9000 + 1900 + 2500)

		mock_instance.subtotal_cents.assert_called_once_with(items)
		mock_instance.apply_coupon.assert_called_once_with(10000, coupon)
		mock_instance.tax_cents.assert_called_once_with(9000, country)
		mock_instance.shipping_cents.assert_called_once_with(9000, country)