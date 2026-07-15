from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):

    name = State()

    age = State()

    gender = State()

    looking = State()

    city = State()

    bio = State()

    photo1 = State()

    photo2 = State()

    photo3 = State()

    photo4 = State()

    photo5 = State()

    finish = State()


class EditProfileState(StatesGroup):

    name = State()

    age = State()

    city = State()

    bio = State()

    photos = State()


class SearchState(StatesGroup):

    search = State()

    profile = State()

    like = State()

    match = State()


class ChatState(StatesGroup):

    chatting = State()


class PremiumState(StatesGroup):

    choose = State()

    payment = State()

    confirm = State()


class ReportState(StatesGroup):

    reason = State()


class AdminState(StatesGroup):

    panel = State()

    broadcast = State()

    ban = State()

    unban = State()

    statistics = State()
