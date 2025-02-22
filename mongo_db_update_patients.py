from pymongo import MongoClient
from datetime import datetime
import os

# MongoDB Connection
MONGO_URI = "mongodb+srv://maimizuno:ZNDHe1twqS7ir0vT@medicalhistorytaker.3ya8j.mongodb.net/medical_history_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client['medical_history_db']
patient_collection = db['patients']

# Example Patient Data - Mary Smith
example_patient_data = {
    "session_id": 1001,  # Example session ID
    "patient_id": 2001,  # Example patient ID
    "session_info": {
        "session_start": datetime.utcnow(),
        "session_end": datetime.utcnow()
    },
    "response": [
        # Personal Information
        {"question_id": "q0_0", "response": "Mary Smith", "time": datetime.utcnow()},
        {"question_id": "q0_1", "response": "1985-04-23", "time": datetime.utcnow()},
        {"question_id": "q0_2", "response": "Female", "time": datetime.utcnow()},
        {"question_id": "q0_3", "response": "+61412345678", "time": datetime.utcnow()},
        {"question_id": "q0_4", "response": "mary.smith@example.com", "time": datetime.utcnow()},
        {"question_id": "q0_5", "response": "123 Example Street, Melbourne", "time": datetime.utcnow()},

        # Emergency Contact
        {"question_id": "q1_0", "response": "John Smith", "time": datetime.utcnow()},
        {"question_id": "q1_1", "response": "Husband", "time": datetime.utcnow()},
        {"question_id": "q1_2", "response": "+61498765432", "time": datetime.utcnow()},

        # Medical History
        {"question_id": "q2_0", "response": "Yes", "time": datetime.utcnow()},
        {"question_id": "q2_0_0", "response": "Hypertension", "time": datetime.utcnow()},
        {"question_id": "q2_1", "response": "No", "time": datetime.utcnow()},
        {"question_id": "q2_2", "response": "Yes", "time": datetime.utcnow()},
        {"question_id": "q2_2_0", "response": "Vitamin D, Iron Supplements", "time": datetime.utcnow()},
        {"question_id": "q2_3", "response": "No", "time": datetime.utcnow()},

        # Family Medical History
        {"question_id": "q3_0", "response": "Yes", "time": datetime.utcnow()},
        {"question_id": "q3_0_0", "response": "Heart Disease", "time": datetime.utcnow()},
        {"question_id": "q3_1", "response": "No", "time": datetime.utcnow()},

        # Lifestyle and Habits
        {"question_id": "q4_0", "response": "No", "time": datetime.utcnow()},
        {"question_id": "q4_1", "response": "Yes", "time": datetime.utcnow()},
        {"question_id": "q4_1_0", "response": "2 glasses of wine per week", "time": datetime.utcnow()},
        {"question_id": "q4_2", "response": "Yes", "time": datetime.utcnow()},
        {"question_id": "q4_2_0", "response": "Jogging, Yoga", "time": datetime.utcnow()},

        # Social History
        {"question_id": "q5_0", "response": "Software Engineer", "time": datetime.utcnow()},
        {"question_id": "q5_1", "response": "Married", "time": datetime.utcnow()},
        {"question_id": "q5_2", "response": "Yes", "time": datetime.utcnow()},

        # Immunization History
        {"question_id": "q6_0", "response": "Yes", "time": datetime.utcnow()},
        {"question_id": "q6_0_0", "response": "COVID-19, Flu, Hepatitis B", "time": datetime.utcnow()},
        {"question_id": "q6_0_1", "response": "Last flu shot in 2023", "time": datetime.utcnow()},

        # Previous Medical Records
        {"question_id": "q7_0", "response": "Yes", "time": datetime.utcnow()},
        {"question_id": "q7_0_0", "response": "Providing records to receptionist", "time": datetime.utcnow()}
    ],
    "closing": "OK, all done. This has been good to meet you. Thank you. We look forward to providing you with excellent healthcare."
}

# Insert the patient data into MongoDB
insert_result = patient_collection.insert_one(example_patient_data)
print(f"Inserted patient record with ID: {insert_result.inserted_id}")
