from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response, LaunchRequest, IntentRequest, SlotConfirmationStatus
import pymongo
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# MongoDB connection setup
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    MONGO_URI = "mongodb+srv://maimizuno:ZNDHe1twqS7ir0vT@medicalhistorytaker.3ya8j.mongodb.net/medical_history_db?retryWrites=true&w=majority"

client = pymongo.MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client['medical_history_db']
collection = db['questions']

# Initialise SkillBuilder
sb = SkillBuilder()

# Error message to indicate that there is a problem with data retrieval
retrieve_error_mg = "Sorry, I couldn't retrieve the questions. Please try again later."

# Retrieve questions from MongoDB with logging
def get_questions():
    try:
        questions_doc = collection.find_one()  # Get the first document
        if questions_doc is None:
            logger.info("No document found in 'questions' collection.")
            return None
        logger.info(f"Retrieved questions: {questions_doc}")
        return questions_doc
    except Exception as e:
        logger.error(f"Error retrieving questions from MongoDB: {str(e)}")
        return None

# Retrieve the next question based on the current section and question index
def get_next_question(questions, section_index, question_index):
    if questions and "sections" in questions:
        sections = questions['sections']
        if section_index < len(sections):
            current_section = sections[section_index]
            if question_index < len(current_section['questions']):
                return current_section['questions'][question_index]['question']
            else:
                return None  # No more questions in this section
    return None

# Function to retrieve session attributes
def get_session_attributes(handler_input):
    return handler_input.attributes_manager.session_attributes

# Function to store patient data into MongoDB
def save_patient_data(session_attributes):
    patient_collection = db['patients']  # Use a different collection for storing patient responses
    patient_collection.insert_one(session_attributes)

# Handler for SessionEndedRequest
class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput):
        return handler_input.request_envelope.request.object_type == "SessionEndedRequest"

    def handle(self, handler_input: HandlerInput) -> Response:
        # Log the session end or handle cleanup here
        logger.info("Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response  # No response required

# Add this handler to the skill builder
sb.add_request_handler(SessionEndedRequestHandler())    

# LaunchRequest handler
@sb.request_handler(can_handle_func=lambda handler_input:
                    isinstance(handler_input.request_envelope.request, LaunchRequest))
def launch_request_handler(handler_input: HandlerInput) -> Response:
    questions = get_questions()
    if questions:
        opening_statement = questions['opening']
        session_attributes = get_session_attributes(handler_input)
        session_attributes['current_section'] = 0  # Initialise to the first section
        session_attributes['current_question'] = 0  # Initialise to the first question
        speak_output = opening_statement
    else:
        speak_output = retrieve_error_mg
    return handler_input.response_builder.speak(speak_output).ask(speak_output).response

# StartMedicalHistoryIntent handler (Handles the "are you ready" confirmation and asks the first question)
@sb.request_handler(can_handle_func=lambda handler_input:
                    isinstance(handler_input.request_envelope.request, IntentRequest) and 
                    handler_input.request_envelope.request.intent.name == "StartMedicalHistoryIntent")
def start_medical_history_intent(handler_input: HandlerInput) -> Response:
    session_attributes = get_session_attributes(handler_input)

    # Get questions from the database
    questions = get_questions()

    # Ensure patient_data is initialised
    if 'patient_data' not in session_attributes:
        session_attributes['patient_data'] = {}

    # Initialise current_section and current_question if not present
    session_attributes['current_section'] = 0
    session_attributes['current_question'] = 0

    # Get the first question from the database
    next_question = get_next_question(questions, session_attributes['current_section'], session_attributes['current_question'])

    if next_question:
        speak_output = f"Great! Let me start by asking your personal information. {next_question}"
        session_attributes['current_question'] += 1  # Increment to the next question
    else:
        speak_output = retrieve_error_mg
    
    return handler_input.response_builder.speak(speak_output).ask(speak_output).response
    

# CaptureAnswerIntent: Dynamically handle questions and slot confirmation
@sb.request_handler(can_handle_func=lambda handler_input:
                    isinstance(handler_input.request_envelope.request, IntentRequest) and 
                    handler_input.request_envelope.request.intent.name == "CaptureAnswerIntent")
def capture_answer_intent(handler_input: HandlerInput) -> Response:
    session_attributes = get_session_attributes(handler_input)
    
    # Retrieve the current section and question
    current_section = session_attributes.get('current_section', 0)
    current_question = session_attributes.get('current_question', 0)
    
    # Get questions from the database
    questions = get_questions()
    current_question_text = get_next_question(questions, current_section, current_question)  # Use current question index

    # Dynamically handle slot confirmation
    if current_question_text:
        intent_request = handler_input.request_envelope.request.intent
        
        # Handle each slot based on the current question
        slot_name, slot_value = None, None
        
        if "Full Name" in current_question_text:
            slot_name = 'name'
        elif "Date of Birth" in current_question_text:
            slot_name = 'date_of_birth'
        elif "Gender" in current_question_text:
            slot_name = 'gender'
        elif "Contact Number" in current_question_text:
            slot_name = 'contact_number'
        elif "Email Address" in current_question_text:
            slot_name = 'email_address'
        elif "Home Address" in current_question_text:
            slot_name = 'home_address'
        
        if slot_name:
            slot = intent_request.slots.get(slot_name)
            # Log the slot value and confirmation status for debugging
            logger.info(f"Slot Name: {slot_name}, Slot Value: {slot.value}, Confirmation Status: {slot.confirmation_status}")
        
            # Slot Confirmation Logic
            if slot and slot.confirmation_status == SlotConfirmationStatus.CONFIRMED:
                slot_value = slot.value
                # Use .get() to preserve existing data and update only the current slot value
                patient_data = session_attributes.get('patient_data', {})
                patient_data[slot_name] = slot_value
                session_attributes['patient_data'] = patient_data  # Update the session attribute
                
                # Save the data to the database
                save_patient_data(session_attributes)  # Save the entire session data including patient data
                logger.info(f"Patient Data Saved: {patient_data}")  # Log to verify saving
                
                speak_output = f"Thank you. Your {slot_name} has been saved."
                session_attributes['current_question'] += 1  # Move to the next question

                # Get the next question
                next_question = get_next_question(questions, current_section, session_attributes['current_question'])
                if next_question:
                    speak_output += f"<break time='1s'/> Here is your next question: {next_question}"
                else:
                    session_attributes['current_section'] += 1
                    session_attributes['current_question'] = 0
                    next_question = get_next_question(questions, session_attributes['current_section'], 0)
                    if next_question:
                        speak_output += f"<break time='1s'/> Let's move to the next section. {next_question}"
                    else:
                        speak_output += "Thank you for providing all the information."
                        save_patient_data(session_attributes)  # Save the collected data
            elif slot and slot.confirmation_status == SlotConfirmationStatus.DENIED:
                speak_output = f"I'm sorry, could you please repeat your {slot_name}?"
            else:
                speak_output = f"Is your {slot_name} {slot.value}?"
                
        else:
            speak_output = "Sorry, I couldn't understand that. Could you please repeat?"

    return handler_input.response_builder.speak(speak_output).ask(speak_output).response


# Error handler (Catch-all handler)
@sb.request_handler(can_handle_func=lambda handler_input: True)
def fallback_handler(handler_input: HandlerInput) -> Response:
    speak_output = "Sorry, I didn't understand that. Could you repeat?"
    return handler_input.response_builder.speak(speak_output).ask(speak_output).response

# Lambda handler
lambda_handler = sb.lambda_handler()
