# 🚀 Deploy to PythonAnywhere - Complete Guide

Step-by-step guide to deploy your Waste Classifier on PythonAnywhere (FREE).

---

## 🎯 Why PythonAnywhere?

✅ **Free tier available** (no credit card needed)  
✅ **Persistent storage** (database doesn't reset)  
✅ **No sleep/wake delays** (always on)  
✅ **Easy to use** (beginner-friendly)  
✅ **Python pre-installed**  

**Free Tier Limits:**
- 1 web app
- 512 MB storage
- Good for portfolio projects

---

## 📝 Step 1: Sign Up for PythonAnywhere

1. Go to **https://www.pythonanywhere.com**
2. Click **"Pricing & signup"**
3. Choose **"Create a Beginner account"** (FREE)
4. Fill in:
   - Username: `your-username` (will be your URL)
   - Email
   - Password
5. Click **"Register"**
6. Verify your email

**Your app URL will be:** `https://your-username.pythonanywhere.com`

---

## 📦 Step 2: Upload Your Code to GitHub

**If not already done:**

```bash
cd waste-classifier

# Initialize git
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub (https://github.com/new)
# Then push
git remote add origin https://github.com/YOUR-USERNAME/waste-classifier.git
git branch -M main
git push -u origin main
```

---

## 💻 Step 3: Clone Your Code on PythonAnywhere

### A. Open Bash Console

1. Login to PythonAnywhere
2. Click **"Consoles"** tab at top
3. Click **"Bash"** to start a new console

### B. Clone Your Repository

```bash
# Clone your repo
git clone https://github.com/YOUR-USERNAME/waste-classifier.git

# Go into the directory
cd waste-classifier

# Check files
ls -la
```

You should see all your files: `app.py`, `db.py`, `requirements.txt`, etc.

---

## 🔧 Step 4: Set Up Virtual Environment

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) in prompt now
```

---

## 📥 Step 5: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# This will take 2-3 minutes
```

**Expected output:**
```
Successfully installed Flask-3.x scikit-learn-1.x pandas-2.x ...
```

---

## 🗄️ Step 6: Set Up Database & Models

```bash
# Generate training data
python generate_data.py

# Train models
python train.py

# Create admin account
python create_admin.py
```

When prompted:
```
Admin username: admin
Admin email: admin@example.com
Password: [choose strong password]
Confirm password: [same password]

✓ Admin user created!
```

**Test locally (optional):**
```bash
python app.py
# Press Ctrl+C to stop after confirming it starts
```

---

## 🌐 Step 7: Configure Web App

### A. Go to Web Tab

1. Click **"Web"** tab at top
2. Click **"Add a new web app"**
3. Click **"Next"** on the domain confirmation
4. Choose **"Manual configuration"** (NOT Flask)
5. Select **"Python 3.10"**
6. Click **"Next"**

### B. Configure Settings

On the Web tab, update these sections:

#### 1. **Source Code**
```
/home/your-username/waste-classifier
```
*(Replace `your-username` with your actual username)*

#### 2. **Working Directory**
```
/home/your-username/waste-classifier
```

#### 3. **Virtualenv**
```
/home/your-username/waste-classifier/venv
```

---

## ⚙️ Step 8: Configure WSGI File

### A. Open WSGI Configuration

1. Still on **Web** tab
2. Find section **"Code"**
3. Click on **WSGI configuration file** link  
   (Should be something like `/var/www/your-username_pythonanywhere_com_wsgi.py`)

### B. Replace ALL Content with This:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/your-username/waste-classifier'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['SECRET_KEY'] = 'your-secret-key-change-this-to-random-string'
os.environ['SESSION_COOKIE_SECURE'] = '0'  # Set to 1 if you enable HTTPS

# Import Flask app
from app import app as application
```

**⚠️ IMPORTANT:**
- Replace `your-username` with your actual PythonAnywhere username
- Change `SECRET_KEY` to a random string (use online generator or run: `python -c "import secrets; print(secrets.token_hex(32))"`)

### C. Save File

Click **"Save"** button at top right.

---

## 🔄 Step 9: Reload Web App

1. Go back to **Web** tab
2. Scroll to top
3. Click big green **"Reload your-username.pythonanywhere.com"** button
4. Wait 5-10 seconds

---

## ✅ Step 10: Test Your Live App

1. Click the link at top: `https://your-username.pythonanywhere.com`
2. You should see your homepage! 🎉

**Test these:**
- [ ] Homepage loads
- [ ] Sign up works
- [ ] Login works
- [ ] Make a prediction
- [ ] View history
- [ ] Admin dashboard (login with admin account)

---

## 🐛 Troubleshooting

### Problem: "Something went wrong" error page

**Solution:**

1. Go to **Web** tab
2. Click **"Error log"** link
3. Read the last few lines
4. Common issues:

#### Error: "No module named 'flask'"
```bash
# In Bash console:
cd ~/waste-classifier
source venv/bin/activate
pip install -r requirements.txt
```

#### Error: "No module named 'app'"
Check WSGI file:
- Path correct?
- `your-username` replaced?
- File saved?

#### Error: "FileNotFoundError: models/decision_tree.joblib"
```bash
# In Bash console:
cd ~/waste-classifier
source venv/bin/activate
python generate_data.py
python train.py
```

Then reload web app.

---

### Problem: Page loads but styles broken

**Solution:**

1. Go to **Web** tab
2. Scroll to **"Static files"** section
3. Add this mapping:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/your-username/waste-classifier/static` |

4. Click checkmark to save
5. Reload web app

---

### Problem: Database not persisting / data lost

**Good news:** PythonAnywhere free tier has persistent storage!

Your database is safe at:
```
/home/your-username/waste-classifier/instance/waste.db
```

Check if it exists:
```bash
ls -lh ~/waste-classifier/instance/waste.db
```

---

### Problem: Rate limiting not working

**Solution:** PythonAnywhere uses memory storage for rate limiting by default, which resets on app reload. This is fine for development.

For production rate limiting, you would need Redis (not available on free tier).

---

## 🔒 Step 11: Security Setup

### A. Generate Strong Secret Key

In Bash console:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (long random string).

### B. Update WSGI File

1. Go to **Web** tab → **WSGI configuration file**
2. Update this line:
```python
os.environ['SECRET_KEY'] = 'paste-your-generated-key-here'
```
3. Save and reload app

---

## 📊 Step 12: Create Demo Account (Optional)

```bash
# In Bash console
cd ~/waste-classifier
source venv/bin/activate
python create_admin.py
```

Create a demo user:
- Username: `demo`
- Email: `demo@example.com`
- Password: `demo123`

Now visitors can try your app without signing up!

---

## 🔄 Step 13: Update Your App (Future Changes)

When you make changes:

### A. Update Code on GitHub
```bash
# On your local computer
git add .
git commit -m "Update feature X"
git push
```

### B. Pull Changes on PythonAnywhere

```bash
# In PythonAnywhere Bash console
cd ~/waste-classifier
git pull

# If you updated requirements.txt
source venv/bin/activate
pip install -r requirements.txt

# If you changed database schema
python migrate_db.py
```

### C. Reload Web App

Go to **Web** tab → Click **"Reload"** button

---

## 📝 Step 14: Add Your URL to README

Update your GitHub README:

```markdown
## 🚀 Live Demo

**👉 [Try it here](https://your-username.pythonanywhere.com)**

Demo Login:
- Username: `demo`
- Password: `demo123`

Hosted on PythonAnywhere (free tier)
```

Commit and push:
```bash
git add README.md
git commit -m "Add live demo link"
git push
```

---

## 🎯 PythonAnywhere Cheat Sheet

### Useful Commands

```bash
# Restart bash console
exit

# View files
ls -la ~/waste-classifier/

# Check database
sqlite3 ~/waste-classifier/instance/waste.db
.tables
.quit

# View logs
tail -50 ~/waste-classifier/app.log

# Check disk usage
quota

# Update code
cd ~/waste-classifier
git pull
source venv/bin/activate
pip install -r requirements.txt
```

### Important Paths

| Item | Path |
|------|------|
| Project | `/home/your-username/waste-classifier` |
| Virtualenv | `/home/your-username/waste-classifier/venv` |
| Database | `/home/your-username/waste-classifier/instance/waste.db` |
| Logs | `/home/your-username/waste-classifier/app.log` |
| WSGI | `/var/www/your-username_pythonanywhere_com_wsgi.py` |

---

## 📊 Monitor Your App

### A. View Error Logs

**Web tab** → **"Error log"** link

Shows Flask errors, exceptions.

### B. View Server Logs

**Web tab** → **"Server log"** link

Shows access logs, requests.

### C. View App Logs

```bash
# In Bash console
tail -f ~/waste-classifier/app.log
```

Shows your custom logs (predictions, feedback, etc.)

---

## 🎓 Tips for Free Tier

### Storage Management

Free tier: **512 MB**

Check usage:
```bash
quota
```

Save space:
```bash
# Remove pip cache
pip cache purge

# Remove old logs
rm ~/waste-classifier/app.log

# Remove __pycache__
find ~/waste-classifier -type d -name __pycache__ -exec rm -r {} +
```

### Performance Tips

- Keep `requirements.txt` minimal
- Use SQLite (no need for PostgreSQL on free tier)
- Optimize images/assets
- Enable browser caching

---

## 🚀 Upgrade Options (Optional)

If you outgrow the free tier:

| Plan | Price | Features |
|------|-------|----------|
| Hacker | $5/month | More CPU, storage, always-on tasks |
| Web Developer | $12/month | Multiple apps, more resources |

But free tier is perfect for portfolio projects!

---

## ✅ Final Checklist

- [ ] Code cloned from GitHub
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Models trained
- [ ] Admin account created
- [ ] Web app configured
- [ ] WSGI file updated with correct paths
- [ ] SECRET_KEY set to random value
- [ ] Web app reloaded
- [ ] Homepage loads successfully
- [ ] All features tested
- [ ] Demo account created (optional)
- [ ] README updated with live URL

---

## 🎉 Success!

Your Waste Classifier is now LIVE! 🚀

**Your Links:**
- 🌐 Live App: `https://your-username.pythonanywhere.com`
- 💻 Source Code: `https://github.com/YOUR-USERNAME/waste-classifier`
- 📊 Admin: `https://your-username.pythonanywhere.com/admin`

**Share it:**
- Add to your resume
- Post on LinkedIn
- Share with friends
- Add to portfolio

---

## 📞 Need Help?

**PythonAnywhere Help:**
- Forums: https://www.pythonanywhere.com/forums/
- Help pages: https://help.pythonanywhere.com/

**Project Help:**
- Check `app.log` in your project folder
- Review error logs on Web tab
- Open GitHub issue

---

**Congratulations! You're now deployed!** 🎊

Time to share your project with the world! 🌍
