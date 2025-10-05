"""FSM states for problem solving flow"""
from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """States for user onboarding flow"""
    choosing_gender = State()  # Selecting gender during onboarding
    entering_birth_date = State()  # Entering date of birth (DD.MM.YYYY)
    entering_occupation = State()  # Entering occupation/job
    choosing_work_format = State()  # Choosing work format (remote/office/hybrid/student)


class ProfileEditStates(StatesGroup):
    """States for editing profile fields"""
    editing_gender = State()
    editing_birth_date = State()
    editing_occupation = State()
    editing_work_format = State()


class ProblemSolvingStates(StatesGroup):
    """States for problem analysis flow"""
    waiting_for_problem = State()  # Waiting for problem description
    analyzing_problem = State()     # Claude is analyzing problem type
    asking_questions = State()      # Interactive Q&A based on methodology
    generating_solution = State()   # Generating final solution
    discussing_solution = State()   # Additional discussion after solution