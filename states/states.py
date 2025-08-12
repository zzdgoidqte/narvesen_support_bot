from aiogram.fsm.state import State, StatesGroup

class TicketStates(StatesGroup):
    enter_details = State()