# Retail Analytics Dashboard – Setup & Run Guide

## Requirements (install once on a new PC)

1. **Python 3.11 or newer**
   Download: https://www.python.org/downloads/

2. **Git**
   Download: https://git-scm.com/downloads

3. **VS Code (recommended)**
   Download: https://code.visualstudio.com/

---

# 1. Clone the Project

Open **PowerShell** and run:

```powershell
git clone https://github.com/JKooner1/HonoursProject.git
cd HonoursProject
```

---

# 2. Create the Python Environment

Run:

```powershell
python -m venv .venv
```

Install the project dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Note:

* The `.venv` folder is **not pushed to GitHub**.
* Each computer creates its own environment.

---

# 3. Run the Backend API (Terminal 1)

Open a **PowerShell terminal** in the project folder and run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

API will run at:

```
http://127.0.0.1:8000
```

Test endpoints:

```
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

---

# 4. Run the Dashboard (Terminal 2)

Open **another PowerShell terminal** in the project folder and run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\dashboard\app.py
```

Dashboard opens at:

```
http://localhost:8501
```

---

# 5. Normal Development Workflow

Start the system using two terminals.

### Terminal 1

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

### Terminal 2

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\dashboard\app.py
```

---

# 6. Stop the Servers

Press:

```
CTRL + C
```

in each terminal.

---

# Project Structure

```
HonoursProject
│
├── api
│   └── main.py
│
├── dashboard
│   └── app.py
│
├── app
│   └── settings.py
│
├── data
│   └── .gitkeep
│
├── requirements.txt
└── README.md
```

---

# Quick Setup Summary

```powershell
git clone https://github.com/JKooner1/HonoursProject.git
cd HonoursProject
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run:

```powershell
# Terminal 1
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

```powershell
# Terminal 2
.\.venv\Scripts\python.exe -m streamlit run .\dashboard\app.py
```
