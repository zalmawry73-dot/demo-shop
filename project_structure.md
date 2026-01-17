# Project Architecture

## Modular Monolith Structure (Target)

```ascii
/Store
├── /app
│   ├── /core               # Core Logic
│   │   ├── config.py       # Env Settings & DB Conn
│   │   ├── security.py     # Auth & JWT
│   │   ├── database.py     # SessionConfig
│   │   └── exceptions.py   # Global Handlers
│   │
│   ├── /modules            # Domain Modules
│   │   ├── /marketing
│   │   │   ├── models.py
│   │   │   └── service.py
│   │   ├── /sales          # Orders & POS
│   │   │   ├── models.py
│   │   │   └── service.py
│   │   ├── /inventory
│   │   │   ├── models.py
│   │   │   └── service.py
│   │   └── /settings
│   │       ├── models.py
│   │       └── service.py
│   │
│   ├── main.py             # App Entrypoint
│   └── dependencies.py     # Shared Deps
│
├── /static                 # Frontend Assets
│   ├── /css                # Compiled CSS
│   ├── /scss               # Source SCSS
│   └── /js                 # Vanilla JS Configs
│
├── /templates              # Jinja2 Templates
│   ├── /components         # Shared (Nav, Sidebar)
│   ├── dashboard.html
│   ├── pos.html
│   └── settings.html
│
├── requirements.txt
├── README.md
└── reset_db.py             # Dev Tool
```
