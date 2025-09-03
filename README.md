# Saaransh Link - URL Shortener with Analytics

A comprehensive URL shortening service built with Django, featuring user authentication, analytics tracking, QR code generation, and a REST API. Inspired by the Nepali word "Saaransh" meaning summary.

## Features

- **User Authentication**: Registration, login, email verification, password reset
- **URL Shortening**: Generate short URLs with custom aliases and expiry dates
- **Analytics**: Track clicks, unique visitors, referrers, browser/device info, geolocation
- **Dashboard**: User and admin dashboards with charts and data export
- **QR Codes**: Generate QR codes for shortened URLs
- **REST API**: Programmatic access to URL shortening functionality
- **Rate Limiting**: Prevent abuse with configurable limits
- **Security**: CSRF protection, XSS prevention, URL validation

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip and virtualenv

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd django-url-shortener
   ```

2. **Create virtual environment**
   ```bash
   # On Windows:
   python -m venv .venv
   .venv\Scripts\activate
   
   # On macOS/Linux:
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Configure Django Secret Key**
   ```bash
   # Generate a new secret key
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   
   # Copy the generated key to your .env file
   # SECRET_KEY=your-generated-secret-key-here
   ```

6. **Setup PostgreSQL Database**
   ```bash
   # Install PostgreSQL if not already installed
   # Windows: Download from https://www.postgresql.org/download/windows/
   # macOS: brew install postgresql
   # Ubuntu: sudo apt-get install postgresql postgresql-contrib
   
   # Create database and user
   psql -U postgres
   CREATE DATABASE urlshortener;
   CREATE USER urlshortener_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE urlshortener TO urlshortener_user;
   \q
   
   # Update .env file with database credentials
   ```

7. **Configure Email Settings (Optional but Recommended)**
   ```bash
   # For Gmail:
   # 1. Enable 2-factor authentication on your Google account
   # 2. Generate an App Password: https://myaccount.google.com/apppasswords
   # 3. Update .env file with your email and app password
   
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

8. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

9. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

10. **Collect static files**
    ```bash
    python manage.py collectstatic
    ```

11. **Run development server**
    ```bash
    python manage.py runserver
    ```

Visit http://127.0.0.1:8000 to access the application.

### Environment Variables (.env)

Make sure to configure these variables in your `.env` file:

```bash
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=urlshortener
DB_USER=urlshortener_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Email settings (for password reset and verification)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@saaranshlink.com

# App settings
BASE_URL=http://127.0.0.1:8000
```

## Project Structure

```
django-url-shortener/
├── accounts/          # User authentication and management
├── shortener/         # Core URL shortening functionality
├── analytics/         # Analytics and tracking utilities
├── api/              # REST API endpoints
├── templates/        # Django templates
├── static/           # Static files (CSS, JS, images)
├── media/            # User uploaded files (QR codes)
└── urlshortener/     # Main project settings
```

## API Endpoints

- `POST /api/shorten/` - Create shortened URL
- `GET /api/urls/` - List user's URLs
- `GET /api/urls/{id}/` - Get URL details
- `DELETE /api/urls/{id}/` - Delete URL
- `GET /api/urls/{id}/analytics/` - Get URL analytics

## Admin Interface

Access the Django admin at `/admin/` to manage users, URLs, and view system analytics.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
