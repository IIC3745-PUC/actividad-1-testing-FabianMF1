import unittest
from unittest.mock import Mock, patch

from src.models import CartItem, Order
from src.pricing import PricingService, PricingError
from src.checkout import CheckoutService, ChargeResult

class TestCheckoutService(unittest.TestCase):

	def mock_CheckoutService(self):

		payments = Mock()
		email = Mock()
		fraud = Mock()
		repo = Mock()
		pricing = Mock()

		instance = CheckoutService(payments, email, fraud, repo, pricing)

		return instance, payments, email, fraud, repo, pricing

	def test_checkout_returns_error_on_invalid_user_id(self):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		result = instance.checkout("", [], "token", "CL")

		self.assertEqual(result, "INVALID_USER")
		pricing.total_cents.assert_not_called()

	def test_checkout_returns_invalid_cart_on_pricing_total_subtotal_cents_error(self):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.side_effect = PricingError("error")
		items = [CartItem("A", 1000, 0)]

		result = instance.checkout("user", items, "token", "CL", "SAVE10")

		self.assertEqual(result, "INVALID_CART:error")
		pricing.total_cents.assert_called_once_with(items, "SAVE10", "CL")

	def test_checkout_returns_invalid_cart_on_pricing_total_coupon_error(self):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.side_effect = PricingError("error")
		items = [CartItem("A", 1000, 1)]

		result = instance.checkout("user", items, "token", "CL", "SAVE10")

		self.assertEqual(result, "INVALID_CART:error")
		pricing.total_cents.assert_called_once_with(items, "SAVE10", "CL")

	def test_checkout_returns_invalid_cart_on_pricing_total_tax_cents_error(self):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.side_effect = PricingError("error")
		items = [CartItem("A", 1000, 1)]

		result = instance.checkout("user", items, "token", "XX", "SAVE10")

		self.assertEqual(result, "INVALID_CART:error")
		pricing.total_cents.assert_called_once_with(items, "SAVE10", "XX")

	def test_checkout_returns_invalid_cart_on_pricing_total_tax_shipping_cents_error(self):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.side_effect = PricingError("error")
		items = [CartItem("A", 1000, 1)]

		result = instance.checkout("user", items, "token", "XX", "SAVE10")

		self.assertEqual(result, "INVALID_CART:error")
		pricing.total_cents.assert_called_once_with(items, "SAVE10", "XX")

	def test_checkout_returns_rejected_fraud_on_fraud_score_80_or_more(self):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.return_value = 1000
		fraud.score.return_value = 80

		result = instance.checkout("user", [CartItem("A", 1000,1)], "token", "CL", "SAVE10")

		self.assertEqual(result, "REJECTED_FRAUD")
		fraud.score.assert_called_once_with("user", 1000)

	def test_checkout_returns_payment_failed_on_charge_failure(self):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.return_value = 1000
		fraud.score.return_value = 50
		payments.charge.return_value = ChargeResult(ok=False, reason="error")

		result = instance.checkout("user", [CartItem("A", 1000,1)], "token", "CL", "SAVE10")

		self.assertEqual(result, "PAYMENT_FAILED:error")
		payments.charge.assert_called_once_with(user_id="user", amount_cents=1000, payment_token="token")

	@patch("src.checkout.uuid.uuid4")
	def test_checkout_saves_order_and_sends_receipt_when_successful(self, mock_get):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.return_value = 1000
		fraud.score.return_value = 50
		payments.charge.return_value = ChargeResult(ok=True, charge_id="1", reason="")
		mock_get.return_value = "1234"

		result = instance.checkout("user", [CartItem("A", 1000,1)], "token", "CL", "SAVE10")

		self.assertEqual(result, "OK:1234")

		repo.save.assert_called_once()
		email.send_receipt.assert_called_once_with("user", "1234", 1000)

		# Para poder obtener los datos de la order probe este metodo
		# https://docs.python.org/3/library/unittest.mock.html#calls-as-tuples
		# https://docs.python.org/3/library/unittest.mock.html
		order = repo.save.call_args[0][0]

		self.assertEqual(order.order_id, "1234")
		self.assertEqual(order.user_id, "user")
		self.assertEqual(order.total_cents, 1000)
		self.assertEqual(order.payment_charge_id, "1")
		self.assertEqual(order.coupon_code, "SAVE10")
		self.assertEqual(order.country, "CL")

	@patch("src.checkout.uuid.uuid4")
	def test_checkout_returns_unknown_when_charge_id_is_none(self, mock_get):
		instance, payments, email, fraud, repo, pricing = self.mock_CheckoutService()

		pricing.total_cents.return_value = 1000
		fraud.score.return_value = 50
		payments.charge.return_value = ChargeResult(ok=True, charge_id=None, reason="")

		result = instance.checkout("user", [CartItem("A", 1000, 1)], "token", "CL", "SAVE10")

		# Para poder obtener los datos de la order probe este metodo
		# https://docs.python.org/3/library/unittest.mock.html#calls-as-tuples
		# https://docs.python.org/3/library/unittest.mock.html
		order = repo.save.call_args[0][0]

		self.assertEqual(order.payment_charge_id, "UNKNOWN")

