"""
Test Google Analytics 4 implementation.
Management command to validate GA4 Measurement Protocol integration.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from myproject.analytics import GoogleAnalyticsTracker
from ecom.models import Order
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Test Google Analytics 4 Measurement Protocol integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Use GA4 debug endpoint for validation',
        )
        parser.add_argument(
            '--test-all',
            action='store_true',
            help='Test all available event types',
        )

    def handle(self, *args, **options):
        debug_mode = options['debug']
        test_all = options['test_all']

        self.stdout.write(
            f"Testing Google Analytics 4 integration (debug={debug_mode})")

        # Initialize tracker
        tracker = GoogleAnalyticsTracker(debug=debug_mode)

        if not tracker.enabled:
            self.stdout.write(
                self.style.ERROR(
                    "Google Analytics is not properly configured. "
                    "Please set GA_MEASUREMENT_ID and GA_API_SECRET in your environment."
                )
            )
            return

        self.stdout.write(self.style.SUCCESS(
            "✓ Google Analytics configuration found"))

        # Test basic custom event
        success = tracker.track_custom_event(
            "test_event",
            {
                "test_parameter": "test_value",
                "source": "management_command"
            },
            session_id="test_session_123"
        )

        if success:
            self.stdout.write(self.style.SUCCESS(
                "✓ Basic event tracking test passed"))
        else:
            self.stdout.write(self.style.ERROR(
                "✗ Basic event tracking test failed"))

        if test_all:
            self._test_all_events(tracker)

        if debug_mode:
            self.stdout.write(
                self.style.WARNING(
                    "Debug mode enabled - check console output for GA4 validation response"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Google Analytics test completed. "
                "Check GA4 Real-time reports to verify events are being received."
            )
        )

    def _test_all_events(self, tracker):
        """Test all event types with mock data."""
        self.stdout.write("Testing all event types...")

        # Test signup event
        success = tracker.track_signup(
            user={'id': 'test_user_123', 'is_authenticated': True},
            method="phone",
            session_id="test_session_signup"
        )
        if success:
            self.stdout.write(self.style.SUCCESS("✓ Signup event test passed"))
        else:
            self.stdout.write(self.style.ERROR("✗ Signup event test failed"))

        # Test login event
        success = tracker.track_login(
            user={'id': 'test_user_123', 'is_authenticated': True},
            method="phone",
            session_id="test_session_login"
        )
        if success:
            self.stdout.write(self.style.SUCCESS("✓ Login event test passed"))
        else:
            self.stdout.write(self.style.ERROR("✗ Login event test failed"))

        # Test failed payment event
        mock_order = type('MockOrder', (), {
            'id': 'test_order_123',
            'total_amount': 999.99,
            'payment_method': 'phonepe'
        })()

        success = tracker.track_failed_payment(
            mock_order,
            error_reason="payment_timeout",
            user={'id': 'test_user_123', 'is_authenticated': True},
            session_id="test_session_payment"
        )
        if success:
            self.stdout.write(self.style.SUCCESS(
                "✓ Failed payment event test passed"))
        else:
            self.stdout.write(self.style.ERROR(
                "✗ Failed payment event test failed"))

        # Test cart action event
        mock_cart_item = type('MockCartItem', (), {
            'product': type('MockProduct', (), {
                'id': 'test_product_123',
                'name': 'Test Product',
                'price': 99.99,
                'category': type('MockCategory', (), {'name': 'Test Category'})()
            })(),
            'quantity': 2
        })()

        success = tracker.track_cart_action(
            "add_to_cart",
            [mock_cart_item],
            user={'id': 'test_user_123', 'is_authenticated': True},
            session_id="test_session_cart"
        )
        if success:
            self.stdout.write(self.style.SUCCESS(
                "✓ Cart action event test passed"))
        else:
            self.stdout.write(self.style.ERROR(
                "✗ Cart action event test failed"))

        self.stdout.write(
            self.style.SUCCESS(
                "All event tests completed. "
                "Monitor GA4 Real-time reports for event verification."
            )
        )
