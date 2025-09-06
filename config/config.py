import os
from dotenv import load_dotenv
from handlers.automated_replies import *
from utils.telegram_helpers import forward_ticket_to_admin

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))  
    DB_USER = os.getenv("DB_USER", "user")
    DB_PASS = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "mydb")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))  
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))  

    BOT_USERNAME = os.getenv("BOT_USERNAME") # retrieve from db
    SUPPORT_ADMIN_USERNAME = 'guncha420' # @guncha420 for testing

    NANO_GPT_API_KEY = os.getenv("NANO_GPT_API_KEY")

    IPROYAL_PROXY_AUTH = os.getenv("IPROYAL_PROXY_AUTH")

    USER_CONVERSATIONS = {
        # AI gathers more info, then forwards to admin
        "cant_find_product_or_drop_or_dead_drop": handle_not_received_drop,

        # Automated response
        "dont_know_how_to_pay": handle_payment_help,
        "restock_request_for_product_or_location": handle_restock_info,
        "is_product_still_available": handle_check_product_availability,
        "what_is_usual_product_arrival_time": handle_product_arrival_time, 

        # "👍"
        "user_says_thanks": handle_thanks,
        "issue_resolved_by_user": handle_thanks,
        "ok": handle_thanks,

        # Forward to admin
        "wrong_drop_info": forward_ticket_to_admin,
        "payment_sent_but_no_drop_or_product_or_location_or_coordinates": forward_ticket_to_admin,
        "less_product_received_than_expected": forward_ticket_to_admin, # Maybe automated response?
        "kladmen_or_packaging_complaint": forward_ticket_to_admin, # Maybe automated response?
        "opinion_or_info_question": forward_ticket_to_admin,
        "can_you_get_me_the_closest_drop_to_x_location": forward_ticket_to_admin,
        "other": forward_ticket_to_admin,
    }

    LANGUAGES = ['lv', 'eng', 'ru', 'ee']

    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE") == "true"