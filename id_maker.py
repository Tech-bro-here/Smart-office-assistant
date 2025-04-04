import sqlite3
from datetime import datetime
import random
import string

def generate_employee_id(name, dob):
    # Generate unique employee ID using name initials, year, and random numbers
    initials = ''.join(word[0].upper() for word in name.split())
    year = datetime.now().strftime('%y')
    random_nums = ''.join(random.choices(string.digits, k=4))
    return f"{initials}{year}{random_nums}"

def create_employee(name, dob, position, department):
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Generate employee ID
        employee_id = generate_employee_id(name, dob)
        date_created = datetime.now().strftime("%Y-%m-%d")
        
        # Check if employee already exists
        cursor.execute("SELECT COUNT(*) FROM employees WHERE name=? AND dob=?", 
                      (name, dob))
        if cursor.fetchone()[0] > 0:
            return False, "Employee already exists"
        
        # Ensure department and position are not None
        department = department or "Not Specified"
        position = position or "Not Specified"
        
        # Insert new employee with all fields
        cursor.execute("""
            INSERT INTO employees (
                employee_id, name, dob, date_created, position, department
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (employee_id, name, dob, date_created, position, department))
        
        conn.commit()
        return True, employee_id
    except sqlite3.Error as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()