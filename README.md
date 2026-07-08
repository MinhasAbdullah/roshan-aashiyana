# 🏠 Roshan Aashiyana — Pakistan's Real Estate Marketplace

<div align="center">

![Roshan Aashiyana](https://roshanaashiyana.xyz/static/images/RA3.png)

**A full-stack AI-powered real estate marketplace connecting property buyers, renters, and verified dealers across Pakistan.**

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-roshanaashiyana.xyz-3cb648?style=for-the-badge)](https://roshanaashiyana.xyz)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django)](https://djangoproject.com)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql)](https://neon.tech)
[![Railway](https://img.shields.io/badge/Deployed_on-Railway-0B0D0E?style=for-the-badge&logo=railway)](https://railway.app)

</div>

---

## 📸 Screenshots

> *(Add your screenshots here)*

| Homepage | Property Listings | Property Detail |
|----------|------------------|-----------------|
| ![Home](screenshots/home.png) | ![Listings](screenshots/listings.png) | ![Detail](screenshots/detail.png) |

| Dealer Dashboard | AI Description Generator | Dealer Profile |
|-----------------|--------------------------|----------------|
| ![Dashboard](screenshots/dashboard.png) | ![AI](screenshots/ai.png) | ![Profile](screenshots/profile.png) |

---

## ✨ Features

### 👤 Users
- 📧 Email verification on signup via **Resend API**
- 🔐 Secure login/logout with session management
- ❤️ Save favourite properties
- 📩 Send inquiries directly to dealers
- ⭐ Leave reviews and ratings on properties
- 🔑 Forgot password / reset password flow
- ✏️ Change username and password from account dropdown

### 🏠 Properties
- 🔍 Advanced search with 6+ filters — city, type, purpose, price, bedrooms, keyword
- 📊 Sort by latest, price low-high, price high-low
- 🏷️ Property types: House, Apartment, Plot, Shop, Room
- 📍 10+ major Pakistani cities
- 🖼️ Featured image + gallery support via **Cloudinary**
- 👁️ View counter per listing

### 🤝 Dealers
- 💳 One-time registration fee via **Stripe Checkout**
- ✅ Dealer verification system
- 📋 Full property management dashboard (add, edit, delete)
- 📬 Inquiry management with email notifications
- ⚙️ Profile settings — bio, contact, social links
- 🤖 **AI-powered description generator** using **Mistral AI + LangChain**
- 📈 Analytics — total views, total inquiries
- 🌐 Social media links on public dealer profile

### 🔒 Security
- CSRF protection on all forms
- Password hashing via Django auth
- Email verification before account activation
- Stripe payment verification on dealer registration
- `DEBUG=False` in production

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 6.0, Python 3.13 |
| **Database** | PostgreSQL (Neon) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Image Storage** | Cloudinary |
| **Payments** | Stripe Checkout |
| **Email** | Resend API (HTML emails) |
| **AI** | Mistral AI + LangChain |
| **Deployment** | Railway |
| **Static Files** | WhiteNoise |
| **Web Server** | Gunicorn |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- PostgreSQL database (or Neon free tier)
- Cloudinary account
- Stripe account
- Resend account
- Mistral AI API key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/MinhasAbdullah/roshan-aashiyana.git
cd roshan-aashiyana

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Fill in your credentials

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver
```

### Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

DATABASE_URL=your_neon_postgresql_url

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_SECRET_KEY=your_stripe_secret_key

RESEND_API_KEY=your_resend_api_key

MISTRAL_API_KEY=your_mistral_api_key
```

---

## 📁 Project Structure

```
roshan-aashiyana/
│
├── ghr/                        # Main Django app
│   ├── migrations/             # Database migrations
│   ├── static/                 # CSS, JS, Images
│   │   ├── css/                # Stylesheets per page
│   │   ├── js/                 # JavaScript files
│   │   └── images/             # Static images
│   ├── templates/              # HTML templates
│   │   ├── base.html           # Base template
│   │   ├── home.html           # Homepage
│   │   ├── listings.html       # Property listings
│   │   ├── property_detail.html
│   │   ├── dashboard.html      # Dealer dashboard
│   │   └── ...
│   ├── models.py               # Database models
│   ├── views.py                # View functions
│   ├── urls.py                 # URL patterns
│   └── agent.py                # Mistral AI agent
│
├── myproject/                  # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── requirements.txt
├── Procfile                    # Railway deployment
├── .env.example
└── manage.py
```

---

## 🤖 AI Description Generator

One of the standout features — dealers can auto-generate professional property descriptions using **Mistral AI**.

**How it works:**
1. Dealer fills in property details (title, price, location, rooms, features)
2. Clicks **"Generate with AI"** button
3. A LangChain prompt template formats the data
4. Mistral AI (`mistral-small-latest`) generates an 80-120 word professional description
5. Description auto-fills in the textarea instantly

```python
# ghr/agent.py
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

def generate_description(data: dict) -> str:
    llm = ChatMistralAI(model='mistral-small-latest', temperature=0)
    chain = prompt | llm
    return chain.invoke(data).content.strip()
```

---

## 📧 Email System

All transactional emails are sent via **Resend API** as branded HTML emails:

| Trigger | Email Sent |
|---------|-----------|
| User signup | Email verification link |
| Email verified | Welcome email |
| Dealer registered | Dealer account created |
| Inquiry submitted | Notification to dealer |
| Forgot password | Password reset link |

---

## 🗃️ Database Models

```
User (Django built-in)
├── Dealer (OneToOne)
│   └── Properties (ForeignKey)
│       ├── PropertyImage (ForeignKey)
│       ├── Features (ManyToMany)
│       ├── DealerReview (ForeignKey)
│       └── Inquiry (ForeignKey)
├── Favorite (ForeignKey)
└── ContactMessage
```

---

## 🌐 Deployment

This project is deployed on **Railway** with the following setup:

- **Build Command:** `python manage.py collectstatic --noinput`
- **Start Command:** `gunicorn myproject.wsgi --bind 0.0.0.0:$PORT`
- **Database:** Neon PostgreSQL (serverless)
- **Static Files:** WhiteNoise + Railway build phase
- **Media Files:** Cloudinary (direct upload)

---

## 📄 License

This project is for portfolio and educational purposes.

---

## 👨‍💻 Author

**Abdullah Minhas**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Abdullah_Minhas-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/abdullah-minhas-6798b932a/)
[![GitHub](https://img.shields.io/badge/GitHub-MinhasAbdullah-181717?style=flat&logo=github)](https://github.com/MinhasAbdullah)
[![Live](https://img.shields.io/badge/Live-roshanaashiyana.xyz-3cb648?style=flat)](https://roshanaashiyana.xyz)

---

<div align="center">
  <strong>⭐ Star this repo if you found it useful!</strong>
</div>