import random
import json
import pickle
import numpy as np
import nltk
import pyttsx3
import sys
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model  # type: ignore
import re
from datetime import datetime
import sqlite3

# Initialize NLTK lemmatizer
lemmatizer = WordNetLemmatizer()

# Load the required data only once when the module is imported
try:
    with open('intents.json', 'r') as file:
        intents = json.load(file)
    
    words = pickle.load(open('words.pkl', 'rb'))
    classes = pickle.load(open('classes.pkl', 'rb'))
    model = load_model('chatbot_model.h5')
except Exception as e:
    print(f"Error loading chatbot files: {str(e)}")
    raise

# Initialize text-to-speech engine
try:
    engine = pyttsx3.init()
except Exception as e:
    print(f"Error initializing text-to-speech: {str(e)}")
    engine = None

def speak_text(text):
    """Function to convert text to speech"""
    try:
        if engine:
            engine.say(text)
            engine.runAndWait()
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")

class AppointmentState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.name = None
        self.date = None
        self.time = None
        self.purpose = None
        self.current_state = None
        self.is_urgent = False

appointment_state = AppointmentState()

def validate_date(date_str):
    """Validate the date format and return a datetime object or None."""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        return None

def validate_time(time_str):
    """Check if the provided time is valid."""
    valid_times = ['9:00', '10:00', '11:00', '14:00', '15:00', '16:00']
    return time_str in valid_times

def is_time_passed(time_str):
    """Check if the provided time is in the past."""
    return time_str < datetime.now().strftime("%H:%M")

def is_date_within_one_month(date):
    """Check if the date is within one month from now."""
    return (date - datetime.now()).days <= 30

def extract_name(message):
    # Extract name from patterns like "My name is John" or "I am John"
    patterns = [
        r"my name is (.+)",
        r"i am (.+)",
        r"(.+) is my name",
        r"call me (.+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return match.group(1).strip()
    return message.strip()

def check_appointment_availability(date, time):
    """Check if the appointment slot is available."""
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute(""" 
            SELECT COUNT(*) FROM appointments 
            WHERE date = ? AND time = ? AND status != 'cancelled'
        """, (date, time))
        count = cursor.fetchone()[0]
        return count == 0
    except Exception as e:
        print(f"Database error: {str(e)}")
        return False
    finally:
        conn.close()

def book_appointment(name, date, time, purpose):
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (visitor_name, date, time, purpose)
            VALUES (?, ?, ?, ?)
        """, (name, date, time, purpose))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database error: {str(e)}")
        return False

def bag_of_words(sentence):
    # Add the bag_of_words function implementation here
    # This function should be implemented according to your training process
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    bag = [1 if word in sentence_words else 0 for word in words]
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list

def is_urgent_request(user_input):
    """Check if the request is urgent based on keywords"""
    urgent_keywords = ['urgent', 'emergency', 'asap', 'right away', 'immediately', 'today']
    return any(keyword in user_input.lower() for keyword in urgent_keywords)

def extract_employee_name(pattern, message):
    """Extract employee name from the message based on the pattern."""
    # Remove the asterisk from the pattern and escape special characters
    pattern = re.escape(pattern.replace('*', ''))
    # Create a regex pattern that captures the name
    regex = pattern.replace('\\\\\\*', '(.+)')
    match = re.search(regex, message, re.IGNORECASE)
    return match.group(1) if match else None

def handle_employee_query(message, intent):
    """Handle queries about specific employees."""
    # Find the matching pattern that contains an asterisk
    matching_pattern = None
    for pattern in intent['patterns']:
        if '*' in pattern and re.search(pattern.replace('*', '.+'), message, re.IGNORECASE):
            matching_pattern = pattern
            break
    
    if matching_pattern:
        employee_name = extract_employee_name(matching_pattern, message)
        if employee_name:
            return f"For information about {employee_name}, please contact our reception desk at 123-456-7890. For privacy reasons, I cannot directly provide personal contact details."
    
    return random.choice(intent['responses'])

def get_response(user_input):
    """Generate a response based on user input."""
    global appointment_state
    response = None

    try:
        # Check for cancellation request during appointment booking
        if appointment_state.current_state and user_input.lower() in ['cancel', 'stop', 'quit', 'exit']:
            appointment_state.reset()
            return "Appointment booking cancelled. How else can I help you?"

        # Check for urgent appointment requests
        if is_urgent_request(user_input):
            return ("For urgent appointments, please contact our emergency booking line at 123-456-7890. "
                   "They can assist you with immediate scheduling needs.")

        # Handle appointment booking flow
        if appointment_state.current_state == "get_name":
            appointment_state.name = extract_name(user_input)
            appointment_state.current_state = "get_date"
            return "Please provide the date for your appointment (DD-MM-YYYY). You can say 'cancel' at any time to stop booking."
        
        elif appointment_state.current_state == "get_date":
            date = validate_date(user_input)
            if date is None:
                return "Invalid date format. Please use DD-MM-YYYY format, or say 'cancel' to stop booking."
            if date < datetime.now():
                return "The date you provided is in the past. Please provide a future date, or say 'cancel' to stop booking."
            if not is_date_within_one_month(date):
                return "You can only book appointments within the next month. Please provide a valid date, or say 'cancel' to stop booking."
            appointment_state.date = user_input
            appointment_state.current_state = "get_time"
            return "What time would you prefer? Available slots: 9:00, 10:00, 11:00, 14:00, 15:00, 16:00. You can say 'cancel' to stop booking."
        
        elif appointment_state.current_state == "get_time":
            if not validate_time(user_input):
                return "Invalid time. Please choose from available slots, or say 'cancel' to stop booking."
            if is_time_passed(user_input) and appointment_state.date == datetime.now().strftime("%d-%m-%Y"):
                return "The time you provided has already passed. Please choose a future time, or say 'cancel' to stop booking."
            if not check_appointment_availability(appointment_state.date, user_input):
                return "Sorry, that slot is not available. Please choose another time, or say 'cancel' to stop booking."
            appointment_state.time = user_input
            appointment_state.current_state = "get_purpose"
            return "What's the purpose of your meeting? You can say 'cancel' to stop booking."
        
        elif appointment_state.current_state == "get_purpose":
            appointment_state.purpose = user_input
            if book_appointment(
                appointment_state.name,
                appointment_state.date,
                appointment_state.time,
                appointment_state.purpose
            ):
                appointment_details = (
                    f"Great! Your appointment has been booked.\n"
                    f"Details:\n"
                    f"Name: {appointment_state.name}\n"
                    f"Date: {appointment_state.date}\n"
                    f"Time: {appointment_state.time}\n"
                    f"Purpose: {appointment_state.purpose}"
                )
                appointment_state.reset()
                return appointment_details
            else:
                appointment_state.reset()
                return "Sorry, there was an error booking your appointment. Please try again."
        
        # Handle other intents
        intents_list = predict_class(user_input)
        if intents_list:
            tag = intents_list[0]['intent']
            for intent in intents['intents']:
                if intent['tag'] == tag:
                    # Special handling for employee-related queries
                    if tag == "find_employee":
                        return handle_employee_query(user_input, intent)
                    elif tag == "book_appointment":
                        appointment_state.current_state = "get_name"
                        return "I'll help you book an appointment. What's your name? You can say 'cancel' at any time to stop booking."
                    else:
                        return random.choice(intent['responses'])
        
        # Handle unknown requests with more helpful response
        return ("I'm not sure I understand. Could you please rephrase that? You can ask about:\n"
                "- Booking appointments\n"
                "- Office information\n"
                "- Employee locations\n"
                "- IT support\n"
                "- Maintenance requests\n"
                "- Security issues\n"
                "- Facilities and amenities\n"
                "Or type 'help' for more options.")

    except Exception as e:
        print(f"Error in get_response: {str(e)}")
        return "Sorry, I encountered an error processing your request. Please try again or contact support."

if __name__ == "__main__":
    # This block only runs when the script is run directly
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
        response = get_response(user_input)
        print(response)
        