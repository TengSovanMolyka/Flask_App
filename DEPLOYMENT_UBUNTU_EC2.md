# Ubuntu EC2 Deployment Guide for Flask Application

This step-by-step guide explains how to host your Flask application on an **AWS EC2 instance** running **Ubuntu 22.04 / 24.04 LTS** using **Gunicorn**, **Nginx**, and **Systemd**.

---

## 📋 Overview of Files Created for Deployment

- `wsgi.py` - WSGI entrypoint for Gunicorn.
- `.env.example` - Template for environment variables (`SECRET_KEY`, `DATABASE_URL`, `TELEGRAM_TOKEN`, etc.).
- `flaskapp.service` - Systemd service template to run Gunicorn as a background daemon.
- `flaskapp.nginx` - Nginx server configuration template for reverse proxying and static files.
- `deploy.sh` - Automated bash script to pull updates and restart the service.

---

## 🚀 Step-by-Step Setup Guide

### Step 1: AWS EC2 Security Group Setup
In your AWS EC2 Console, ensure your Security Group allows the following inbound traffic:
- **SSH** (Port 22) - Your IP
- **HTTP** (Port 80) - Anywhere (`0.0.0.0/0`)
- **HTTPS** (Port 443) - Anywhere (`0.0.0.0/0`)

---

### Step 2: System Update & Package Installation
Connect to your EC2 instance via SSH:
```bash
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Update packages and install dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git
```

---

### Step 3: Clone Codebase to Server
Create application directory and grant permissions to user `ubuntu`:
```bash
sudo mkdir -p /var/www/flask_app
sudo chown -R ubuntu:ubuntu /var/www/flask_app
cd /var/www/flask_app
```

Clone your Git repository into `/var/www/flask_app`:
```bash
git clone YOUR_GIT_REPO_URL .
```

---

### Step 4: Python Virtual Environment & Dependencies
Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create production `.env` file from template:
```bash
cp .env.example .env
nano .env
```
> Update `SECRET_KEY` with a strong random string (e.g. generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`).

---

### Step 5: Database Setup & Migrations
Initialize database tables using Flask-Migrate:
```bash
export FLASK_APP=wsgi.py
flask db upgrade
```
*(Optionally run your admin reset script if needed: `python reset_admin.py`)*

Ensure proper write permissions for SQLite database & static uploads:
```bash
sudo chown -R ubuntu:www-data /var/www/flask_app
chmod -R 775 /var/www/flask_app/instance
chmod -R 775 /var/www/flask_app/static/uploads
```

---

### Step 6: Configure Systemd Service (Gunicorn)
Copy the service configuration file:
```bash
sudo cp flaskapp.service /etc/systemd/system/flaskapp.service
```

Start and enable the systemd service:
```bash
sudo systemctl daemon-reload
sudo systemctl start flaskapp
sudo systemctl enable flaskapp
```

Verify service status:
```bash
sudo systemctl status flaskapp
```

---

### Step 7: Configure Nginx Reverse Proxy
Copy Nginx configuration:
```bash
sudo cp flaskapp.nginx /etc/nginx/sites-available/flaskapp
```

Edit `/etc/nginx/sites-available/flaskapp` to set your domain or EC2 Public IP:
```bash
sudo nano /etc/nginx/sites-available/flaskapp
```

Enable the configuration by creating a symlink:
```bash
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

Test Nginx configuration and restart:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

### Step 8: (Optional) HTTPS Setup with Let's Encrypt Certbot
If you attached a custom domain to your EC2 IP address:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 🔄 Updating Your Application

To deploy new code updates in the future:
```bash
cd /var/www/flask_app
chmod +x deploy.sh
./deploy.sh
```

---

## 🛠️ Helpful Debugging Commands

- **Check Gunicorn Logs:**
  ```bash
  sudo journalctl -u flaskapp -f
  ```
- **Check Nginx Logs:**
  ```bash
  sudo tail -f /var/log/nginx/error.log
  ```
- **Restart Services:**
  ```bash
  sudo systemctl restart flaskapp
  sudo systemctl restart nginx
  ```
