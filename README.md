# Demo Shop - E-Commerce Platform

🛒 **Complete e-commerce store** built with FastAPI, SQLite/PostgreSQL, and modern web technologies.

## 🌐 Live Demo
- **URL**: https://demo-shop.onrender.com
- **Admin Login**: `admin@store.com` / `admin123`

## ✨ Features

### 🏪 Core E-Commerce
- **POS System**: Point of Sale for quick orders
- **Product Management**: Full catalog with variants, options, images
- **Order Management**: Complete order lifecycle
- **Customer Management**: CRM with advanced filtering
- **Inventory Tracking**: Multi-warehouse stock management

### 📊 Business Tools
- **Reports & Analytics**: Sales, inventory, customer reports
- **Settings Management**: Store configuration, taxes, shipping
- **Team Management**: User roles and permissions
- **Notifications**: Email/SMS alerts for orders

### 🎨 User Interface
- **RTL Arabic Support**: Fully localized
- **Responsive Design**: Works on all devices
- **Modern UI**: Clean, professional interface

## 🚀 Quick Start

### Local Development
```bash
# Clone
git clone https://github.com/YOUR_USERNAME/demo-shop.git
cd demo-shop

# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run
python -m uvicorn app.main:app --reload
```

Visit: http://localhost:8000

### Deploy to Render.com
See [DEPLOY_CHEATSHEET.md](DEPLOY_CHEATSHEET.md) for full guide.

```bash
git push
# Auto-deploys! 🚀
```

## 📁 Project Structure
```
demo-shop/
├── app/
│   ├── modules/        # Feature modules
│   │   ├── auth/       # Authentication
│   │   ├── catalog/    # Products & categories
│   │   ├── sales/      # Orders & POS
│   │   ├── customers/  # CRM
│   │   ├── inventory/  # Stock management
│   │   └── settings/   # Configuration
│   ├── core/           # Database, schemas
│   └── main.py         # FastAPI app
├── static/             # CSS, JS, images
├── templates/          # Jinja2 HTML templates
└── requirements.txt    # Python dependencies
```

## 🔧 Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite (local) / PostgreSQL (production)
- **ORM**: SQLAlchemy (async)
- **Frontend**: Jinja2 templates, Vanilla JS
- **Styling**: Bootstrap 5 + Custom CSS
- **Deployment**: Render.com

## 🔐 Security
- JWT Authentication
- Password hashing (Argon2)
- CSRF protection
- SQL injection prevention

## 📝 License
MIT License

## 👨‍💻 Author
Built with ❤️ for e-commerce solutions

---

**Need help?** Check the [deployment guide](render_deployment_guide.md)
