# color-wizard

A Discord bot that creates color roles based on hex codes or color names.

## Features

- `/pick` slash command to choose your name color
- Accepts hex codes (e.g., `#FF5733`, `FF5733`, `#F00`)
- Accepts color names (e.g., `red`, `blue`, `coral`, `mediumseagreen`)
- Automatically creates roles if they don't exist
- Removes previous color roles when switching colors

## Setup

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Copy the bot token
5. Enable the following Privileged Gateway Intents:
   - Server Members Intent

### 2. Invite the Bot

1. Go to OAuth2 → URL Generator
2. Select scopes: `bot`, `applications.commands`
3. Select bot permissions: `Manage Roles`
4. Use the generated URL to invite the bot to your server

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your bot token:

```
DISCORD_TOKEN=your_discord_bot_token_here
```

### 4. Run with Docker

```bash
docker compose up -d
```

### 5. Run Locally (Development)

```bash
pip install -r requirements.txt
python bot.py
```

## Usage

In Discord, use the slash command:

```
/pick color:#FF5733
/pick color:red
/pick color:coral
/pick color:mediumseagreen
```

The bot will create a role with that color (if it doesn't exist) and assign it to you.

## Supported Color Names

The bot uses the [webcolors](https://webcolors.readthedocs.io/) library which supports:
- CSS3 color names (140+ colors)
- Examples: `red`, `blue`, `green`, `coral`, `salmon`, `mediumseagreen`, `darkviolet`, etc.
