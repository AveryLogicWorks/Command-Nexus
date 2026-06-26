# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
PayPal Integration for Command Nexus Upgrades Store.

Flow:
1. User clicks "Purchase" in the Upgrades dialog.
2. PayPalClient.create_order() creates an order via PayPal Orders API v2.
3. User's browser opens to PayPal approval URL.
4. After payment, PayPal redirects to a local callback server.
5. PayPalClient.capture_order() verifies and captures the payment.
6. On success, the upgrade is unlocked and persisted.

Security:
- Only the PayPal Client ID is stored in the app (public, safe to embed).
- The Client Secret is NEVER stored in the app — capture is done via
  PayPal's client-side token flow or a backend proxy (future).
- No payment data touches Command Nexus — PayPal handles all card/bank info.

For production, you should add a backend server to hold the Client Secret
and perform server-side capture. For beta, we use the client-side flow.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Event
from typing import Optional, Callable
from dataclasses import dataclass
from .settings_manager import SettingsManager


# PayPal API endpoints
_PAYPAL_SANDBOX = "https://api-m.sandbox.paypal.com"
_PAYPAL_LIVE = "https://api-m.paypal.com"
_PAYPAL_SANDBOX_WEB = "https://www.sandbox.paypal.com"
_PAYPAL_LIVE_WEB = "https://www.paypal.com"


@dataclass
class PayPalOrderResult:
    """Result of creating a PayPal order."""
    success: bool
    order_id: str = ""
    approval_url: str = ""
    error: str = ""


@dataclass
class PayPalCaptureResult:
    """Result of capturing/verifying a PayPal order."""
    success: bool
    order_id: str = ""
    status: str = ""  # COMPLETED, APPROVED, etc.
    payer_email: str = ""
    error: str = ""


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that catches the PayPal redirect after approval."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        token = params.get("token", [""])[0]
        payer_id = params.get("PayerID", [""])[0]

        if token:
            self.server.received_token = token
            self.server.received_payer_id = payer_id
            self.server.received_event.set()

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;padding:40px;'>"
                b"<h2>Payment Approved!</h2>"
                b"<p>You can close this tab and return to Command Nexus.</p>"
                b"<script>setTimeout(()=>window.close(),3000);</script>"
                b"</body></html>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Missing payment token.</h2></body></html>")

    def log_message(self, format, *args):
        pass  # Suppress console output


class _CallbackServer(HTTPServer):
    """HTTP server with event signaling for PayPal callback."""

    def __init__(self, port: int):
        self.received_token: str = ""
        self.received_payer_id: str = ""
        self.received_event = Event()
        super().__init__(("127.0.0.1", port), _CallbackHandler)


class PayPalClient:
    """
    PayPal Orders API v2 client for Command Nexus.

    Uses the client-side flow (Client ID only, no secret in the app).
    For production, add a backend server to hold the secret and do
    server-side capture for stronger security.
    """

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
        s = self._settings.get()
        self._client_id = getattr(s, "paypal_client_id", "") or ""
        self._sandbox = getattr(s, "paypal_sandbox", True)
        self._callback_port = getattr(s, "paypal_callback_port", 8755)

        self._api_base = _PAYPAL_SANDBOX if self._sandbox else _PAYPAL_LIVE
        self._web_base = _PAYPAL_SANDBOX_WEB if self._sandbox else _PAYPAL_LIVE_WEB
        self._callback_server: Optional[_CallbackServer] = None
        self._callback_thread: Optional[Thread] = None

    def is_configured(self) -> bool:
        """Check if PayPal Client ID is configured."""
        return bool(self._client_id)

    def get_callback_url(self) -> str:
        return f"http://127.0.0.1:{self._callback_port}/callback"

    def _get_access_token(self) -> str:
        """
        Get an access token using client credentials (client-side flow).
        For sandbox, this uses the Client ID only with the 'client_credentials' grant.
        In production, you'd use a backend with the Client Secret.
        """
        if not self._client_id:
            raise ValueError("PayPal Client ID is not configured.")

        url = f"{self._api_base}/v1/oauth2/token"
        data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Basic {self._client_id}:")  # Client ID only, no secret
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("access_token", "")

    def create_order(
        self,
        upgrade_id: str,
        upgrade_name: str,
        price: str,
        description: str = "",
    ) -> PayPalOrderResult:
        """
        Create a PayPal order for an upgrade purchase.
        Returns the order ID and approval URL.
        """
        if not self._client_id:
            return PayPalOrderResult(
                success=False,
                error="PayPal is not configured. Add your PayPal Client ID in Settings.",
            )

        # Parse price to PayPal format (amount with 2 decimals)
        try:
            amount = f"{float(price.replace('$', '').replace('/user', '').strip()):.2f}"
        except ValueError:
            return PayPalOrderResult(
                success=False,
                error=f"Invalid price format: {price}",
            )

        try:
            token = self._get_access_token()
        except Exception as e:
            return PayPalOrderResult(
                success=False,
                error=f"PayPal authentication failed: {e}",
            )

        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": upgrade_id,
                    "description": description or upgrade_name,
                    "amount": {
                        "currency_code": "USD",
                        "value": amount,
                    },
                }
            ],
            "application_context": {
                "brand_name": "Command Nexus",
                "return_url": self.get_callback_url(),
                "cancel_url": self.get_callback_url() + "?cancelled=true",
                "user_action": "PAY_NOW",
                "shipping_preference": "NO_SHIPPING",
            },
        }

        url = f"{self._api_base}/v2/checkout/orders"
        req = urllib.request.Request(
            url,
            data=json.dumps(order_payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {token}")

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            return PayPalOrderResult(
                success=False,
                error=f"PayPal order creation failed (HTTP {e.code}): {error_body[:300]}",
            )
        except Exception as e:
            return PayPalOrderResult(
                success=False,
                error=f"PayPal order creation failed: {e}",
            )

        order_id = body.get("id", "")
        approval_url = ""
        for link in body.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link.get("href", "")
                break

        if not approval_url:
            return PayPalOrderResult(
                success=False,
                error="PayPal did not return an approval URL.",
            )

        return PayPalOrderResult(
            success=True,
            order_id=order_id,
            approval_url=approval_url,
        )

    def capture_order(self, order_id: str) -> PayPalCaptureResult:
        """
        Capture payment for an approved order.
        This finalizes the transaction.
        """
        if not self._client_id:
            return PayPalCaptureResult(
                success=False,
                error="PayPal is not configured.",
            )

        try:
            token = self._get_access_token()
        except Exception as e:
            return PayPalCaptureResult(
                success=False,
                error=f"PayPal authentication failed: {e}",
            )

        url = f"{self._api_base}/v2/checkout/orders/{order_id}/capture"
        req = urllib.request.Request(url, data=b"{}", method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {token}")

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            return PayPalCaptureResult(
                success=False,
                error=f"PayPal capture failed (HTTP {e.code}): {error_body[:300]}",
            )
        except Exception as e:
            return PayPalCaptureResult(
                success=False,
                error=f"PayPal capture failed: {e}",
            )

        status = body.get("status", "")
        payer_email = ""
        payer = body.get("payer", {})
        if payer:
            payer_email = payer.get("email_address", "")

        # Check if capture was completed
        purchase_units = body.get("purchase_units", [])
        capture_completed = False
        for unit in purchase_units:
            for capture in unit.get("payments", {}).get("captures", []):
                if capture.get("status") == "COMPLETED":
                    capture_completed = True
                    break

        if status == "COMPLETED" or capture_completed:
            return PayPalCaptureResult(
                success=True,
                order_id=order_id,
                status="COMPLETED",
                payer_email=payer_email,
            )

        return PayPalCaptureResult(
            success=False,
            order_id=order_id,
            status=status,
            error=f"Payment not completed. Status: {status}",
        )

    def start_callback_server(self, timeout_seconds: int = 300) -> Optional[str]:
        """
        Start a local HTTP server to catch the PayPal redirect.
        Returns the order token if received within timeout, or None.
        """
        if self._callback_server is not None:
            self.stop_callback_server()

        try:
            self._callback_server = _CallbackServer(self._callback_port)
        except OSError:
            # Port in use — try next port
            for port in range(self._callback_port + 1, self._callback_port + 10):
                try:
                    self._callback_server = _CallbackServer(port)
                    self._callback_port = port
                    break
                except OSError:
                    continue
            if self._callback_server is None:
                return None

        self._callback_thread = Thread(
            target=self._callback_server.serve_forever,
            daemon=True,
        )
        self._callback_thread.start()

        # Wait for callback or timeout
        if self._callback_server.received_event.wait(timeout=timeout_seconds):
            return self._callback_server.received_token

        return None

    def stop_callback_server(self):
        """Stop the callback HTTP server."""
        if self._callback_server is not None:
            try:
                self._callback_server.shutdown()
                self._callback_server.server_close()
            except Exception:
                pass
            self._callback_server = None
        if self._callback_thread is not None:
            self._callback_thread = None

    def purchase_upgrade(
        self,
        upgrade_id: str,
        upgrade_name: str,
        price: str,
        description: str = "",
        on_status: Callable[[str], None] | None = None,
    ) -> PayPalCaptureResult:
        """
        Full purchase flow: create order → open browser → wait for callback → capture.

        on_status: optional callback for status updates (shown in UI).
        """
        def _status(msg: str):
            if on_status:
                on_status(msg)

        _status("Creating PayPal order...")

        # Step 1: Create the order
        order = self.create_order(upgrade_id, upgrade_name, price, description)
        if not order.success:
            return PayPalCaptureResult(
                success=False,
                error=order.error,
            )

        _status("Opening PayPal in your browser...")

        # Step 2: Open browser to approval URL
        webbrowser.open(order.approval_url)

        # Step 3: Start callback server and wait for redirect
        _status("Waiting for PayPal approval (5 minute timeout)...")

        token = self.start_callback_server(timeout_seconds=300)

        try:
            if token is None:
                # User might have completed payment but callback failed
                # Offer manual order ID entry
                _status("Callback not received. Please enter your Order ID manually.")
                return PayPalCaptureResult(
                    success=False,
                    order_id=order.order_id,
                    status="TIMEOUT",
                    error="PayPal callback not received. You can verify manually with the Order ID.",
                )

            _status("Payment approved! Capturing order...")

            # Step 4: Capture the order
            result = self.capture_order(order.order_id)
            return result

        finally:
            self.stop_callback_server()

    def verify_order_id(self, order_id: str) -> PayPalCaptureResult:
        """
        Manually verify an order ID (fallback when callback fails).
        Captures the order if it's approved but not yet captured.
        """
        if not self._client_id:
            return PayPalCaptureResult(
                success=False,
                error="PayPal is not configured.",
            )

        try:
            token = self._get_access_token()
        except Exception as e:
            return PayPalCaptureResult(
                success=False,
                error=f"PayPal authentication failed: {e}",
            )

        # First check the order status
        url = f"{self._api_base}/v2/checkout/orders/{order_id}"
        req = urllib.request.Request(url, method="GET")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {token}")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return PayPalCaptureResult(
                success=False,
                order_id=order_id,
                error=f"Order verification failed (HTTP {e.code})",
            )
        except Exception as e:
            return PayPalCaptureResult(
                success=False,
                order_id=order_id,
                error=f"Order verification failed: {e}",
            )

        status = body.get("status", "")

        if status == "COMPLETED":
            payer_email = body.get("payer", {}).get("email_address", "")
            return PayPalCaptureResult(
                success=True,
                order_id=order_id,
                status="COMPLETED",
                payer_email=payer_email,
            )

        if status == "APPROVED":
            # Capture it
            return self.capture_order(order_id)

        return PayPalCaptureResult(
            success=False,
            order_id=order_id,
            status=status,
            error=f"Order status is {status}, not APPROVED or COMPLETED.",
        )
