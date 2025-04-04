# Smart Office Assistant

Welcome to the **Smart Office Assistant** project! This repository contains a comprehensive system designed to streamline office management through face recognition-based attendance tracking, a chatbot for visitor and employee assistance, and an admin dashboard for managing employees and appointments.

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [File Descriptions](#file-descriptions)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview
The **Smart Office Assistant** is an intelligent office management system that leverages modern technologies to enhance workplace efficiency and security. It includes a face recognition system for automated attendance tracking, a chatbot for answering queries and booking appointments, and an admin interface for managing employee data and appointments.

This project is ideal for offices looking to automate attendance, improve visitor management, and provide an interactive assistant for employees and guests.

---

## Features
- **Face Recognition Attendance**: Employees can mark their attendance using facial recognition technology.
- **Chatbot Assistant**: A conversational AI that helps with appointment booking, office information, and answering common queries.
- **Admin Dashboard**: A web interface for managers to monitor attendance, manage employees, and handle appointments.
- **Employee Management**: Register new employees, assign tasks, and track attendance history.
- **Appointment System**: Schedule and manage visitor appointments with real-time availability checks.
- **Task Management**: Assign and track tasks for employees with reply functionality.
- **Responsive Design**: Web interfaces are optimized for both desktop and mobile devices.

---

## Technologies Used
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **Face Recognition**: OpenCV, LBPH Face Recognizer
- **Chatbot**: TensorFlow, NLTK (Natural Language Toolkit)
- **Text-to-Speech**: pyttsx3
- **External Libraries**: Chart.js, Font Awesome

---

## Project Structure
Here’s an overview of the directory structure:

```
Smart-Office-Assistant/
├── data/                  # Stores face recognition training images
├── static/                # Static files (CSS, images)
│   ├── css/
│   │   ├── style.css
│   │   └── styles.css
│   └── images/
│       └── imagefile
├── templates/             # HTML templates
│   ├── admin.html
│   ├── chatbot.html
│   ├── contact.html
│   ├── dash.html
│   ├── employee_attendance.html
│   ├── index.html
│   ├── new_user_login.html
│   ├── register_employee.html
│   ├── scan.html
│   ├── services.html
│   └── training.html
├── app.py                 # Main Flask application
├── chatbot.py             # Chatbot logic and AI model handling
├── dataset.py             # Face data collection script
├── face_recognition.py    # Face recognition script
├── id_maker.py            # Employee ID generation script
├── intents.JSON           # Chatbot intent definitions
├── new.py                 # Chatbot model training script
├── train.py               # Face recognition model training script
├── Trainer.yml            # Trained face recognition model (generated)
├── words.pkl              # Pickled chatbot vocabulary (generated)
├── classes.pkl            # Pickled chatbot classes (generated)
├── chatbot_model.h5       # Trained chatbot model (generated)
└── README.md              # This file
```

---

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git
- A webcam (for face recognition)

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/Smart-Office-Assistant.git
   cd Smart-Office-Assistant
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   If `requirements.txt` is not provided, install these packages:
   ```bash
   pip install flask opencv-python numpy tensorflow nltk pyttsx3 sqlite3 pillow
   ```

4. **Download NLTK Data**:
   Open a Python shell and run:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('wordnet')
   ```

5. **Initialize the Database**:
   The database (`attendance_system.db`) is automatically created when you run `app.py` for the first time.

---

## Usage

### Running the Application
1. **Start the Flask Server**:
   ```bash
   python app.py
   ```
   The application will run on `http://localhost:5000`.

2. **Access the Homepage**:
   Open your browser and navigate to `http://localhost:5000`.

3. **Register a Manager** (First Time):
   - Click the "Admin" button on the homepage.
   - Enter the admin credentials (ID: `admin123`, Designation: `Manager`).
   - Register a manager’s face via the `new_user_login` page.

4. **Employee Registration**:
   - Log in as an admin (`/admin`).
   - Navigate to "Register New Employee" and fill in the details.
   - Complete face registration for the new employee.

5. **Mark Attendance**:
   - From the homepage, click "click here" to start face recognition.
   - Once recognized, use the "Mark In" or "Mark Out" buttons on the scan page.

6. **Use the Chatbot**:
   - Visit `/chatbot` or get redirected if face recognition fails.
   - Ask questions or book appointments interactively.

7. **Admin Functions**:
   - Access `/admin` to view stats, manage employees, and handle appointments.

### Training the Models
- **Face Recognition Model**:
  Run `train.py` after collecting face data:
  ```bash
  python train.py
  ```
- **Chatbot Model**:
  Run `new.py` to train the chatbot model:
  ```bash
  python new.py
  ```

---

## File Descriptions

### Core Files
- **`app.py`**: Main Flask application handling routes and backend logic.
- **`chatbot.py`**: Chatbot implementation with intent recognition and appointment booking.
- **`dataset.py`**: Script to collect face data for training.
- **`face_recognition.py`**: Performs real-time face recognition.
- **`id_maker.py`**: Generates unique employee IDs.
- **`intents.JSON`**: Defines chatbot intents and responses.
- **`new.py`**: Trains the chatbot’s neural network model.
- **`train.py`**: Trains the face recognition model.

### Static Files
- **`style.css`**: Styling for login and registration pages.
- **`styles.css`**: General styling for other pages.

### Templates
- **`admin.html`**: Admin dashboard for managing employees and appointments.
- **`chatbot.html`**: Chatbot interface (currently Python-based, no frontend).
- **`contact.html`**: Contact information page.
- **`dash.html`**: Employee attendance dashboard.
- **`employee_attendance.html`**: Detailed employee attendance view for admins.
- **`index.html`**: Homepage with face recognition trigger.
- **`new_user_login.html`**: New user face registration page.
- **`register_employee.html`**: Employee registration form for admins.
- **`scan.html`**: Attendance marking page.
- **`services.html`**: Overview of offered services.
- **`training.html`**: Displays training progress for face recognition.

 Enjoy using the Smart Office Assistant!
