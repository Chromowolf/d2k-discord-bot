# Discord Bot Docker Setup

This guide explains how to manage your Discord bot using Docker.

## Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system

## Building and Running the Bot

To build and start the bot in detached mode:

```bash
docker-compose up -d --build
```

## Managing Your Bot

### Viewing Logs

```bash
docker-compose logs -f discord-bot
```

### Controlling the Bot

```bash
# Stop the bot without removing containers
docker-compose stop discord-bot

# Start a stopped bot
docker-compose start discord-bot

# Restart after code changes (no rebuild needed)
docker-compose restart discord-bot

# Stop and remove containers
docker-compose down
```

### When to Rebuild

Rebuild the container with `docker-compose up -d --build` when you:
- Modify the Dockerfile
- Update requirements.txt
- Change docker-compose.yml

No rebuild needed when:
- Updating code in src/ (just restart)
- Changing .env file (just restart)

## Quick Reference

| Action | Command |
|--------|---------|
| Build and start | `docker-compose up -d --build` |
| Stop bot (keep container) | `docker-compose stop discord-bot` |
| Start stopped bot | `docker-compose start discord-bot` |
| Restart bot | `docker-compose restart discord-bot` |
| View logs | `docker-compose logs -f discord-bot` |
| Stop and remove containers | `docker-compose down` |
| Check container status | `docker-compose ps` |
