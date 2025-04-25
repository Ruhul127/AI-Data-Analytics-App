# 📊 Data Analytics Dashboard with AI Insights

A Flask-powered web app for instant data analysis, rich visualizations, and AI-generated insights — just upload your dataset and let the dashboard do the rest.

![Dashboard Preview](Assets/Example1.PNG) <!-- Update with real screenshot -->

---

## 🚀 Features

- **📂 Upload CSV or Excel files (max 5MB)**
- **📈 Auto-generated analysis**
  - Data shape summary
  - Descriptive statistics (mean, median, etc.)
- **📊 Visualizations**
  - Histograms for numeric columns
- **🧠 AI Insights**
  - GPT-generated summaries
  - Data quality checks
  - Suggestions for further analysis
- **🌓 Responsive UI**
  - Works across devices
  - Toggle between light/dark mode

---

## 🗂️ Project Structure

```text
├── app.py                  # Entry point of the Flask app
├── analytics.db            # SQLite database for logging
├── requirements.txt        # Python dependencies
├── uploads/                # Uploaded user datasets
├── Assets/                 # Image assets and screenshots
│   ├── Example1.PNG
│   └── ...                 
├── static/                 # Frontend assets
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── script.js
├── templates/
│   └── index.html          # Main HTML template
├── Test_API/
│   └── TestAPI.py          # Isolated testing/experimental API logic
```

---

## 🛠️ Technologies Used

| Layer      | Tech Stack                              |
|------------|------------------------------------------|
| **Backend** | Flask, Python, OpenAI API               |
| **Frontend**| HTML5, CSS3, JavaScript                 |
| **AI**      | OpenAI GPT (gpt-3.5-turbo / gpt-4)       |
| **Data**    | Pandas, Matplotlib                      |
| **DB**      | SQLite (for logging)                    |

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/data-analytics-dashboard.git
cd data-analytics-dashboard

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate     # On Windows use `venv\Scripts\activate`

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" > .env
```

---

## ▶️ Usage

```bash
# Run the app
python app.py
```

Open your browser and go to [http://localhost:5000](http://localhost:5000)

Upload a file → See analysis → Get insights.

---

## 🔌 API Endpoints

| Endpoint     | Method | Description            |
|--------------|--------|------------------------|
| `/`          | GET    | Homepage with upload   |
| `/upload`    | POST   | Upload and analyze CSV/Excel file |

---

## 🧾 Database Schema

```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_ip TEXT,
    row_count INTEGER,
    column_count INTEGER
);
```

---

## 📦 Requirements

Python 3.7+ and these packages:

```txt
flask
flask-cors
pandas
openai
matplotlib
python-dotenv
```

---

## 📸 Screenshots

| Upload Interface             | AI Insights                 |
|-----------------------------|-----------------------------|
| ![Upload](Assets/Example2.PNG) | ![Insights](Assets/Example3.PNG) |

---
