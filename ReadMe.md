# Discord Bot Docker Setup

This README explains how to build, run, and maintain the Discord bot using Docker.

## Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system

## Initial Setup

1. Clone this repository to your local machine
2. Ensure your `.env` file is in the root directory with your bot token and other configuration
3. Place your Python code in the `src/` directory

## Building and Running the Bot

To build and start the bot in detached mode:

```bash
docker-compose up -d --build
```

This command:
- Builds the Docker image using the Dockerfile
- Creates and starts a container
- Runs the container in the background (detached mode)

## Managing Your Bot

### Viewing Logs

To see the bot's logs:

```bash
docker-compose logs -f discord-bot
```

The `-f` flag follows the logs in real-time.

### Making Changes

#### When you update Python code in src/

Since the `src/` directory is mounted as a volume to the container, code changes are immediately available to the container. After making changes:

```bash
docker-compose restart discord-bot
```

No rebuild is necessary for code changes!

#### When you update Dockerfile

If you modify the Dockerfile (e.g., changing the base image or adding new system dependencies):

```bash
docker-compose up -d --build
```

This rebuilds the image with your changes and recreates the container.

#### When you update requirements.txt

If you add or update Python dependencies in requirements.txt:

```bash
docker-compose up -d --build
```

This rebuilds the image, installing the updated dependencies, and recreates the container.

#### When you update docker-compose.yml

If you change the docker-compose.yml file (e.g., adding new services or changing configuration):

```bash
docker-compose up -d --build
```

This applies the new configuration and rebuilds if necessary.

#### When you update .env file

If you update environment variables in your .env file:

```bash
docker-compose up -d
```

No rebuild is needed, but the container needs to be recreated to pick up the new environment variables.

## Stopping the Bot

To stop the bot:

```bash
docker-compose down
```

To stop the bot and remove the built images:

```bash
docker-compose down --rmi local
```

## Troubleshooting

### Container fails to start or crashes

Check the logs:

```bash
docker-compose logs discord-bot
```

### Checking container status

```bash
docker-compose ps
```

### Forcefully rebuild everything

If you're having unexplained issues:

```bash
docker-compose down
docker-compose up -d --build --force-recreate
```

## Quick Reference

| Action | Command |
|--------|---------|
| Start bot | `docker-compose up -d` |
| Build and start | `docker-compose up -d --build` |
| View logs | `docker-compose logs -f discord-bot` |
| Restart bot | `docker-compose restart discord-bot` |
| Stop bot | `docker-compose down` |
| Update after code change | `docker-compose restart discord-bot` |
| Update after dependency change | `docker-compose up -d --build` |

## File Structure

```
my-discord-bot/
├── .env                  # Environment variables
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker image instructions
├── README.md             # This file
└── src/                  # Your bot's source code
    ├── main.py           # Bot entry point
    └── ...               # Other Python modules
```