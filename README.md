# Door Face Panels

Smart door security & anomaly detection system for elderly care facilities.

---

## Architecture

| Layer    | Tech              | Port |
|----------|-------------------|------|
| Backend  | Python / Flask    | 5000 |
| Frontend | Next.js (React)   | 3000 |

The Flask server exposes a REST API only. The Next.js app is the dashboard and proxies all `/api/*` requests to Flask automatically.

---

## Prerequisites

- Python 3.8+
- Node.js 18+ and npm — download from https://nodejs.org

---

## Running the project

### 1 — Start the Flask API

```bash
# Install Python dependencies (first time only)
pip install -r requirements.txt

# Start the API server
python main.py
```

Flask will be available at http://localhost:5000

### 2 — Start the Next.js frontend

Open a **second** terminal:

```bash
cd frontend

# Install Node dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

The dashboard will be available at **http://localhost:3000**

---

## Building the frontend for production

```bash
cd frontend
npm run build
npm start
```

---

![alt text](image.png)
![alt text](image-1.png)
![alt text](image-2.png)
![alt text](image-3.png)