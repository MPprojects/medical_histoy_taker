from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response, LaunchRequest, SlotConfirmationStatus

# Initialise SkillBuilder
sb = SkillBuilder()
def get_session_attributes(handler_input):
    """Helper function to retrieve session attributes."""
    return handler_input.attributes_manager.session_attributes

# Handling LaunchRequest when the skill is invoked without a specific intent
@sb.request_handler(can_handle_func=lambda handler_input:
                    isinstance(handler_input.request_envelope.request, LaunchRequest))
def launch_request_handler(handler_input: HandlerInput) -> Response:
    # You can customise this opening message
    speak_output = ("Hi there, Thank you for choosing our medical practice. "
                    "We will now ask you some questions to collect your medical history. "
                    "Please answer to the best of your ability. Are you ready?")

    # Return this welcome message as the response
    return handler_input.response_builder.speak(speak_output).ask(speak_output).response

# StartMedicalHistoryIntent: Opening the session
@sb.request_handler(can_handle_func=lambda handler_input:
                    handler_input.request_envelope.request.intent.name == "StartMedicalHistoryIntent")
def start_medical_history_intent(handler_input: HandlerInput) -> Response:
    # Initialise session attributes
    session_attributes = get_session_attributes(handler_input)
    session_attributes['patient_data'] = {}

    # The message you want Alexa to say
    speak_output = ("Alright, let's begin. What is your full name?")

    # Return this message as the response
    return handler_input.response_builder.speak(speak_output).ask(speak_output).response

# ProvideNameIntent: Asking for Full Name with Slot Confirmation
@sb.request_handler(can_handle_func=lambda handler_input:
                    handler_input.request_envelope.request.intent.name == "ProvideNameIntent")
def provide_name_intent(handler_input: HandlerInput) -> Response:
    session_attributes = get_session_attributes(handler_input)
    intent_request = handler_input.request_envelope.request.intent
    name_slot = intent_request.slots.get('name')

    # Check if the name slot has been confirmed
    if name_slot.confirmation_status == SlotConfirmationStatus.CONFIRMED:
        name = name_slot.value
        session_attributes['patient_data']['name'] = name  # Store the confirmed name
        speak_output = f"Thank you, {name}. What is your date of birth?"
    elif name_slot.confirmation_status == SlotConfirmationStatus.DENIED:
        # If the name was denied, ask for the correct name again
        speak_output = "I'm sorry, what is your correct name?"
    else:
        # Prompt for confirmation if the name hasn't been confirmed or denied yet
        speak_output = f"Is your name {name_slot.value}?"

    return handler_input.response_builder.speak(speak_output).ask(speak_output).response

# Add similar updates for other intents to ensure `session_attributes` is used properly.

# Lambda handler
lambda_handler = sb.lambda_handler()
