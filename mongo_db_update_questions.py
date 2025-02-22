from pymongo import MongoClient
from bson import ObjectId

# MongoDB Connection
MONGO_URI = "mongodb+srv://maimizuno:ZNDHe1twqS7ir0vT@medicalhistorytaker.3ya8j.mongodb.net/medical_history_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client['medical_history_db']
collection = db['questions']

# Define the updated opening statement
updated_opening = (
    "Thank you for choosing our medical practice. To ensure we have a comprehensive understanding of your medical history, "
    "we ask you some questions. All the information you provide will remain confidential and will only be used for medical purposes. "
    "If you have any concerns or require assistance while completing this questionnaire, our staff will be happy to help you. "
    "These questions will help us register you onto our practice database and assist our healthcare providers in delivering the best possible care. "
    "Please answer each question to the best of your knowledge. Let’s start – are you ready?"
)

# Define the updated questions with `question_id`
updated_questions = [
    {"category": "Personal Information", "questions": [
        {"question": "What’s your Full Name?", "question_id": "q0_0"},
        {"question": "What’s your Date of Birth?", "question_id": "q0_1"},
        {"question": "What’s your Biological Gender?", "question_id": "q0_2"},
        {"question": "What’s your Contact Number?", "question_id": "q0_3"},
        {"question": "What’s your Email Address?", "question_id": "q0_4"},
        {"question": "What’s your Home Address?", "question_id": "q0_5"}
    ]},
    {"category": "Emergency Contact", "questions": [
        {"question": "What Name can we use for your Emergency Contact?", "question_id": "q1_0"},
        {"question": "Their Relationship to you?", "question_id": "q1_1"},
        {"question": "Their Contact Number?", "question_id": "q1_2"}
    ]},
    {"category": "Medical History", "questions": [
        {"question": "Do you have any existing medical conditions?", "question_id": "q2_0", "follow_up": "OK, what are those?"},
        {"question": "Have you undergone any surgeries in the past?", "question_id": "q2_1", "follow_up": "OK, what was it for?"},
        {"question": "Are you currently taking any medications or supplements?", "question_id": "q2_2", "follow_up": "OK, what do you take?"},
        {"question": "Do you have any known allergies?", "question_id": "q2_3", "follow_up": [
            {"question": "OK. What’s the allergy?", "question_id": "q2_3_0"},
            {"question": "And, what sort of reaction do you have?", "question_id": "q2_3_1"}
        ]}
    ]},
    {"category": "Family Medical History", "questions": [
        {"question": "Are there any significant medical conditions that run in your immediate family? Things like heart disease, diabetes, cancer?", "question_id": "q3_0", "follow_up": "OK. What are they?"},
        {"question": "Are there any hereditary conditions or genetic disorders in your family?", "question_id": "q3_1", "follow_up": "OK. What are they?"}
    ]},
    {"category": "Lifestyle and Habits", "questions": [
        {"question": "Do you smoke?", "question_id": "q4_0", "follow_up": "OK, how many cigarettes do you smoke each day?"},
        {"question": "Do you consume alcohol?", "question_id": "q4_1", "follow_up": "OK, how frequently and how much each time?"},
        {"question": "Do you engage in regular exercise?", "question_id": "q4_2", "follow_up": "That’s good, what sort of exercise?"}
    ]},
    {"category": "Social History", "questions": [
        {"question": "What’s your work, your Occupation?", "question_id": "q5_0"},
        {"question": "Are you married or with a partner?", "question_id": "q5_1"},
        {"question": "Do you have children?", "question_id": "q5_2"}
    ]},
    {"category": "Immunization History", "questions": [
        {"question": "Are your immunizations up to date?", "question_id": "q6_0", "follow_up": [
            {"question": "Good, what have you got?", "question_id": "q6_0_0"},
            {"question": "When was the last time?", "question_id": "q6_0_1"}
        ]}
    ]},
    {"category": "Previous Medical Records", "questions": [
        {"question": "And finally, do you have any previous medical records or test results that you would like to share with us?", "question_id": "q7_0", "follow_up": [
            {"question": "OK, let’s get those to the receptionist.", "question_id": "q7_0_0"}
        ]}
    ]}
]

# Define the updated closing statement
closing_statement = "OK, all done. Thank you for providing all the information. This has been good to talk to you. We look forward to providing you with excellent healthcare."

# Prepare the updated document
updated_document = {
    "opening": updated_opening,
    "sections": updated_questions,
    "closing": closing_statement  # Store the closing statement separately
}

# Update the document in MongoDB
result = collection.update_one({}, {"$set": updated_document})

if result.modified_count > 0:
    print("Database updated successfully!")
else:
    print("No updates were made. Either the document was already correct or there was an issue.")
