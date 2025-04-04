from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import subprocess
import os
import sqlite3
from datetime import datetime
import sys
import cv2
from chatbot import get_response
import pyttsx3
from id_maker import create_employee

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static')

app.secret_key = 'your_secret_key_here'



ADMIN_ID = "admin123"
ADMIN_DESIGNATION = "Manager"

def init_db():
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            position TEXT NOT NULL,
            department TEXT NOT NULL,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            check_in_time DATETIME NOT NULL,
            type TEXT DEFAULT 'in',
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            purpose TEXT,
            status TEXT DEFAULT NULL
        )
    """)

    # Add new table for tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            message TEXT NOT NULL,
            date_assigned DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
    """)
    
    # Add new table for task replies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            reply TEXT NOT NULL,
            date_replied DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES employee_tasks(id)
        )
    """)
    
    conn.commit()
    conn.close()

def mark_attendance(name):
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%d-%m-%Y")
        current_time = datetime.now().strftime("%H:%M:%S")
        cursor.execute("INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)",
                      (name, current_date, current_time))
        conn.commit()
        conn.close()
        return True, "Attendance marked successfully"
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recognize_face')
def recognize_face():
    try:
        process = subprocess.Popen(
            ['python', 'face_recognition.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        recognized_name = stdout.strip()

        if recognized_name == "Unknown":
            return jsonify({
                'status': 'error',
                'message': 'Face not recognized'
            })

        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT employee_id, name, position 
            FROM employees 
            WHERE name = ?
        """, (recognized_name,))
        
        result = cursor.fetchone()
        
        if result:
            employee_id, name, position = result
            session['employee_id'] = employee_id
            session['user_name'] = name
            session['position'] = position
            session['access_method'] = 'face'
            
            return jsonify({
                'status': 'success',
                'name': name,
                'user_type': position
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Employee not found in database'
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/admin_check')
def admin_check():
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees WHERE position = 'Manager'")
        manager_exists = cursor.fetchone()[0] > 0
        conn.close()

        if manager_exists:
            return jsonify({
                'status': 'success',
                'manager_exists': True
            })
        else:
            return jsonify({
                'status': 'no_manager',
                'message': 'No manager registered in the system'
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/admin_face_verify')
def admin_face_verify():
    try:
        process = subprocess.Popen(
            ['python', 'face_recognition.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        output_lines = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
        recognized_name = output_lines[-1]

        if not recognized_name or recognized_name == "Unknown":
            return jsonify({
                'status': 'error',
                'message': 'Face not recognized. Please try again.',
                'redirect': '/'
            })
        
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT position FROM employees WHERE name = ?", (recognized_name,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0].strip().lower() == 'manager':
            session['admin_authenticated'] = True
            session['admin_name'] = recognized_name
            session['position'] = result[0]
            return jsonify({
                'status': 'success',
                'message': 'Manager authenticated',
                'redirect': '/admin'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized: Only managers can access admin panel',
                'redirect': '/'
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error during verification: {str(e)}',
            'redirect': '/'
        })

@app.route('/admin')
def admin():
    print(f"Admin route accessed. Session data: {session}")  # Debug print
    
    # Check if user is authenticated as manager
    if session.get('admin_authenticated') or session.get('position') == 'Manager':
        print("Authenticated, rendering admin page")  # Debug print
        return render_template('admin.html', admin_name=session.get('admin_name', 'Manager'))
    else:
        print("Not authenticated, redirecting to home")  # Debug print
        return redirect('/')

@app.route('/new_user_login')
def new_user_login():
    return render_template('new_user_login.html')

@app.route('/start_face_recognition', methods=['POST'])
def start_face_recognition():
    try:
        data = request.get_json()
        
        # Extract user details from request
        employee_id = data.get('employee_id')
        name = data.get('name')
        dob = data.get('dob')
        position = data.get('position')
        department = data.get('department')

        # Validate required fields
        if not all([employee_id, name, dob, position, department]):
            return jsonify({
                'status': 'error',
                'message': 'All fields are required'
            })

        # Connect to database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()

        try:
            # Check if employee ID already exists
            cursor.execute('''
                SELECT employee_id, name, dob, position, department
                FROM employees 
                WHERE employee_id = ?
            ''', (employee_id,))
            
            existing_employee = cursor.fetchone()
            
            if existing_employee:
                # Verify that provided details match existing record
                db_employee_id, db_name, db_dob, db_position, db_department = existing_employee
                
                if name != db_name or dob != db_dob or position != db_position or department != db_department:
                    return jsonify({
                        'status': 'error',
                        'message': 'Details do not match existing employee record'
                    })
                
                # If we reach here, details match - proceed to collect face data for existing employee
                print(f"Collecting face data for existing employee: {name}")
            else:
                # Insert new employee into database
                cursor.execute('''
                    INSERT INTO employees (employee_id, name, dob, position, department)
                    VALUES (?, ?, ?, ?, ?)
                ''', (employee_id, name, dob, position, department))
                conn.commit()
                print(f"New employee added: {name}")

            # Start face data collection process
            process = subprocess.Popen(
                ['python', 'dataset.py', name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                # After collecting face data, train the model
                train_process = subprocess.Popen(
                    ['python', 'train.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                train_stdout, train_stderr = train_process.communicate()

                if train_process.returncode == 0:
                    return jsonify({
                        'status': 'success',
                        'message': 'Registration completed successfully'
                    })
                else:
                    raise Exception(f'Error in training: {train_stderr}')
            else:
                raise Exception(f'Error collecting face data: {stderr}')

        except sqlite3.IntegrityError:
            return jsonify({
                'status': 'error',
                'message': 'Database integrity error'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
        finally:
            conn.close()

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# Add this route to handle employee details retrieval if needed
@app.route('/get_employee_details/<employee_id>')
def get_employee_details(employee_id):
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT employee_id, name, dob, position, department 
            FROM employees 
            WHERE employee_id = ?
        ''', (employee_id,))
        
        employee = cursor.fetchone()
        
        if employee:
            return jsonify({
                'employee_id': employee[0],
                'name': employee[1],
                'dob': employee[2],
                'position': employee[3],
                'department': employee[4]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Employee not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/start_training', methods=['POST'])
def start_training():
    try:
        if not os.path.exists('data') or not os.listdir('data'):
            return jsonify({'status': 'error', 'message': 'No training data found'})
        
        process = subprocess.run(['python', 'train.py'], 
                               capture_output=True,
                               text=True,
                               timeout=300)
        
        if process.returncode == 0:
            return jsonify({'status': 'success'})
        else:
            print(f"Training error: {process.stderr}")
            return jsonify({'status': 'error', 'message': 'Training failed'})
            
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Training timeout'})
    except Exception as e:
        print(f"Error during training: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/start_recognition')
def start_recognition():
    try:
        process = subprocess.Popen(
            ['python', 'face_recognition.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        recognized_name = stdout.strip()
        
        if recognized_name and recognized_name != "Unknown":
            session['recognized_user'] = recognized_name
            return jsonify({
                'status': 'success',
                'name': recognized_name,
                'redirect': url_for('scan')
            })
        else:
            # Redirect to chatbot for unknown users
            return jsonify({
                'status': 'unknown',
                'redirect': url_for('chatbot_page')
            })
            
    except Exception as e:
        print(f"Error in face recognition: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/scan')
def scan():
    # Check if user is authenticated
    if 'user_name' not in session:
        print("DEBUG: User not authenticated, redirecting to index")
        return redirect(url_for('index'))
    
    print(f"DEBUG: User authenticated, rendering scan page. Session: {dict(session)}")
    return render_template('scan.html', 
                          user_name=session.get('user_name'),
                          position=session.get('position'))

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    conn = None  # Initialize conn to None
    try:
        data = request.json
        attendance_type = data.get('type')
        employee_id = session.get('employee_id')
        user_name = session.get('user_name')
        current_time = datetime.now()
        
        # Connect to database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        if not employee_id:
            # If employee_id is not in session, fetch it using the user_name
            cursor.execute("SELECT employee_id FROM employees WHERE name = ?", (user_name,))
            result = cursor.fetchone()
            if result:
                employee_id = result[0]
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Employee not found'
                })

        # Check if already marked for today
        cursor.execute("""
            SELECT type FROM attendance_log 
            WHERE employee_id = ? 
            AND DATE(check_in_time) = DATE(?)
            AND type = ?
        """, (employee_id, current_time, attendance_type))
        
        if cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': f'Already marked {attendance_type} for today'
            })

        # Insert new attendance record
        cursor.execute("""
            INSERT INTO attendance_log (employee_id, check_in_time, type)
            VALUES (?, ?, ?)
        """, (employee_id, current_time.strftime('%Y-%m-%d %H:%M:%S'), attendance_type))
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance marked successfully - {attendance_type.upper()}'
        })
    except Exception as e:
        print(f"Error marking attendance: {str(e)}")  # Add debug print
        return jsonify({
            'status': 'error',
            'message': str(e)
        })
    finally:
        if conn:
            conn.close()

@app.route('/view_attendance')
def view_attendance():
    # Check if user is authenticated
    if 'user_name' not in session:
        return redirect(url_for('index'))
    
    # Render the dash.html template with user data
    return render_template('dash.html', 
                          user_name=session.get('user_name'),
                          position=session.get('position'))

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/get_bot_response', methods=['POST'])
def get_bot_response_route():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'response': 'Invalid request'}), 400
            
        user_message = data['message']
        response = get_response(user_message)
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in get_bot_response: {str(e)}")
        return jsonify({'response': 'Sorry, I encountered an error.'}), 500

@app.route('/check_appointment_slot', methods=['POST'])
def check_appointment_slot():
    data = request.get_json()
    date = data.get('date')
    time = data.get('time')
    
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check if slot is available
        cursor.execute("""
            SELECT COUNT(*) FROM appointments 
            WHERE date = ? AND time = ? AND status != 'cancelled'
        """, (date, time))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({'available': count == 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    data = request.get_json()
    visitor_name = data.get('visitor_name')
    date = data.get('date')
    time = data.get('time')
    purpose = data.get('purpose')
    
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check if slot is available
        cursor.execute("""
            SELECT COUNT(*) FROM appointments 
            WHERE date = ? AND time = ? AND status != 'cancelled'
        """, (date, time))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'error': 'Slot not available'}), 400
        
        # Book the appointment
        cursor.execute("""
            INSERT INTO appointments (visitor_name, date, time, purpose)
            VALUES (?, ?, ?, ?)
        """, (visitor_name, date, time, purpose))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Appointment booked successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process_voice', methods=['POST'])
def process_voice():
    try:
        data = request.get_json()
        voice_input = data.get('voice_input', '')
        
        if not voice_input:
            return jsonify({'error': 'No voice input received'}), 400
            
        response = get_response(voice_input)
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/register_employee')
def register_employee():
    # Check if user is authenticated as manager through either method
    if not (session.get('recognized_user') == "Manager" or 
            session.get('admin_authenticated') or 
            session.get('position') == 'Manager'):
        return redirect(url_for('index'))
    return render_template('register_employee.html')

@app.route('/get_dashboard_stats')
def get_dashboard_stats():
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Get total number of employees - not filtering by status to get all employees
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = cursor.fetchone()[0] or 0
        print(f"DEBUG: Total employees found: {total_employees}")
        
        # Get today's attendance count (employees who marked in)
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(DISTINCT employee_id)
            FROM attendance_log
            WHERE DATE(check_in_time) = ?
            AND type = 'in'
        """, (today,))
        today_present = cursor.fetchone()[0] or 0
        print(f"DEBUG: Employees present today: {today_present}")
        
        # Get total ACTIVE appointments count (exclude completed ones)
        cursor.execute("""
            SELECT COUNT(*) FROM appointments 
            WHERE status IS NULL OR status != 'completed'
        """)
        appointments_count = cursor.fetchone()[0] or 0
        print(f"DEBUG: Active appointments: {appointments_count}")
        
        # Return the data
        return jsonify({
            'total_employees': total_employees,
            'today_present': today_present,
            'appointments': appointments_count
        })
    except Exception as e:
        print(f"Error in get_dashboard_stats: {str(e)}")
        return jsonify({
            'total_employees': 0,
            'today_present': 0,
            'appointments': 0
        })
    finally:
        if conn:
            conn.close()

@app.route('/get_attendance_log/<date>')
def get_attendance_log(date):
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                a.employee_id,
                e.name,
                e.department,
                time(a.check_in_time) as check_in_time,
                date(a.check_in_time) as date
            FROM attendance_log a
            JOIN employees e ON a.employee_id = e.employee_id
            WHERE DATE(a.check_in_time) = ?
            ORDER BY a.check_in_time DESC
        """, (date,))
        
        columns = ['employee_id', 'name', 'department', 'check_in_time', 'date']
        attendance_log = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify(attendance_log)
    except Exception as e:
        print(f"Error fetching attendance log: {str(e)}")
        return jsonify([])
    finally:
        if conn:
            conn.close()

@app.route('/generate_employee_id', methods=['POST'])
def generate_employee_id():
    data = request.json
    name = data.get('name')
    dob = data.get('dob')
    position = data.get('position')
    department = data.get('department')
    
    success, result = create_employee(name, dob, position, department)
    
    if success:
        return jsonify({'success': True, 'employee_id': result})
    else:
        return jsonify({'success': False, 'message': result})

@app.route('/get_employees')
def get_employees():
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Fetch all employees ordered by most recent first
        cursor.execute("""
            SELECT employee_id, name, department, position, date_created, status 
            FROM employees 
            ORDER BY date_created DESC
        """)
        
        employees = cursor.fetchall()
        
        # Convert to list of dictionaries for JSON response
        employee_list = []
        for emp in employees:
            employee_list.append({
                'employee_id': emp[0],
                'name': emp[1],
                'department': emp[2],
                'position': emp[3],
                'date_created': emp[4],
                'status': emp[5] if len(emp) > 5 else 'Active'
            })
        
        return jsonify(employee_list)
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify([])
        
    finally:
        if conn:
            conn.close()


@app.route('/verify_admin', methods=['POST'])
def verify_admin():
    try:
        data = request.get_json()
        admin_id = data.get('id')
        designation = data.get('designation')

        # Check if manager exists in database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees WHERE position = 'Manager'")
        manager_exists = cursor.fetchone()[0] > 0
        conn.close()

        # Verify credentials
        if admin_id == ADMIN_ID and designation == ADMIN_DESIGNATION:
            if not manager_exists:
                # No manager exists, proceed to registration
                session['registering_manager'] = True
                return jsonify({
                    'status': 'no_manager',
                    'redirect': '/register_new_manager'
                })
            else:
                # Manager exists, proceed to face recognition
                return jsonify({
                    'status': 'success',
                    'redirect': '/admin_face_verify'
                })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            })

    except Exception as e:
        print(f"Error in verify_admin: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/register_new_manager')
def register_new_manager():
    # Redirect to new_user_login with manager registration parameter
    return redirect('/new_user_login?register_manager=true')

@app.route('/save_manager', methods=['POST'])
def save_manager():
    try:
        data = request.get_json()
        if data.get('id') != ADMIN_ID or data.get('designation') != ADMIN_DESIGNATION:
            return jsonify({
                'status': 'error',
                'message': 'Invalid manager credentials'
            })
        
        session['registering_manager'] = True
        return jsonify({
            'status': 'success',
            'redirect': '/new_user_login'
        })
        
    except Exception as e:
        print(f"Error saving manager: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/get_user_info')
def get_user_info():
    """Return the current user's information from session"""
    if 'user_name' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    return jsonify({
        'name': session.get('user_name'),
        'position': session.get('position'),
        'employee_id': session.get('employee_id')
    })

@app.route('/check_attendance_status')
def check_attendance_status():
    """Check if the user has already marked in/out for today"""
    conn = None
    try:
        if 'user_name' not in session or 'employee_id' not in session:
            return jsonify({'error': 'User not authenticated'}), 401
        
        employee_id = session.get('employee_id')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check if marked in today
        cursor.execute("""
            SELECT type FROM attendance_log 
            WHERE employee_id = ? 
            AND DATE(check_in_time) = ? 
            AND type = 'in'
        """, (employee_id, current_date))
        marked_in = cursor.fetchone() is not None
        
        # Check if marked out today
        cursor.execute("""
            SELECT type FROM attendance_log 
            WHERE employee_id = ? 
            AND DATE(check_in_time) = ? 
            AND type = 'out'
        """, (employee_id, current_date))
        marked_out = cursor.fetchone() is not None
        
        return jsonify({
            'marked_in': marked_in,
            'marked_out': marked_out,
            'date': current_date
        })
    except Exception as e:
        print(f"Error checking attendance status: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_user_attendance/<username>')
def get_user_attendance(username):
    """Get attendance records for a specific user"""
    if 'user_name' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Get employee_id for the username
        cursor.execute("SELECT employee_id FROM employees WHERE name = ?", (username,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        employee_id = result[0]
        
        # Get attendance records
        cursor.execute("""
            SELECT 
                DATE(check_in_time) as date, 
                TIME(check_in_time) as time,
                type
            FROM attendance_log
            WHERE employee_id = ?
            ORDER BY check_in_time DESC
        """, (employee_id,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'date': row[0],
                'time': row[1],
                'type': row[2]
            })
        
        return jsonify({'records': records})
    except Exception as e:
        print(f"Error fetching attendance: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/dash')
def dash():
    """Render the attendance dashboard"""
    if 'user_name' not in session:
        return redirect(url_for('index'))
    
    return render_template('dash.html', 
                          user_name=session.get('user_name'),
                          position=session.get('position'))

@app.route('/employee_attendance/<employee_id>')
def employee_attendance(employee_id):
    """Render the employee attendance details page"""
    if not (session.get('admin_authenticated') or session.get('position') == 'Manager'):
        return redirect(url_for('index'))
    
    return render_template('employee_attendance.html', employee_id=employee_id)

@app.route('/get_employee_attendance/<employee_id>')
def get_employee_attendance(employee_id):
    """Get attendance records for a specific employee by ID"""
    if not (session.get('admin_authenticated') or session.get('position') == 'Manager'):
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Get attendance records including seconds for precise time calculations
        cursor.execute("""
            SELECT 
                DATE(check_in_time) as date, 
                TIME(check_in_time) as time,
                check_in_time as full_timestamp,
                type
            FROM attendance_log
            WHERE employee_id = ?
            ORDER BY check_in_time DESC
        """, (employee_id,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'date': row[0],
                'time': row[1],
                'timestamp': row[2],
                'type': row[3]
            })
        
        # Get employee status for accurate activity reporting
        cursor.execute("""
            SELECT status FROM employees WHERE employee_id = ?
        """, (employee_id,))
        status = cursor.fetchone()
        
        return jsonify({
            'records': records,
            'status': status[0] if status else 'Unknown'
        })
    except Exception as e:
        print(f"Error fetching attendance: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/get_appointments')
def get_appointments():
    """Get all appointments for admin dashboard"""
    if not (session.get('admin_authenticated') or session.get('position') == 'Manager'):
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Fetch appointments
        cursor.execute("""
            SELECT id, visitor_name, date, time, purpose, status
            FROM appointments
            WHERE status IS NULL OR status != 'completed'
            ORDER BY date DESC, time ASC
        """)
        
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                'id': row[0],
                'visitor_name': row[1],
                'date': row[2],
                'time': row[3],
                'purpose': row[4],
                'status': row[5]
            })
        
        return jsonify(appointments)
    except Exception as e:
        print(f"Error fetching appointments: {str(e)}")
        return jsonify([])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
def complete_appointment(appointment_id):
    """Mark an appointment as completed"""
    if not (session.get('admin_authenticated') or session.get('position') == 'Manager'):
        return jsonify({'success': False, 'message': 'Not authorized'}), 401
    
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check if appointment exists
        cursor.execute("SELECT id FROM appointments WHERE id = ?", (appointment_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False, 
                'message': 'Appointment not found'
            }), 404
        
        # Mark appointment as completed
        cursor.execute("""
            UPDATE appointments 
            SET status = 'completed' 
            WHERE id = ?
        """, (appointment_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Appointment marked as completed'
        })
    except Exception as e:
        print(f"Error completing appointment: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/delete_employee/<employee_id>', methods=['POST'])
def delete_employee(employee_id):
    if not (session.get('admin_authenticated') or session.get('position') == 'Manager'):
        return jsonify({
            'success': False,
            'message': 'Not authorized'
        }), 401

    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()

        # Get employee name before deletion
        cursor.execute("SELECT name FROM employees WHERE employee_id = ?", (employee_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404

        employee_name = result[0]

        # Delete employee from database
        cursor.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
        cursor.execute("DELETE FROM attendance_log WHERE employee_id = ?", (employee_id,))
        conn.commit()

        # Delete face recognition data
        data_dir = "data"
        if os.path.exists(data_dir):
            # Delete all images for this employee
            for filename in os.listdir(data_dir):
                if filename.startswith(f"{employee_name}."):
                    os.remove(os.path.join(data_dir, filename))

        # Retrain the face recognition model
        try:
            subprocess.run(['python', 'train.py'], 
                         capture_output=True,
                         text=True,
                         timeout=300)
        except subprocess.TimeoutExpired:
            print("Warning: Face recognition model training timed out")
        except Exception as e:
            print(f"Warning: Error retraining face recognition model: {str(e)}")

        return jsonify({
            'success': True,
            'message': 'Employee removed successfully'
        })

    except Exception as e:
        print(f"Error deleting employee: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/assign_task', methods=['POST'])
def assign_task():
    if not (session.get('admin_authenticated') or session.get('position') == 'Manager'):
        return jsonify({
            'success': False,
            'message': 'Not authorized'
        }), 401

    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        task_message = data.get('task_message')

        if not employee_id or not task_message:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400

        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()

        # Check if employee exists
        cursor.execute("SELECT employee_id FROM employees WHERE employee_id = ?", (employee_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404

        # Insert new task
        cursor.execute("""
            INSERT INTO employee_tasks (employee_id, message)
            VALUES (?, ?)
        """, (employee_id, task_message))
        
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Task assigned successfully'
        })

    except Exception as e:
        print(f"Error assigning task: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/get_employee_tasks/<employee_id>')
def get_employee_tasks(employee_id):
    if not (session.get('admin_authenticated') or session.get('position') == 'Manager'):
        return jsonify({
            'success': False,
            'message': 'Not authorized'
        }), 401

    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()

        # Get tasks with replies
        cursor.execute("""
            SELECT 
                t.id,
                t.message,
                t.date_assigned,
                t.status,
                r.reply,
                r.date_replied
            FROM employee_tasks t
            LEFT JOIN task_replies r ON t.id = r.task_id
            WHERE t.employee_id = ?
            ORDER BY t.date_assigned DESC, r.date_replied ASC
        """, (employee_id,))

        rows = cursor.fetchall()
        tasks = {}
        
        for row in rows:
            task_id = row[0]
            if task_id not in tasks:
                tasks[task_id] = {
                    'id': task_id,
                    'message': row[1],
                    'date': row[2],
                    'status': row[3],
                    'replies': []
                }
            if row[4]:  # If there's a reply
                tasks[task_id]['replies'].append({
                    'message': row[4],
                    'date': row[5]
                })

        return jsonify({
            'success': True,
            'tasks': list(tasks.values())
        })

    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/get_user_tasks/<username>')
def get_user_tasks(username):
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()

        # Get employee_id for the username
        cursor.execute("SELECT employee_id FROM employees WHERE name = ?", (username,))
        result = cursor.fetchone()

        if not result:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404

        employee_id = result[0]

        # Get tasks with replies
        cursor.execute("""
            SELECT 
                t.id,
                t.message,
                t.date_assigned,
                t.status,
                r.reply,
                r.date_replied
            FROM employee_tasks t
            LEFT JOIN task_replies r ON t.id = r.task_id
            WHERE t.employee_id = ?
            ORDER BY t.date_assigned DESC, r.date_replied ASC
        """, (employee_id,))

        rows = cursor.fetchall()
        tasks = {}
        
        for row in rows:
            task_id = row[0]
            if task_id not in tasks:
                tasks[task_id] = {
                    'id': task_id,
                    'message': row[1],
                    'date': row[2],
                    'status': row[3],
                    'replies': []
                }
            if row[4]:  # If there's a reply
                tasks[task_id]['replies'].append({
                    'message': row[4],
                    'date': row[5]
                })

        return jsonify({
            'success': True,
            'tasks': list(tasks.values())
        })

    except Exception as e:
        print(f"Error fetching user tasks: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/reply_to_task', methods=['POST'])
def reply_to_task():
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        reply = data.get('reply')

        if not task_id or not reply:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400

        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()

        # Insert reply
        cursor.execute("""
            INSERT INTO task_replies (task_id, reply)
            VALUES (?, ?)
        """, (task_id, reply))
        
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Reply sent successfully'
        })

    except Exception as e:
        print(f"Error sending reply: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Call this function when the app starts
if __name__ == '__main__':
    init_db()
    app.run(debug=True)