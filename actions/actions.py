from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, UserUtteranceReverted
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
import re
from datetime import datetime

class ValidateReservationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_reservation_form"

    def validate_phone_number(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        """Validate phone number."""
        pattern = r"^\+?\d{10,15}$"
        if re.match(pattern, slot_value):
            return {"phone_number": slot_value}
        else:
            dispatcher.utter_message(text="The phone number seems invalid. Please enter a valid phone number.")
            return {"phone_number": None}

    def validate_reservation_date(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        """Validate reservation date."""
        try:
            reservation_date = datetime.strptime(slot_value, "%Y-%m-%d")
            if reservation_date >= datetime.now():
                return {"reservation_date": slot_value}
            else:
                dispatcher.utter_message(text="The reservation date must be in the future.")
                return {"reservation_date": None}
        except ValueError:
            dispatcher.utter_message(text="Please enter the date in YYYY-MM-DD format.")
            return {"reservation_date": None}

    def validate(self, slot_values: Dict[Text, Any], dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        if tracker.latest_message.get('intent').get('name') == 'ask_question':
            dispatcher.utter_message(text="Let's address your question first.")
            return self.handle_interruption(tracker)
        return slot_values

    def handle_interruption(self, tracker: Tracker) -> Dict[Text, Any]:
        """Store the current state of the form and return it."""
        return {"active_loop": "reservation_form"}

class ActionSubmitReservation(Action):
    def name(self) -> str:
        return "action_submit_reservation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Confirm the reservation
        name = tracker.get_slot('name')
        phone_number = tracker.get_slot('phone_number')
        reservation_date = tracker.get_slot('reservation_date')
        number_of_guests = tracker.get_slot('number_of_guests')

        dispatcher.utter_message(text="Your reservation is confirmed! We look forward to serving you.")

        # Clear the slots or reset the active loop
        return [
            SlotSet("name", None),
            SlotSet("phone_number", None),
            SlotSet("reservation_date", None),
            SlotSet("number_of_guests", None)
        ]

class ActionHandleQuestion(Action):
    def name(self) -> str:
        return "action_handle_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get('text')
        # Answering the user's question
        if "how long" in user_message.lower():
            dispatcher.utter_message(text="You should receive a confirmation within a few minutes.")
        elif "cancellation" in user_message.lower():
            dispatcher.utter_message(text="You can cancel your reservation by contacting us directly.")
        else:
            dispatcher.utter_message(text="That's a great question! I'll do my best to help.")

        # Resume the form after answering
        return [UserUtteranceReverted()]  # Resuming the previous form state
