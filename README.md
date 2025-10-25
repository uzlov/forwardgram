# Forwardgram

> **Automated Telegram message forwarding with intelligent transformation and scheduling**

Forwardgram is a production-ready Telegram bot application that forwards messages from multiple source channels to designated destination channels with advanced filtering, price adjustment, tag generation, and scheduled delivery.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🚀 Features

### Core Functionality

- **Multi-Channel Forwarding** - Forward from multiple source channels to single destination channels
- **Queue-Based Processing** - Reliable message queuing with database persistence (MariaDB)
- **Scheduled Delivery** - Batch forwarding with configurable intervals (default: 45 minutes)
- **Event-Driven Architecture** - Real-time message handling with Telegram API integration

### Message Transformations

- **🔍 Keyword Filtering** - Allow/disallow lists with regex pattern matching
- **💰 Price Adjustment** - Progressive price increases with currency-specific rules
- **🏷️ Tag Generation** - Multi-language tag generation (Russian/Ukrainian)
- **📸 Media Handling** - Support for photos, documents, and grouped albums
- **🧹 Content Cleaning** - Remove links, user mentions, emails, hashtags
- **🌍 Language Detection** - Automatic language detection based on unique character patterns

### Advanced Features

- **Configuration-Driven** - YAML-based configuration with environment separation (dev/prod)
- **Per-Channel Settings** - Granular control with default settings and channel-specific overrides
- **Database Persistence** - Queue state preserved across restarts
- **Graceful Shutdown** - Proper cleanup of timers and connections
- **Type Safety** - Full type hints and dataclasses for reliability
- **Docker Support** - Containerized deployment with Docker Compose and Kubernetes templates

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Development](#-development)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🏗️ Architecture

Forwardgram uses a **modular Object-Oriented architecture** with 8 specialized components:

```
┌────────────────────────────────────────────────────┐
│                     ForwardgramApp                 │
│                  (Main Orchestrator)               │
└────────────┬───────────────────────────────────────┘
             │
    ┌────────┴────────┬──────────┬──────────┬────────┐
    │                 │          │          │        │
┌───▼────┐  ┌────────▼───┐  ┌───▼─────┐  ┌▼────────┐ │
│Config  │  │  Database  │  │  Queue  │  │Scheduler│ │
│Manager │  │  Manager   │  │ Manager │  │ Manager │ │
└────────┘  └────────────┘  └─────────┘  └─────────┘ │
                                                     │
    ┌────────────────────────────────────────────────┘
    │                 │                    │
┌───▼────────┐  ┌────▼──────────┐  ┌─────▼──────┐
│  Telegram  │  │   Message     │  │ Data Types │
│  Client    │  │  Processor    │  │            │
└────────────┘  └───────────────┘  └────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **ForwardgramApp** | Application orchestration and lifecycle management |
| **ConfigurationManager** | YAML configuration loading and validation |
| **DatabaseManager** | MariaDB operations with connection pooling |
| **QueueManager** | Message queue lifecycle with timer management |
| **SchedulerManager** | AsyncIO job scheduling and sending status tracking |
| **TelegramClientManager** | Telegram API client and entity resolution |
| **MessageProcessor** | Text filtering, price adjustment, tag generation |
| **Data Types** | Type-safe dataclasses and enumerations |

---

## 🔧 Prerequisites

- **Python 3.10+** (recommended: 3.10.7)
- **Docker** and **Docker Compose** (for containerized deployment)
- **MariaDB** or **MySQL** database
- **Telegram API Credentials** ([obtain here](https://my.telegram.org/apps))

---

## 📦 Installation

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/forwardgram.git
cd forwardgram

# Copy environment configuration
cp .env.default .env
cp docker-compose.override.default.yml docker-compose.override.yml

# Edit .env and set COMPOSE_PROJECT_NAME
nano .env

# Build and start
make
```

### Option 2: Local Python

```bash
# Clone the repository
git clone https://github.com/yourusername/forwardgram.git
cd forwardgram

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt

# Run application
python app/main.py app/config.global.dev.yml app/tags.prod.yml
```

---

## ⚙️ Configuration

### 1. Global Configuration

Create `app/config.global.{env}.yml`:

```yaml
# Telegram API credentials
api_id: 12345678
api_hash: "your_api_hash_here"

# Environment
env: "dev"  # or "prod"
session_name: "forwardgram"
logging_level: "INFO"

# Database configuration
db_config:
  host: "localhost"
  user: "forwardgram"
  password: "your_password"
  database: "forwardgram"
```

### 2. Tags Configuration

Create `app/tags.prod.yml` for global tag generation rules:

```yaml
global_tags:
  product_type:
    ru:
      "платье": "платье"
      "юбка": "юбка"
    ua:
      "сукня": "сукня"
      "спідниця": "спідниця"
  colors:
    ru:
      "черный": "черный"
      "белый": "белый"
    ua:
      "чорний": "чорний"
      "білий": "білий"
```

### 3. Channel Configuration

Create channel configs in `app/configs.{env}/`:

```yaml
# app/configs.dev/example.yml
redirector_channel_id: "123456789"  # Optional
output_channel_id: "111222333"      # Required

input_channels:
  "444555666":  # Source channel ID
    allowed_keywords:
      - "sale"
      - "discount"
    prices:
      - pattern: "([0-9]+)\\s*(грн|uah)"
        value: 50
        currency: " грн"

channel_settings_default:
  close_queue_interval: 2700  # 45 minutes
  links: false                # Remove links
  users: false                # Remove user mentions
  emails: false               # Remove emails
  hash_tags: false            # Remove hashtags
  media_without_message: false
  allowed_keywords:
    - ".*"  # Allow all by default
  prices:
    - pattern: "([0-9]+)\\s*(грн)"
      value: 100
      currency: " грн"
  progressive_values:
    - limit: 500
      value: 50
    - limit: 1000
      value: 100
  tags:
    - "recommend"
  brand_id: "brand123"
```

---

## 🚀 Usage

### Docker Commands

```bash
# Full setup (build, stop, start)
make

# Start application
make start

# Stop application
make stop

# Rebuild containers
make rebuild

# Restart application
make restart

# Execute commands in container
make exec app bash
```

### Direct Python Execution

```bash
# OOP entry point (recommended)
python app/main.py app/config.global.dev.yml app/tags.prod.yml

# Legacy monolithic entry point (backward compatibility)
python app/forwardgram.py app/config.global.dev.yml app/tags.prod.yml
```

### Channel Discovery

To find channel IDs:

```python
# Edit app/main.py and set channel_names list
channel_names = ["Channel Name 1", "Channel Name 2"]
python app/main.py app/config.global.dev.yml
```

---

## 🛠️ Development

### Project Structure

```
forwardgram/
├── app/
│   ├── main.py                    # OOP entry point
│   ├── forwardgram.py            # Legacy entry point
│   ├── forwardgram/              # Modular architecture
│   │   ├── app.py               # Main orchestrator
│   │   ├── config_manager.py    # Configuration
│   │   ├── database_manager.py  # Database operations
│   │   ├── queue_manager.py     # Queue management
│   │   ├── scheduler_manager.py # Job scheduling
│   │   ├── telegram_client.py   # Telegram client
│   │   ├── message_processor.py # Transformations
│   │   └── data_types.py        # Type definitions
│   ├── configs.dev/             # Dev configurations
│   ├── configs.prod/            # Prod configurations
│   └── requirements.txt         # Dependencies
├── docker/
│   ├── Dockerfile.dev
│   └── Dockerfile.prod
├── sessions/                     # Telegram sessions
├── docker-compose.yml
├── Makefile
└── README.md
```

### Running Tests

```bash
# Adjust testing intervals in app/forwardgram/app.py
SENDING_INTERVAL = 15  # 15 seconds for testing
SENDING_MESSAGE_INTERVAL_MIN = 5
SENDING_MESSAGE_INTERVAL_MAX = 15
```

### Adding New Features

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Implement in appropriate manager class**
3. **Add type hints and docstrings**
4. **Update configuration if needed**
5. **Test locally**: `python app/main.py ...`
6. **Submit pull request**

---

## 🚢 Deployment

### Docker Compose (Production)

```bash
# Edit production environment
nano .env

# Start production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Edit Kubernetes templates
nano kubernetes.deployment.tpl.yml
nano kubernetes.storage.tpl.yml

# Apply configuration
kubectl apply -f kubernetes.storage.tpl.yml
kubectl apply -f kubernetes.deployment.tpl.yml
```

### GitLab CI/CD

The project includes `.gitlab-ci.yml` for automated deployment:

- **Staging**: Auto-deploy on `develop` branch
- **Production**: Manual deploy on `main` branch

---

## 📊 Message Processing Pipeline

```
┌─────────────────┐
│  New Message    │ (Telegram Event)
└────────┬────────┘
         │
┌────────▼────────┐
│ Queue Creation  │ (Per-channel, per-config)
└────────┬────────┘
         │
┌────────▼────────┐
│   Filtering     │ (Keywords, media type)
└────────┬────────┘
         │
┌────────▼────────┐
│ Transformation  │ (Remove links, adjust prices, add tags)
└────────┬────────┘
         │
┌────────▼────────┐
│ Queue Storage   │ (Database persistence)
└────────┬────────┘
         │
┌────────▼────────┐
│ Scheduled Send  │ (45-min intervals, rate-limited)
└─────────────────┘
```

---

## 📝 Configuration Examples

### Simple Forwarding

```yaml
output_channel_id: "123456789"
input_channels:
  "987654321": {}
channel_settings_default:
  close_queue_interval: 2700
```

### Advanced Filtering and Transformation

```yaml
output_channel_id: "123456789"
input_channels:
  "987654321":
    allowed_keywords:
      - "платье"
      - "юбка"
    disallowed_keywords:
      - "spam"
    prices:
      - pattern: "([0-9]+)\\s*грн"
        value: 100
        currency: " грн"
channel_settings_default:
  close_queue_interval: 2700
  links: false
  users: false
  progressive_values:
    - limit: 500
      value: 50
    - limit: 1000
      value: 100
  tags:
    - "recommend"
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Follow Python PEP 8 style guide
5. Add type hints to all functions
6. Update documentation
7. Submit pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- [APScheduler](https://apscheduler.readthedocs.io/) - Job scheduling
- [MariaDB](https://mariadb.org/) - Database

---

## 📞 Support

For issues, questions, or contributions:

- **Issues**: [GitHub Issues](https://github.com/yourusername/forwardgram/issues)

---

**Built with ❤️ for automated Telegram channel management**
