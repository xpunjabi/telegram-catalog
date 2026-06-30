#!/usr/bin/env python3
"""
One-time bot setup script.

Configures the Telegram bot with:
1. Persistent menu button (opens the catalog form in WebApp)
2. Bot description (shows when user opens chat)
3. Bot short description (shows in chat list)
4. Bot commands (/start, /help, /catalog)
5. Fetches recent /start messages and sends welcome to each user

Run this script via GitHub Actions (workflow_dispatch) or locally.
It's idempotent — safe to run multiple times.

Environment variables:
    TELEGRAM_BOT_TOKEN - Bot token from @BotFather
    FORM_URL - URL of the GitHub Pages form (e.g., https://xpunjabi.github.io/telegram-catalog/)
"""
import json
import os
import sys
import urllib.request
import urllib.error

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
FORM_URL = os.environ.get("FORM_URL", "https://xpunjabi.github.io/telegram-catalog/").strip()

if not BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN is not set", file=sys.stderr)
    sys.exit(1)

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg_call(method, payload=None):
    """Call a Telegram Bot API method."""
    url = f"{API}/{method}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  ❌ {method} failed: HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ❌ {method} failed: {e}", file=sys.stderr)
        return None


def setup_menu_button():
    """Set persistent menu button that opens the form in WebApp."""
    print("1. Setting persistent menu button...")
    result = tg_call("setChatMenuButton", {
        "menu_button": {
            "type": "web_app",
            "text": "📝 Add Product",
            "web_app": {"url": FORM_URL}
        }
    })
    if result and result.get("ok"):
        print("   ✅ Menu button set — users will see '📝 Add Product' button in chat")
    else:
        print("   ⚠️  Menu button setup failed (may need to be set per-chat)")


def setup_description():
    """Set bot description (shows when user opens chat)."""
    print("2. Setting bot description...")
    desc = (
        "🛍️ A Collection - Narowal Cloth Hub\n\n"
        "Product catalog management bot.\n\n"
        "📝 Add Product button neeche click karein\n"
        "Catalog form khulega - product details bharein\n"
        "Submit karte hi channel pe post aa jayegi!\n\n"
        "Commands:\n"
        "/start - Bot shuru karein\n"
        "/help - Madad cheezein\n"
        "/catalog - Form kholiye"
    )
    result = tg_call("setMyDescription", {"description": desc})
    if result and result.get("ok"):
        print("   ✅ Description set")


def setup_short_description():
    """Set bot short description (shows in chat list)."""
    print("3. Setting bot short description...")
    short_desc = "🛍️ Product catalog management - Narowal Cloth Hub"
    result = tg_call("setMyShortDescription", {"short_description": short_desc})
    if result and result.get("ok"):
        print("   ✅ Short description set")


def setup_commands():
    """Set bot commands (shows in /menu)."""
    print("4. Setting bot commands...")
    commands = [
        {"command": "start", "description": "Bot shuru karein / Start the bot"},
        {"command": "help", "description": "Madad / Help guide"},
        {"command": "catalog", "description": "Form kholiye / Open catalog form"},
        {"command": "about", "description": "Bot ke baare mein / About this bot"},
    ]
    result = tg_call("setMyCommands", {"commands": commands})
    if result and result.get("ok"):
        print("   ✅ Commands set: /start, /help, /catalog, /about")


def get_bot_info():
    """Get bot info to display."""
    print("5. Getting bot info...")
    result = tg_call("getMe")
    if result and result.get("ok"):
        bot = result["result"]
        print(f"   ✅ Bot: @{bot['username']} ({bot['first_name']})")
        print(f"   Bot URL: https://t.me/{bot['username']}")
        return bot
    return None


def send_welcome_to_recent_users():
    """Fetch recent updates and send welcome to users who sent /start."""
    print("6. Checking for recent /start messages...")
    result = tg_call("getUpdates", {"limit": 100, "timeout": 0})
    if not result or not result.get("ok"):
        print("   ⚠️  Could not fetch updates")
        return

    updates = result.get("result", [])
    if not updates:
        print("   ℹ️  No recent updates found")
        return

    # Find unique users who sent /start
    welcomed_users = set()
    for update in updates:
        msg = update.get("message") or update.get("channel_post")
        if not msg:
            continue
        text = msg.get("text", "")
        user = msg.get("from") or msg.get("chat")
        if not user:
            continue
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id:
            continue

        if text.startswith("/start") and chat_id not in welcomed_users:
            welcomed_users.add(chat_id)
            send_welcome_message(chat_id, user)

    if not welcomed_users:
        print("   ℹ️  No /start messages found in recent updates")


def send_welcome_message(chat_id, user):
    """Send a welcome message with inline buttons."""
    print(f"   📤 Sending welcome to chat_id={chat_id} ({user.get('first_name', 'User')})...")

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

    # Inline keyboard with WebApp button
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "📝 Add Product (Form Kholiye)",
                    "web_app": {"url": FORM_URL}
                }
            ],
            [
                {"text": "❓ Help", "callback_data": "help"},
                {"text": "ℹ️ About", "callback_data": "about"}
            ]
        ]
    }

    result = tg_call("sendMessage", {
        "chat_id": chat_id,
        "text": welcome_text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })

    if result and result.get("ok"):
        print(f"   ✅ Welcome sent!")
    else:
        print(f"   ❌ Failed to send welcome")


def main():
    print("=" * 60)
    print("🤖 Telegram Bot Setup - A Collection Catalog")
    print("=" * 60)
    print(f"Form URL: {FORM_URL}")
    print()

    bot = get_bot_info()
    if not bot:
        print("FATAL: Could not connect to bot. Check TELEGRAM_BOT_TOKEN.")
        sys.exit(1)

    print()
    setup_menu_button()
    setup_description()
    setup_short_description()
    setup_commands()
    print()
    send_welcome_to_recent_users()

    print()
    print("=" * 60)
    print("✅ Bot setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"  1. Open your bot: https://t.me/{bot['username']}")
    print("  2. You should see '📝 Add Product' menu button")
    print("  3. Click it → form opens inside Telegram")
    print("  4. Fill product details → submit")
    print("  5. Check your channel — post appears in 1-2 minutes")
    print()
    print("Note: For future /start commands from new users,")
    print("the 'Poll Bot Updates' workflow runs every 10 minutes")
    print("and automatically sends welcome messages.")


if __name__ == "__main__":
    main()
