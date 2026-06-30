#!/usr/bin/env python3
"""
Polling script that checks for new /start messages and sends welcome.

This runs on a schedule (every 10 min) via GitHub Actions cron.
It's a "serverless polling" approach — no persistent server needed.

The script:
1. Calls getUpdates to fetch recent messages
2. Tracks which updates have been processed (using offset)
3. Sends welcome message to new /start users
4. Sends responses to /help, /catalog, /about commands
5. Saves the new offset so next run skips processed updates

State (offset) is stored in a GitHub Actions cache file.
"""
import json
import os
import sys
import urllib.request
import urllib.error

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
FORM_URL = os.environ.get("FORM_URL", "https://xpunjabi.github.io/telegram-catalog/").strip()
STATE_FILE = os.environ.get("STATE_FILE", "/tmp/bot_state.json")

if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN is not set", file=sys.stderr)
    sys.exit(1)

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg_call(method, payload=None):
    url = f"{API}/{method}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  ❌ {method} HTTP {e.code}: {body[:200]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ❌ {method}: {e}", file=sys.stderr)
        return None


def load_state():
    """Load the last processed update_id."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_update_id": 0, "welcomed_users": []}


def save_state(state):
    """Save state for next run."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        print(f"  State saved to {STATE_FILE}")
    except Exception as e:
        print(f"  ⚠️  Could not save state: {e}", file=sys.stderr)


def send_welcome(chat_id, user):
    """Send welcome message with inline keyboard."""
    welcome_text = (
        f"👋 Assalam-o-Alaikum, {user.get('first_name', 'there')}!\n\n"
        "🛍️ **A Collection - Narowal Cloth Hub**\n"
        "me aapka swagat hai!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 **Ye bot kya kar sakta hai?**\n\n"
        "✅ Product catalog form bharna\n"
        "✅ Photos ke saath product details\n"
        "✅ Auto-post to Telegram channel\n"
        "✅ Inventory tracking\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **Shuru karne ke liye:**\n"
        "Neeche **📝 Add Product** button click karein\n"
        "ya /catalog command bhejein\n\n"
        "💡 **Need help?** /help type karein"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "📝 Add Product (Form Kholiye)", "web_app": {"url": FORM_URL}}],
            [
                {"text": "❓ Help", "callback_data": "help"},
                {"text": "ℹ️ About", "callback_data": "about"}
            ]
        ]
    }
    return tg_call("sendMessage", {
        "chat_id": chat_id,
        "text": welcome_text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })


def send_help(chat_id):
    """Send help message."""
    help_text = (
        "❓ **Help Guide**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 **Add Product:**\n"
        "Menu button ya /catalog use karein\n"
        "Form khulega - details bharein\n"
        "Submit karein - channel pe post aa jayegi\n\n"
        "🔧 **Commands:**\n"
        "/start - Welcome message\n"
        "/help - Ye help guide\n"
        "/catalog - Form kholiye\n"
        "/about - Bot ke baare mein\n\n"
        "💡 **Tips:**\n"
        "• Images ke liye catbox.moe use karein (free)\n"
        "• Ek submission = ek channel post\n"
        "• Issues tab pe history dekh sakte hain\n\n"
        "❌ **Problem?**\n"
        "GitHub Issues tab mein check karein:\n"
        "https://github.com/xpunjabi/telegram-catalog/issues"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "📝 Open Form", "web_app": {"url": FORM_URL}}]
        ]
    }
    tg_call("sendMessage", {
        "chat_id": chat_id,
        "text": help_text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })


def send_about(chat_id):
    """Send about message."""
    about_text = (
        "ℹ️ **About This Bot**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🛍️ **A Collection - Narowal Cloth Hub**\n"
        "Product catalog management bot\n\n"
        "🏗️ **Architecture:**\n"
        "• Frontend: GitHub Pages\n"
        "• Database: GitHub Issues\n"
        "• Backend: GitHub Actions\n"
        "• Bot: Telegram Bot API\n\n"
        "💸 **100% Free** - No paid servers\n"
        "🔒 **Secure** - Minimal permissions\n"
        "📱 **Works** - Mobile + Desktop Telegram\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Made with ❤️ for Narowal Cloth Hub"
    )
    tg_call("sendMessage", {
        "chat_id": chat_id,
        "text": about_text,
        "parse_mode": "Markdown"
    })


def send_catalog_button(chat_id):
    """Send /catalog response with form button."""
    text = (
        "📝 **Catalog Form Kholiye**\n\n"
        "Neeche button click karein:\n"
        "Form Telegram ke andar khulega\n"
        "Bina password ke direct open hoga"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "📝 Open Catalog Form", "web_app": {"url": FORM_URL}}]
        ]
    }
    tg_call("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })


def handle_callback(callback_query):
    """Handle inline button callbacks."""
    data = callback_query.get("data", "")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    if not chat_id:
        return

    # Acknowledge the callback
    tg_call("answerCallbackQuery", {"callback_query_id": callback_query["id"]})

    if data == "help":
        send_help(chat_id)
    elif data == "about":
        send_about(chat_id)
    elif data == "catalog":
        send_catalog_button(chat_id)


def main():
    print("=" * 60)
    print("🤖 Bot Polling - Checking for new messages")
    print("=" * 60)

    state = load_state()
    offset = state.get("last_update_id", 0) + 1
    welcomed = set(state.get("welcomed_users", []))

    print(f"  Fetching updates with offset={offset}...")
    result = tg_call("getUpdates", {
        "offset": offset,
        "limit": 100,
        "timeout": 0,
        "allowed_updates": ["message", "callback_query"]
    })

    if not result or not result.get("ok"):
        print("  ❌ Failed to fetch updates")
        sys.exit(1)

    updates = result.get("result", [])
    print(f"  Found {len(updates)} new update(s)")

    if not updates:
        print("  ℹ️  No new messages")
        # Still save state to update the file timestamp
        save_state(state)
        return

    new_welcomed = []
    for update in updates:
        update_id = update.get("update_id", 0)
        if update_id > state.get("last_update_id", 0):
            state["last_update_id"] = update_id

        # Handle regular messages
        if "message" in update:
            msg = update["message"]
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "").strip()
            user = msg.get("from", {})

            if not chat_id:
                continue

            print(f"  📨 Message from {user.get('first_name', '?')} ({chat_id}): {text[:40]}")

            if text.startswith("/start"):
                if chat_id not in welcomed:
                    send_welcome(chat_id, user)
                    welcomed.add(chat_id)
                    new_welcomed.append(chat_id)
            elif text.startswith("/help"):
                send_help(chat_id)
            elif text.startswith("/catalog"):
                send_catalog_button(chat_id)
            elif text.startswith("/about"):
                send_about(chat_id)

        # Handle callback queries (inline button presses)
        elif "callback_query" in update:
            cb = update["callback_query"]
            print(f"  🔘 Callback from {cb.get('from', {}).get('first_name', '?')}: {cb.get('data')}")
            handle_callback(cb)

    state["welcomed_users"] = list(welcomed)
    save_state(state)

    print()
    print(f"✅ Processed {len(updates)} update(s)")
    if new_welcomed:
        print(f"📤 Sent welcome to {len(new_welcomed)} new user(s)")


if __name__ == "__main__":
    main()
