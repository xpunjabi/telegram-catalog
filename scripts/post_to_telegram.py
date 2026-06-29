#!/usr/bin/env python3
"""
Parse a GitHub issue body containing product JSON and post a formatted
message to a Telegram channel via the Bot API.

The issue body is expected to contain a ```json ... ``` code block with
the product data. This script extracts that JSON, formats a beautiful
Telegram message (with HTML formatting), sends it, and also sends any
image URLs as photos.

Environment variables:
    TELEGRAM_BOT_TOKEN  - Bot token from @BotFather
    TELEGRAM_CHANNEL_ID - Channel ID (e.g., -1001234567890 or @channelname)
    ISSUE_TITLE         - Title of the GitHub issue
    ISSUE_BODY          - Body of the GitHub issue (contains JSON)
    ISSUE_NUMBER        - Issue number
    ISSUE_URL           - URL to the GitHub issue
    REPO_FULL_NAME      - owner/repo (for reference)
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER", "")
ISSUE_URL = os.environ.get("ISSUE_URL", "")

if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN secret is not set", file=sys.stderr)
    sys.exit(1)
if not CHANNEL_ID:
    print("ERROR: TELEGRAM_CHANNEL_ID secret is not set", file=sys.stderr)
    sys.exit(1)


def extract_json_from_body(body):
    """Extract the JSON code block from the issue body."""
    # Match ```json ... ``` block
    match = re.search(r"```json\s*\n(.*?)\n```", body, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON from issue body: {e}", file=sys.stderr)
            return None
    print("ERROR: No ```json code block found in issue body", file=sys.stderr)
    return None


def escape_html(text):
    """Escape HTML special characters for Telegram HTML formatting."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_message(product):
    """Format the product data as a beautiful Telegram HTML message."""
    lines = []
    lines.append("🛍️ <b>New Product Added</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append(f"📋 <b>Code:</b> <code>{escape_html(product.get('code', 'N/A'))}</code>")
    lines.append(f"👤 <b>Name:</b> {escape_html(product.get('name', 'N/A'))}")

    color = product.get("color")
    if color:
        lines.append(f"🎨 <b>Color:</b> {escape_html(color)}")
    fabric = product.get("fabric")
    if fabric:
        lines.append(f"🧵 <b>Fabric:</b> {escape_html(fabric)}")
    brand = product.get("brand")
    if brand:
        lines.append(f"🏷️ <b>Brand:</b> {escape_html(brand)}")

    lines.append("")
    lines.append("💰 <b>Pricing</b>")
    cost = product.get("cost", "0")
    retail = product.get("retail", "0")
    sale = product.get("sale", "0")
    lines.append(f"   Cost: Rs. {escape_html(cost)}")
    lines.append(f"   Retail: Rs. {escape_html(retail)}")
    if sale and sale != "0":
        lines.append(f"   🔥 <b>Sale: Rs. {escape_html(sale)}</b>")

    stock = product.get("stock", "0")
    lines.append("")
    lines.append(f"📦 <b>Stock:</b> {escape_html(stock)} pieces")

    description = product.get("description")
    if description:
        lines.append("")
        lines.append("📝 <b>Description:</b>")
        lines.append(escape_html(description))

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"👤 Submitted by: {escape_html(product.get('submitted_by', 'Unknown'))}")
    lines.append("🛍️ <b>A Collection - Narowal Cloth Hub</b>")
    lines.append("📩 DM to order | 🚚 Nationwide delivery")

    return "\n".join(lines)


def send_telegram_message(text):
    """Send a text message to the Telegram channel."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                print(f"✅ Message sent to Telegram. Message ID: {result['result']['message_id']}")
                return result["result"]["message_id"]
            else:
                print(f"ERROR: Telegram API returned error: {result}", file=sys.stderr)
                return None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: Telegram API HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Failed to send message: {e}", file=sys.stderr)
        return None


def send_telegram_photo(photo_url, caption=None):
    """Send a single photo to the Telegram channel."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHANNEL_ID,
        "photo": photo_url,
    }
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                print(f"✅ Photo sent: {photo_url}")
                return True
            else:
                print(f"WARNING: Telegram rejected photo {photo_url}: {result}", file=sys.stderr)
                return False
    except Exception as e:
        print(f"WARNING: Failed to send photo {photo_url}: {e}", file=sys.stderr)
        return False


def main():
    print(f"Processing issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")
    print(f"Issue URL: {ISSUE_URL}")
    print(f"Channel ID: {CHANNEL_ID}")
    print("")

    product = extract_json_from_body(ISSUE_BODY)
    if not product:
        print("ERROR: Could not extract product data from issue", file=sys.stderr)
        sys.exit(1)

    print(f"Product parsed: {product.get('code')} - {product.get('name')}")

    # 1. Send text message with product details
    message_text = format_message(product)
    msg_id = send_telegram_message(message_text)
    if msg_id is None:
        print("ERROR: Failed to send text message", file=sys.stderr)
        sys.exit(1)

    # 2. Send photos as separate messages (Telegram allows only 1 photo per sendPhoto call)
    images = product.get("images", [])
    if isinstance(images, list) and images:
        print(f"\nSending {len(images)} image(s)...")
        for i, img_url in enumerate(images):
            caption = f"🖼️ Image {i+1}/{len(images)} - {product.get('name', '')}" if i == 0 else None
            send_telegram_photo(img_url, caption)

    print("\n✅ All operations completed successfully!")


if __name__ == "__main__":
    main()
