from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):
    name = State()
    age = State()
    gender = State()
    looking_for = State()
    city = State()
    bio = State()
    photos = State()


class SearchState(StatesGroup):
    searching = State()


class ProfileState(StatesGroup):
    editing = State()


class AdminState(StatesGroup):
    broadcast = State()
    ban_user = State()
    unban_user = State()
