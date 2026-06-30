# Telegram Catalog - A Collection

A smart Telegram Mini App catalog form for the Narowal Cloth Hub business.
Submits product data via GitHub Issues, which triggers a GitHub Action that
posts the product to a Telegram channel automatically.

**100% free hosting** — uses only GitHub Pages, GitHub Issues, and GitHub
Actions. No credit card required. No local PC needed. No paid servers.

## Architecture

```
GitHub Pages (form)  →  GitHub Issues (inbox)  →  GitHub Action  →  Telegram Channel
   (frontend)              (database)              (backend)         (broadcast)
```

1. User opens the form (in Telegram OR a regular web browser)
2. User fills product details + image URLs
3. Form submits → creates a GitHub Issue in this repo
4. GitHub Action triggers automatically on the new issue
5. Action parses the JSON from the issue body
6. Action calls Telegram Bot API to post a formatted message + photos to your channel
7. Action closes the issue and adds a "posted" label

## Setup Guide

### Step 1: Create a Telegram Bot (5 min)

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Name: `A Collection Catalog Bot` (or whatever you want)
4. Username: `acollection_catalog_bot` (must end with `_bot`)
5. Copy the **bot token** (looks like `8123456789:AAH...`)
6. Create a Telegram channel (e.g., `@acollection_catalog`)
7. Add your bot as admin of the channel with "Post Messages" permission
8. Find the channel ID:
   - Forward a message from your channel to **@userinfobot**
   - It will reply with the channel ID (e.g., `-1001234567890`)

### Step 2: Add GitHub Secrets (3 min)

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret name | Value |
|--------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from step 1 |
| `TELEGRAM_CHANNEL_ID` | Your channel ID from step 1 (e.g., `-1001234567890`) |

### Step 3: Create a Fine-Grained PAT (5 min)

This PAT lets the frontend form create issues in this repo.

1. Go to https://github.com/settings/personal-access-tokens/new
2. **Token name**: `telegram-catalog-issue-creator`
3. **Expiration**: 90 days (or 1 year)
4. **Repository access**: Only select repositories → pick `xpunjabi/telegram-catalog`
5. **Repository permissions**:
   - Issues: **Read and write**
   - (Leave all other permissions as "No access")
6. Click **Generate token**
7. Copy the token (starts with `github_pat_...`)

### Step 4: Update the Frontend with Your PAT (2 min)

1. Open `index.html` in this repo
2. Find the line:
   ```javascript
   const GITHUB_PAT = "REPLACE_WITH_YOUR_FINE_GRAINED_PAT";
   ```
3. Replace with your actual PAT:
   ```javascript
   const GITHUB_PAT = "github_pat_xxxxxxxxxxxx";
   ```
4. Commit the change

**Security note**: This PAT is **NOT** secret — anyone can read it from the
frontend code. But it can ONLY create issues in this ONE repo. Worst case:
someone creates spam issues (which you can delete). They CANNOT access your
account, other repos, or push code.

### Step 5: Enable GitHub Pages (1 min)

1. Go to repo → **Settings** → **Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `main` / folder: `/ (root)`
4. Click **Save**
5. Wait ~1 minute
6. Your form is live at: `https://xpunjabi.github.io/telegram-catalog/`

### Step 6: Configure Your Telegram Bot to Open the Form (3 min)

Now you need to make your bot send a button that opens the form.

Option A — Quick test (no code):
1. Send this message to your bot (replace `<BOT_TOKEN>` and `<YOUR_USERNAME>`):
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/sendMessage?chat_id=<YOUR_USER_ID>&text=Open%20Catalog&reply_markup={"inline_keyboard":[[{"text":"📝 Add Product","web_app":{"url":"https://xpunjabi.github.io/telegram-catalog/"}}]]}
   ```
2. Open it in your browser
3. Your bot will send you a button — click it
4. The form opens inside Telegram with auto-bypass (no password needed)

Option B — Permanent bot (Python):
- Use the included `scripts/bot_menu.py` script (coming soon) to set up a
  permanent bot menu with the catalog button

### Step 7: Test the Form (2 min)

1. Open the form URL in your browser: `https://xpunjabi.github.io/telegram-catalog/`
2. You'll see the password screen (because you're not in Telegram)
3. Username: `acollection`
4. Password: `acollection`
5. Fill in product details + at least one image URL
6. Click "Save & Post to Channel"
7. Wait 1-2 minutes
8. Check your Telegram channel — the product post should appear!

## Configuration

### Change the Web Password

The default password is `acollection`. To change it:

1. Generate the SHA256 hash of your new password:
   ```bash
   echo -n "your-new-password" | sha256sum
   ```
   (or use an online tool like https://emn178.github.io/online-tools/sha256.html)

2. Open `index.html`
3. Find this line:
   ```javascript
   const SECURE_TARGET_HASH = "5949062a739546c4695bafcfb1973abd91de0d4619478f009cb2fd52b8a90a84";
   ```
4. Replace with your new hash
5. Commit the change

### Change the Telegram Channel

Update the `TELEGRAM_CHANNEL_ID` GitHub secret in repo Settings.

### Customize the Form

Edit `index.html` directly. The form uses Tailwind CSS for styling.
All product fields are captured and sent to Telegram.

## File Structure

```
.
├── index.html                              # The form (frontend on GitHub Pages)
├── README.md                               # This file
├── .github/
│   └── workflows/
│       └── post-to-telegram.yml            # GitHub Action (backend logic)
├── scripts/
│   └── post_to_telegram.py                 # Python script that posts to Telegram
└── docs/
    └── SETUP.md                            # Detailed setup guide with screenshots
```

## How the Telegram Mini App Auto-Bypass Works

When a user opens the form inside Telegram (via a bot button with `web_app`),
Telegram injects a special object `window.Telegram.WebApp` with the user's
info already authenticated by Telegram.

The form checks if `tg.initDataUnsafe.user` exists:
- **If yes**: form auto-unlocks (Telegram Verified badge shown)
- **If no**: password screen is shown (Web Session)

For maximum security in production, you should also validate `tg.initData`
on a backend server using your bot token (HMAC-SHA256 verification). But
for a small catalog form, the auto-bypass is sufficient.

## Limitations (Honest Notes)

1. **Image uploads**: The form uses image URLs (not file uploads). Users must
   upload images to a free host (catbox.moe, imgur) and paste the URLs.
   This is because GitHub Issues API doesn't support file uploads from
   static sites without OAuth.

2. **PAT in frontend code**: The fine-grained PAT is visible in the browser.
   But it has ONLY `issues: write` permission on this ONE repo. Worst case
   is spam issues (deletable). For a more secure setup, you'd need a backend
   proxy (Cloudflare Workers free tier).

3. **Rate limits**: GitHub Actions free tier = 2,000 minutes/month for
   private repos, unlimited for public repos. This is way more than enough
   for a small business catalog.

4. **Issue history**: All submissions are saved as closed issues. You can
   see the full history at `https://github.com/xpunjabi/telegram-catalog/issues?q=is%3Aissue`

5. **No editing**: Once submitted, you can't edit a product via the form.
   You'd have to manually edit the Telegram message (or close the issue
   and resubmit).

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend hosting | GitHub Pages (free) |
| Frontend framework | Plain HTML + Tailwind CSS + vanilla JS |
| Auth (Telegram) | Telegram WebApp SDK (auto-bypass via initData) |
| Auth (Web) | SHA256 password hash (client-side check) |
| Database | GitHub Issues (each submission = 1 issue) |
| Backend | GitHub Actions (Python script) |
| Image hosting | External (catbox.moe, imgur — user provides URLs) |
| Bot API | Telegram Bot API (via Python requests) |
| Secrets | GitHub repository secrets |
| Auth token for issue creation | Fine-grained PAT (issues:write only) |

## License

Private project for A Collection / Narowal Cloth Hub.
