# Smart Waste Classification System

![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-green.svg)
![Version](https://img.shields.io/badge/version-2.1-brightgreen.svg)

> AI-powered waste classification with **image upload**, confidence scoring, and user feedback

## 🌟 Features

### Core ML Features
- **4 ML Models**: Decision Tree, Random Forest, SVM, Naive Bayes with majority voting
- **Confidence Scoring**: 0-100% confidence on every prediction
- **Input Validation**: Detects impossible combinations (e.g., biodegradable glass)
- **5 Waste Categories**: Recyclable, Organic, Hazardous, E-Waste, General Waste

### NEW! Image Upload (v2.1) 📸
- ✨ **Upload waste images** (PNG, JPG, GIF, WebP)
- ✨ **Image preview** before submission
- ✨ **History with thumbnails** - click to enlarge
- ✨ **Stored securely** with user tracking
- ✨ **Foundation for CNN** classification (coming soon!)

### User Features
- 💬 **User Feedback System** - Mark predictions correct/incorrect
- 📊 **Prediction History** - Track all your classifications
- 🎨 **Light/Dark Theme** - Auto or manual switch
- 📱 **Responsive Design** - Works on mobile & desktop

### Admin Features
- 📈 **Real Accuracy Tracking** - From user feedback
- 🎯 **Model Performance** - Individual model stats
- 📊 **Analytics Dashboard** - Trends, charts, metrics
- 💾 **CSV Export** - Full data with images & feedback

### Security & Production
- 🛡️ **Rate Limiting** - Prevent abuse (Flask-Limiter)
- 🔐 **Authentication** - Secure signup/login
- 🪵 **Logging** - Structured logging to file
- 🏥 **Health Checks** - Startup model validation

## Workflow

1. **Enter Waste Features**: material, wet/dry, texture, biodegradability
2. **Run ML Models**: Decision Tree, Random Forest, SVM, Naive Bayes
3. **Display Prediction**: Recyclable, Organic, Paper, Metal or General Waste (final answer by majority vote)
4. **Disposal Guidance**: bin colour, do's and don'ts, and a tip

## The four models in simple words

| Model | What it does |
|---|---|
| Decision Tree | Classifies waste using feature-based rules, like a flowchart |
| Random Forest | Combines the predictions of many decision trees |
| SVM | Separates categories using the material features |
| Naive Bayes | Predicts the category from the probability of features |

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python generate_data.py         # creates dataset/waste_data.csv (400 rows)
python train.py                 # trains models, saves to models/
python create_admin.py admin you@example.com   # asks for a password; creates YOUR admin account
python app.py                   # open http://127.0.0.1:5000
```

Users can now **sign up / log in**. Every prediction is saved to a SQLite database
(`instance/waste.db`, created automatically) under the user's name.

## Theme (light + dark)

The site has a light and a dark theme. The ☀️/🌙 button in the top bar switches between them; the choice is remembered in the browser, and the first visit follows the device setting. Colours come from the four bin colours: green (organic, buttons), blue (recyclable/paper, links), yellow (metal) and red (warnings and "Don't" tips). To change the palette, edit the variables at the top of `static/css/style.css` (`:root` for light, `[data-bs-theme="dark"]` for dark) and the bin colours in `disposal_guide.py`.

## Accounts, history and admin dashboard

| Page | Who | What |
|---|---|---|
| `/signup`, `/login`, `/logout` | everyone | Account system (passwords are hashed, never stored as plain text) |
| `/` and `/predict` | logged-in users | Classify waste; each result is saved to the user's account |
| `/history` | logged-in users | The user's own past predictions |
| `/compare` | everyone | Model accuracy chart |
| `/admin` | admin only | Total users, total predictions, today's count, new users (7 days), charts, user list |
| `/admin/export.csv` | admin only | Download every prediction as CSV (for Excel) |

**Making yourself admin:** `python create_admin.py <username> <email>`. If the username already exists, that account is promoted to admin.

**Getting the data on your PC:** log in as admin, open `/admin` and click **Download CSV**. To fetch it automatically every day, see `sync_to_pc.py`.

**Where the data lives:** `instance/waste.db` (SQLite). Back this file up. You can change its location with the `DATABASE_PATH` environment variable.

**Before going live:** set a fixed `SECRET_KEY` environment variable, and `SESSION_COOKIE_SECURE=1` once the site is on HTTPS.

## Project structure

```
waste-classifier/
├── app.py               Flask routes: auth, classify, history, compare, admin, CSV
├── db.py                SQLite tables (users, predictions)
├── create_admin.py      create or promote an admin account
├── sync_to_pc.py        optional: download the CSV from your live site to your PC
├── train.py             trains and evaluates the 4 models
├── generate_data.py     builds the dataset
├── disposal_guide.py    bin colour + do's/don'ts per category
├── dataset/waste_data.csv
├── models/              saved .joblib models + model_comparison.json
├── templates/           index, result, compare, login, signup, history, admin (+ base, steps)
├── static/              css/style.css, js/theme.js, js/compare.js, js/admin.js
├── requirements.txt
└── README.md
```

## Category rules used in the dataset

| Materials | Category | Bin |
|---|---|---|
| plastic, glass | Recyclable | Blue |
| paper, cardboard | Paper | Blue (paper) |
| metal | Metal | Yellow |
| food, vegetable | Organic | Green |
| textile, e-waste, other | General Waste | Black |

## Sample test inputs

| Material | Wet/Dry | Texture | Biodegradable | Expected |
|---|---|---|---|---|
| vegetable | wet | soft | yes | Organic |
| metal | dry | hard | no | Metal |
| plastic | dry | smooth | no | Recyclable |

## Note on accuracy

The dataset is synthetic and rule-based, so the models score very high (often 100%). That is expected for a demo. To get more realistic, differing scores, replace `dataset/waste_data.csv` with a real or noisier dataset that has the same columns and re-run `python train.py`.

## Ideas to extend

- Add an image-based classifier (CNN) alongside these feature-based models
- Add local disposal rules for your city in `disposal_guide.py`
- Add password reset by email
