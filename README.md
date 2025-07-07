# ✈️ Australian Flight Tracking Dashboard

A real-time web-based dashboard to monitor live Australian air traffic using OpenSky Network API. Built using **Flask**, **Bootstrap**, **Chart.js**, and integrated with AI-based market analysis. Ideal for hostel operators, travel planners, and aviation enthusiasts looking for actionable insights into domestic and international airspace activity.

---

## 📌 Features

- 🌏 **Live Air Traffic Monitoring** (Australia-specific)
- 📍 **City-specific Flight Tracking**
- 📊 **Categorization**: Domestic / International / Grounded
- ⏱ **Auto-Refreshing Interface** (every 5 minutes)
- 🎨 **Data Visualization** using Chart.js
- 🤖 **AI-Enhanced Market Analysis** (Gemini AI / Structured)
- 🧠 **Formatted Output for Hostel Operators**: Emoji-based summaries and decision hints

---

## 🛠️ Tech Stack

| Layer         | Tools Used                        |
|--------------|------------------------------------|
| Backend       | Python, Flask                     |
| Frontend      | HTML5, Bootstrap, Chart.js         |
| Data Source   | OpenSky Network API               |
| AI Integration| Gemini AI (Initially), Programmatic Analytics |
| Hosting       | Localhost (Flask server)          |

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/aus-flight-dashboard.git
cd aus-flight-dashboard
```
### 2. Create & Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```
### 3. Install Dependencies
```bash
Flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
pytz==2024.1
```
### 4. Add Your OpenSky API Credentials
```bash
OPENSKY_USERNAME=your_opensky_username
OPENSKY_PASSWORD=your_opensky_password
```
### 5. In env file
```bash
GOOGLE_API_KEY=GEMINI_API_KEY
```
### 6. Run the Flask Application
```bash
python app.py
```
