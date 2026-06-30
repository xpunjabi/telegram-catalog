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


def send_media_group(photo_urls, caption):
    """Send multiple photos as a single grouped message with one caption.

    This is the KEY improvement: instead of sending each photo separately
    (which creates multiple messages), sendMediaGroup sends all photos as
    ONE grouped post. Users can share/copy the whole group as one unit.

    Telegram limits:
    - Max 10 photos per group
    - Caption only on first photo (max 1024 chars)
    """
    if not photo_urls:
        return False

    # Telegram limit: 10 photos per media group
    photos_to_send = photo_urls[:10]
    if len(photo_urls) > 10:
        print(f"WARNING: {len(photo_urls)} images provided, but Telegram limit is 10. Sending first 10.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup"
    media = []
    for i, photo_url in enumerate(photos_to_send):
        item = {
            "type": "photo",
            "media": photo_url,
        }
        # Caption only on first photo (Telegram requirement)
        if i == 0 and caption:
            item["caption"] = caption
            item["parse_mode"] = "HTML"
        media.append(item)

    payload = json.dumps({
        "chat_id": CHANNEL_ID,
        "media": media,
    }).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                msg_ids = [m["message_id"] for m in result["result"]]
                print(f"✅ Media group sent! Message IDs: {msg_ids}")
                return True
            else:
                print(f"ERROR: sendMediaGroup failed: {result}", file=sys.stderr)
                return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: sendMediaGroup HTTP {e.code}: {body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: sendMediaGroup exception: {e}", file=sys.stderr)
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

    images = product.get("images", [])
    if not isinstance(images, list):
        images = []

    message_text = format_message(product)

    # STRATEGY: Single grouped post (caption + all images together)
    # - If images present: use sendMediaGroup (1 grouped message, caption on first photo)
    # - If no images: use sendMessage (text only)
    # This ensures the entire product (text + photos) is ONE shareable post

    if images:
        print(f"\nSending {len(images)} image(s) as single grouped post with caption...")
        success = send_media_group(images, message_text)
        if not success:
            print("WARNING: sendMediaGroup failed, falling back to separate message + photos")
            # Fallback: text message first, then individual photos
            msg_id = send_telegram_message(message_text)
            if msg_id is None:
                print("ERROR: Fallback text message also failed", file=sys.stderr)
                sys.exit(1)
            for img_url in images:
                send_telegram_photo(img_url)
    else:
        # No images - just send text message
        print("\nNo images - sending text message only...")
        msg_id = send_telegram_message(message_text)
        if msg_id is None:
            print("ERROR: Failed to send text message", file=sys.stderr)
            sys.exit(1)

    print("\n✅ All operations completed successfully!")


if __name__ == "__main__":
    main()
