# DialogBot Framework

## 📌 Overview

A universal dialog system built with Python and MongoDB, designed around a YAML-based configuration architecture and external handler modules.  
The project is decoupled from any specific API and can be used across Telegram, web interfaces, and other channels.  
All behavior is defined declaratively — through YAML files and plugin-style Python modules.  
Suitable for educational projects, service bots, surveys, CRM automation, and complex multi-step user interaction flows.

---

## ⚙️ Key Features

- Full dialog flow control via YAML files (no hardcoded logic in the codebase)
- Behavior and input processing handled via external Python handlers
- Asynchronous engine built on `asyncio`, optimized for single-thread use with up to 50 concurrent users
- MongoDB integration using `motor` for non-blocking state and history storage
- Placeholder support in responses (`[mark]`, `[errors]`, etc.)
- Deferred user state synchronization with dirty-flag mechanism
- Automatic `id` generation to prevent YAML reference collisions
- External API caching with TTL and global access layer
- Enhanced error logging system

---

## 🛠️ Architecture and Internals

The system follows a clean separation between presentation (YAML) and behavior (Python handlers), enabling:

- scenario updates without restarting the server
- plug-in logic without modifying the core
- unified engine usage across different platforms and APIs

---

## 🔗 Examples and Configuration

- Dialog flow examples can be found in the [`dialogs/`](./dialogs) directory  
- The [`configExample.yaml`](./configExample.yaml) file provides a sample project configuration

---

## 🧩 Planned Features

- [ ] Support for attachments and message forwarding between users (e.g., customer support)
- [ ] YAML template generator for rapid scenario creation
- [ ] Visual editor or YAML validation tool
- [ ] CI/CD pipeline for testing YAML logic and handler modules
- [ ] Extended user input handling and interactive patterns
- [ ] Dynamic loading of new scenarios and GitHub-based scenario hosting support

---

## 🚦 Project Status

The project is under active development.  
Core functionality is in place, and the architecture is stable.  
The design is focused on long-term maintainability, modular growth, and scalable deployment.