"""
Google Analytics 4 Measurement Protocol implementation.
Server-side event tracking for ecommerce events.
"""

import requests
import uuid
import logging
import time
from typing import Dict, Any, Optional, Union, List
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


class GoogleAnalyticsTracker:
    """
    Google Analytics 4 Measurement Protocol tracker.
    Sends server-side events to GA4 for analytics tracking.
    """

    BASE_URL = "https://www.google-analytics.com/mp/collect"
    DEBUG_URL = "https://www.google-analytics.com/debug/mp/collect"

    def __init__(self, debug: bool = False):
        """
        Initialize the GA4 tracker.

        Args:
            debug: If True, uses debug endpoint for validation
        """
        self.measurement_id = settings.GA_MEASUREMENT_ID
        self.api_secret = settings.GA_API_SECRET
        self.debug = debug

        if not self.measurement_id or not self.api_secret:
            logger.warning("GA_MEASUREMENT_ID or GA_API_SECRET not configured")
            self.enabled = False
        else:
            self.enabled = True

    def _get_client_id(self, user: Optional[Any] = None, session_id: Optional[str] = None) -> str:
        """
        Generate a client ID for tracking.

        Args:
            user: Django user instance
            session_id: Session identifier

        Returns:
            Client ID string
        """
        if user and user.is_authenticated:
            # Use user ID for consistent tracking across sessions
            # Daily rotation
            return f"user_{user.id}_{int(time.time() // 86400)}"
        elif session_id:
            return f"session_{session_id}"
        else:
            # Generate random client ID
            return str(uuid.uuid4())

    def _send_event(self, events: List[Dict[str, Any]], client_id: str) -> bool:
        """
        Send events to Google Analytics 4.

        Args:
            events: List of event dictionaries
            client_id: Client identifier

        Returns:
            Success status
        """
        if not self.enabled:
            logger.debug(
                "Google Analytics tracking disabled - missing configuration")
            return False

        url = self.DEBUG_URL if self.debug else self.BASE_URL

        payload = {
            "client_id": client_id,
            "events": events
        }

        params = {
            "measurement_id": self.measurement_id,
            "api_secret": self.api_secret
        }

        try:
            response = requests.post(
                url, json=payload, params=params, timeout=5)

            if self.debug:
                logger.info(f"GA4 Debug Response: {response.json()}")

            if response.status_code == 204 or (self.debug and response.status_code == 200):
                logger.debug(
                    f"Successfully sent GA4 events: {[e['name'] for e in events]}")
                return True
            else:
                logger.error(
                    f"GA4 API error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send GA4 events: {e}")
            return False

    def track_purchase(self, order, user: Optional[Any] = None, session_id: Optional[str] = None) -> bool:
        """
        Track a successful purchase event.

        Args:
            order: Order instance
            user: User who made the purchase
            session_id: Session identifier

        Returns:
            Success status
        """
        client_id = self._get_client_id(user, session_id)

        # Build items list from order
        items = []
        for order_item in order.items.all():
            items.append({
                "item_id": str(order_item.product.id),
                "item_name": order_item.product.name,
                "item_category": order_item.product.category.name if order_item.product.category else "Unknown",
                "price": float(order_item.price),
                "quantity": order_item.quantity
            })

        event = {
            "name": "purchase",
            "params": {
                "transaction_id": str(order.id),
                "value": float(order.total_amount),
                "currency": "INR",
                "payment_type": order.payment_method,
                "items": items
            }
        }

        return self._send_event([event], client_id)

    def track_refund(self, order, refund_amount: Union[Decimal, float], user: Optional[Any] = None, session_id: Optional[str] = None) -> bool:
        """
        Track a refund event.

        Args:
            order: Order instance being refunded
            refund_amount: Amount being refunded
            user: User receiving the refund
            session_id: Session identifier

        Returns:
            Success status
        """
        client_id = self._get_client_id(user, session_id)

        event = {
            "name": "refund",
            "params": {
                "transaction_id": str(order.id),
                "value": float(refund_amount),
                "currency": "INR"
            }
        }

        return self._send_event([event], client_id)

    def track_failed_payment(self, order, error_reason: str, user: Optional[Any] = None, session_id: Optional[str] = None) -> bool:
        """
        Track a failed payment event.

        Args:
            order: Order instance with failed payment
            error_reason: Reason for payment failure
            user: User attempting payment
            session_id: Session identifier

        Returns:
            Success status
        """
        client_id = self._get_client_id(user, session_id)

        event = {
            "name": "payment_failed",
            "params": {
                "transaction_id": str(order.id),
                "value": float(order.total_amount),
                "currency": "INR",
                "payment_method": order.payment_method,
                "error_reason": error_reason[:100]  # Limit length
            }
        }

        return self._send_event([event], client_id)

    def track_signup(self, user: Any, method: str = "phone", session_id: Optional[str] = None) -> bool:
        """
        Track a user signup event.

        Args:
            user: Newly registered user
            method: Signup method (phone, email, etc.)
            session_id: Session identifier

        Returns:
            Success status
        """
        client_id = self._get_client_id(user, session_id)

        event = {
            "name": "sign_up",
            "params": {
                "method": method,
                "user_id": str(user.id)
            }
        }

        return self._send_event([event], client_id)

    def track_login(self, user: Any, method: str = "phone", session_id: Optional[str] = None) -> bool:
        """
        Track a user login event.

        Args:
            user: User logging in
            method: Login method (phone, email, etc.)
            session_id: Session identifier

        Returns:
            Success status
        """
        client_id = self._get_client_id(user, session_id)

        event = {
            "name": "login",
            "params": {
                "method": method,
                "user_id": str(user.id)
            }
        }

        return self._send_event([event], client_id)

    def track_cart_action(self, action: str, cart_items, user: Optional[Any] = None, session_id: Optional[str] = None) -> bool:
        """
        Track cart-related actions (add_to_cart, remove_from_cart, view_cart).

        Args:
            action: Cart action name
            cart_items: Cart items queryset or list
            user: User performing action
            session_id: Session identifier

        Returns:
            Success status
        """
        client_id = self._get_client_id(user, session_id)

        items = []
        total_value = 0

        for item in cart_items:
            item_value = float(item.product.price * item.quantity)
            total_value += item_value

            items.append({
                "item_id": str(item.product.id),
                "item_name": item.product.name,
                "item_category": item.product.category.name if item.product.category else "Unknown",
                "price": float(item.product.price),
                "quantity": item.quantity
            })

        event = {
            "name": action,
            "params": {
                "currency": "INR",
                "value": total_value,
                "items": items
            }
        }

        return self._send_event([event], client_id)

    def track_custom_event(self, event_name: str, params: Dict[str, Any], user: Optional[Any] = None, session_id: Optional[str] = None) -> bool:
        """
        Track a custom event.

        Args:
            event_name: Name of the custom event
            params: Event parameters
            user: User associated with event
            session_id: Session identifier

        Returns:
            Success status
        """
        client_id = self._get_client_id(user, session_id)

        event = {
            "name": event_name,
            "params": params
        }

        return self._send_event([event], client_id)


# Global tracker instance
ga_tracker = GoogleAnalyticsTracker()
