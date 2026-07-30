import os
import hashlib
import ipaddress
import socket
from urllib.parse import urlparse

import requests
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

LEDGER = [
    {"id": "txn_1001", "pan_last4": "4242", "amount": 4200, "currency": "USD", "status": "captured"},
    {"id": "txn_1002", "pan_last4": "4444", "amount": 1899, "currency": "EUR", "status": "refunded"},
]

MAX_FETCH_BYTES = 2048
FETCH_TIMEOUT_SECONDS = 5


def _is_public_address(address):
    ip = ipaddress.ip_address(address)
    return ip.is_global


def _validate_fetch_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None

    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return None

    if not addresses:
        return None

    for address in addresses:
        host = address[4][0]
        if not _is_public_address(host):
            return None

    return parsed.geturl()


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/")
def index():
    return jsonify(message="Ledger API is running")


@app.route("/tokenize", methods=["POST"])
def tokenize():
    payload = request.get_json(silent=True) or {}
    pan = payload.get("pan", "")
    token = "tok_" + hashlib.sha256(pan.encode()).hexdigest()[:24]
    return jsonify(token=token, last4=pan[-4:])


@app.route("/transactions")
def transactions():
    return jsonify(transactions=LEDGER)


@app.route("/import", methods=["POST"])
def import_config():
    config = yaml.safe_load(request.data) or {}
    return jsonify(loaded=str(config))


@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")
    safe_url = _validate_fetch_url(url)
    if safe_url is None:
        return jsonify(error="URL is not allowed"), 400

    resp = requests.get(safe_url, timeout=FETCH_TIMEOUT_SECONDS, allow_redirects=False)
    return jsonify(status_code=resp.status_code, body=resp.text[:MAX_FETCH_BYTES])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

