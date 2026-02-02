"""
PIN verification endpoint for SpendTrackr authentication.
Verifies the provided PIN against the APP_PIN environment variable.
"""

import os
import json
import time
from http.server import BaseHTTPRequestHandler

# Simple in-memory rate limiting (resets on cold start, but that's fine for basic protection)
# In production, you'd use Redis or similar
attempt_tracker = {}
MAX_ATTEMPTS = 8
LOCKOUT_DURATION = 300  # 5 minutes in seconds


def get_client_ip(headers):
    """Extract client IP from headers."""
    # Check common proxy headers
    forwarded_for = headers.get('x-forwarded-for', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return headers.get('x-real-ip', 'unknown')


def check_rate_limit(client_ip):
    """Check if client is rate limited. Returns (is_allowed, attempts_remaining, lockout_remaining)."""
    current_time = time.time()

    if client_ip not in attempt_tracker:
        attempt_tracker[client_ip] = {'attempts': 0, 'lockout_until': 0}

    tracker = attempt_tracker[client_ip]

    # Check if currently locked out
    if tracker['lockout_until'] > current_time:
        remaining = int(tracker['lockout_until'] - current_time)
        return False, 0, remaining

    # Reset if lockout has expired
    if tracker['lockout_until'] > 0 and tracker['lockout_until'] <= current_time:
        tracker['attempts'] = 0
        tracker['lockout_until'] = 0

    attempts_remaining = MAX_ATTEMPTS - tracker['attempts']
    return True, attempts_remaining, 0


def record_attempt(client_ip, success):
    """Record an authentication attempt."""
    if client_ip not in attempt_tracker:
        attempt_tracker[client_ip] = {'attempts': 0, 'lockout_until': 0}

    tracker = attempt_tracker[client_ip]

    if success:
        # Reset on successful auth
        tracker['attempts'] = 0
        tracker['lockout_until'] = 0
    else:
        tracker['attempts'] += 1
        if tracker['attempts'] >= MAX_ATTEMPTS:
            tracker['lockout_until'] = time.time() + LOCKOUT_DURATION


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get client IP for rate limiting
            client_ip = get_client_ip(dict(self.headers))

            # Check rate limit
            is_allowed, attempts_remaining, lockout_remaining = check_rate_limit(client_ip)

            if not is_allowed:
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    'success': False,
                    'error': f'Too many attempts. Try again in {lockout_remaining} seconds.',
                    'lockout_remaining': lockout_remaining
                }
                self.wfile.write(json.dumps(response).encode())
                return

            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # Get submitted PIN
            submitted_pin = data.get('pin', '')

            # Get correct PIN from environment
            correct_pin = os.environ.get('APP_PIN', '')

            if not correct_pin:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    'success': False,
                    'error': 'PIN not configured on server'
                }
                self.wfile.write(json.dumps(response).encode())
                return

            # Verify PIN (constant-time comparison to prevent timing attacks)
            import hmac
            is_valid = hmac.compare_digest(str(submitted_pin), str(correct_pin))

            # Record the attempt
            record_attempt(client_ip, is_valid)

            if is_valid:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                # Generate a simple auth token (timestamp-based, not cryptographically secure but fine for this use case)
                import hashlib
                token_base = f"{correct_pin}-{int(time.time())}-spendtrackr"
                auth_token = hashlib.sha256(token_base.encode()).hexdigest()[:32]

                response = {
                    'success': True,
                    'token': auth_token
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                # Get updated attempts remaining
                _, attempts_remaining, _ = check_rate_limit(client_ip)

                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {
                    'success': False,
                    'error': 'Incorrect PIN',
                    'attempts_remaining': attempts_remaining
                }
                self.wfile.write(json.dumps(response).encode())

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'success': False, 'error': 'Invalid JSON'}
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
