from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response, LaunchRequest, IntentRequest, SlotConfirmationStatus
import pymongo
import os
import logging
from datetime import datetime
import google.generativeai as genai
import re  # Added import for regex validation

# Configure logging for debugging and tracking errors
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# MongoDB connection setup 
MONGO_URI = os.getenv("MONGO_URI")  # Retrieve MongoDB connection string from environment variables
if not MONGO_URI:
    raise ValueError("MongoDB connection string is missing. Set MONGO_URI in Lambda environment variables.")

def get_db():
    """Returns a single MongoDB connection to be reused across functions"""
    if not hasattr(get_db, "client"):
        get_db.client = pymongo.MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False) # Connect to MongoDB
    return get_db.client['medical_history_db'] # Return the database

db = get_db()
collection = db['questions']

# Set up Gemini API Key
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
if not GENAI_API_KEY:
    raise ValueError("API Key is missing. Please ensure the GENAI_API_KEY environment variable is set.")

# Configure Gemini API with the retrieved API key
genai.configure(api_key=GENAI_API_KEY)

def get_gemini_response(user_answer, question):
    """
    Sends user input and the previous question to Gemini for a dynamic follow-up response.
    Returns the AI-generated follow-up question.
    """
    
    # Define the model to use
    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
    
    # Define the prompt for generating a follow-up question
    prompt = f"Patient was asked: '{question}'\nPatient responded: '{user_answer}'\nWhat is the best follow-up question to ask next? Return only the follow-up question."

    try:
        response = model.generate_content(prompt)

        # Extract AI-generated response
        if hasattr(response, 'text') and response.text:
            return response.text.strip()

        return None  # If no text, return None (fallback to predefined questions)

    except Exception as e:
        logger.error(f"Error calling Gemini: {str(e)}")
        return None  # If Gemini API fails, use fallback

# Initialise SkillBuilder (Manages Alexa skill handlers)
sb = SkillBuilder()

# Error message when data retrieval fails
retrieve_error_mg = "Sorry, I couldn't retrieve the questions. Please try again later."

# Retrieve questions from MongoDB
def get_questions():
    """Fetches all questions from MongoDB"""
    try:
        questions_doc = collection.find_one()  # Fetch the first document in the 'questions' collection
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
    """Fetches the next question from the MongoDB document"""
    if questions and "sections" in questions:
        sections = questions['sections']
        if section_index < len(sections):
            current_section = sections[section_index]
            if question_index < len(current_section['questions']):
                return current_section['questions'][question_index]  # Returns full question object
    return None  # No more questions in this section

# Generates auto-incrementing IDs for patients and sessions
def get_next_sequence(name):
    """Auto-increments the session_id or patient_id in the 'counters' collection"""
    counters_collection = db["counters"]
    counter = counters_collection.find_one_and_update(
        {"_id": name}, 
        {"$inc": {"seq": 1}}, 
        upsert=True,  
        return_document=pymongo.ReturnDocument.AFTER  
    )
    return counter["seq"]

# Retrieve session attributes
def get_session_attributes(handler_input):
    """Returns the current session attributes"""
    return handler_input.attributes_manager.session_attributes

# Store patient data into MongoDB
def save_patient_data(session_attributes):
    """Saves collected patient responses to the database"""
    patient_collection = db['patients']
    responses = [
        {"question_id": question_id, "response": answer, "time": datetime.utcnow()}
        for question_id, answer in session_attributes.get('patient_data', {}).items()
    ]
    
    if responses:  # Only save if there are responses
        patient_record = {
            "session_id": session_attributes.get("session_id"),
            "patient_id": session_attributes.get("patient_id"),
            "session_info": {
                "session_start": session_attributes.get("session_start"),
                "session_end": datetime.utcnow()
            },
            "response": responses
        }
        patient_collection.insert_one(patient_record)
        logger.info(f"Patient data saved: {patient_record}")
    else:
        logger.warning("No patient responses recorded, skipping database save.")

# Handles session end
class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput):
        return handler_input.request_envelope.request.object_type == "SessionEndedRequest"

    def handle(self, handler_input: HandlerInput) -> Response:
        logger.info("Session ended.")
        return handler_input.response_builder.response  

sb.add_request_handler(SessionEndedRequestHandler())

# LaunchRequest handler
@sb.request_handler(can_handle_func=lambda handler_input:
                    isinstance(handler_input.request_envelope.request, LaunchRequest))
def launch_request_handler(handler_input: HandlerInput) -> Response:
    """Handles the launch of the Alexa skill and starts asking questions"""
    questions = get_questions()
    session_attributes = get_session_attributes(handler_input)

    if questions:
        session_attributes.update({
            'current_section': 0,
            'current_question': 0,
            'session_start': datetime.utcnow(),
            'session_id': get_next_sequence("session_id"),
            'patient_id': get_next_sequence("patient_id")
        })
        speak_output = questions['opening']
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

def validate_answer_with_gemini(question, response):
    """
    Uses Gemini AI to determine if the response correctly answers the question.
    If invalid, Gemini will suggest a clearer way to re-ask the question.
    Returns:
      - (True, None) if valid
      - (False, reworded_question) if invalid
    """
    prompt = f"""
    Question: {question}
    Patient Response: {response}
    
    - Does the patient's response correctly answer the question? Answer 'VALID' or 'INVALID'.
    - If INVALID, rephrase the question in a **simpler and clearer** way for better understanding.
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
        result = model.generate_content(prompt)
        validation_result = result.text.strip().split("\n")

        if "VALID" in validation_result[0]:
            return True, None  # Answer is correct
        elif "INVALID" in validation_result[0]:
            reworded_question = validation_result[1] if len(validation_result) > 1 else question
            return False, reworded_question  # Answer is incorrect, use Gemini’s reworded question

    except Exception as e:
        logger.error(f"Error validating response with Gemini: {str(e)}")
        return True, None  # Assume valid if Gemini API fails


# CaptureAnswerIntent handler (Processes user responses and asks follow-ups)
@sb.request_handler(can_handle_func=lambda handler_input:
                    isinstance(handler_input.request_envelope.request, IntentRequest) and 
                    handler_input.request_envelope.request.intent.name == "CaptureAnswerIntent")
def capture_answer_intent(handler_input: HandlerInput) -> Response:
    """Handles user responses, stores answers, and moves to the next question"""
    session_attributes = get_session_attributes(handler_input)
    current_section = session_attributes.get('current_section', 0)
    current_question = session_attributes.get('current_question', 0)

    questions = get_questions()
    current_question_data = get_next_question(questions, current_section, current_question)
    
    if not current_question_data:
        closing_statement = questions.get("closing", "Thank you for providing all the information.")
        return handler_input.response_builder.speak(closing_statement).response

    current_question_id = current_question_data["question_id"]
    current_question_text = current_question_data["question"]

    intent_request = handler_input.request_envelope.request.intent
    slot = intent_request.slots.get("response")  # Only one dynamic slot

    if not slot or not slot.value:
        # No response given, rephrase the question
        speak_output = f"I didn't hear your response. {current_question_text}"
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response

    slot_value = slot.value

    # Validate answer using Gemini
    is_valid, reworded_question = validate_answer_with_gemini(current_question_text, slot_value)

    if not is_valid:
        # If answer is incorrect, ask the reworded question from Gemini
        speak_output = f"Hmm, I didn’t quite get that. {reworded_question}"
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response

    # Store response in session attributes
    session_attributes.setdefault('patient_data', {})[current_question_id] = slot_value  
    logger.info(f"Stored response: {current_question_id} -> {slot_value}")

    # Move to next question safely
    next_question = get_next_question(questions, current_section, current_question + 1)
    if next_question:
        session_attributes['current_question'] += 1
        speak_output = next_question["question"]
    else:
        session_attributes['current_section'] += 1
        session_attributes['current_question'] = 0
        next_question = get_next_question(questions, session_attributes['current_section'], 0)
        if next_question:
            speak_output = f"Let's move to the next section. {next_question['question']}"
        else:
            speak_output = questions.get("closing", "Thank you for providing all the information.")
            save_patient_data(session_attributes)

    return handler_input.response_builder.speak(speak_output).ask(speak_output).response


# Lambda handler for deployment
lambda_handler = sb.lambda_handler()
