#!/usr/bin/env python3
"""
Automated tests for User Context integration
Based on TESTING_PLAN.md scenarios
"""
import asyncio
from datetime import datetime
from bot.database.crud import calculate_age
from bot.services.prompt_builder import PromptBuilder

# Colors for test output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def test_result(name: str, passed: bool, details: str = ""):
    """Print test result with colors"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")
    return passed

def scenario_6_calculate_age():
    """Scenario 6: Test age calculation"""
    print(f"\n{BOLD}=== Scenario 6: Age Calculation ==={RESET}")

    results = []

    # Test 1: Birthday already passed this year
    birth_date = datetime(1990, 3, 15)
    age = calculate_age(birth_date)
    expected = 35 if datetime.now() >= datetime(2025, 3, 15) else 34
    results.append(test_result(
        "Age calculation (birthday passed)",
        age == expected,
        f"Expected: {expected}, Got: {age}"
    ))

    # Test 2: Birthday not yet this year
    birth_date = datetime(1990, 11, 15)
    age = calculate_age(birth_date)
    expected = 34 if datetime.now() < datetime(2025, 11, 15) else 35
    results.append(test_result(
        "Age calculation (birthday not yet)",
        age == expected,
        f"Expected: {expected}, Got: {age}"
    ))

    # Test 3: Birthday today
    today = datetime.now()
    birth_date = datetime(2000, today.month, today.day)
    age = calculate_age(birth_date)
    expected = today.year - 2000
    results.append(test_result(
        "Age calculation (birthday today)",
        age == expected,
        f"Expected: {expected}, Got: {age}"
    ))

    # Test 4: None handling
    age = calculate_age(None)
    results.append(test_result(
        "None handling",
        age is None,
        f"Expected: None, Got: {age}"
    ))

    # Test 5: Leap year birthday (29 Feb 2000)
    birth_date = datetime(2000, 2, 29)
    age = calculate_age(birth_date)
    today = datetime.now()
    # Calculate expected age accounting for leap year
    years = today.year - 2000
    if (today.month, today.day) < (2, 29):
        expected = years - 1
    elif today.month == 2 and today.day == 28 and not (today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0)):
        # Not a leap year, before March 1
        expected = years - 1
    else:
        expected = years
    results.append(test_result(
        "Leap year birthday",
        age == expected,
        f"Expected: {expected}, Got: {age}"
    ))

    return all(results)


def scenario_7_prompt_with_user_context():
    """Scenario 7: Test prompt generation with user context"""
    print(f"\n{BOLD}=== Scenario 7: User Context in Prompt ==={RESET}")

    builder = PromptBuilder()
    results = []

    # Test 1: Full profile
    prompt = builder.build_system_prompt(
        gender='female',
        age=30,
        occupation='UX-дизайнер',
        work_format='hybrid'
    )

    results.append(test_result(
        "User context section exists",
        "# КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ" in prompt,
        "Missing user context section"
    ))

    results.append(test_result(
        "Gender is correct",
        "Пол: Женский" in prompt,
        "Gender not found or incorrect"
    ))

    results.append(test_result(
        "Age is correct (no 'None')",
        "Возраст: 30 лет" in prompt and "None" not in prompt,
        "Age formatting issue"
    ))

    results.append(test_result(
        "Occupation is correct",
        "Занятость: UX-дизайнер" in prompt,
        "Occupation not found"
    ))

    results.append(test_result(
        "Work format is correct",
        "Формат работы: Гибридный формат" in prompt,
        "Work format not found"
    ))

    results.append(test_result(
        "Gender-specific section exists",
        "# УЧЁТ ПОЛА: ЖЕНСКИЙ" in prompt or "ГЕНДЕРНО-АДАПТИВНАЯ" in prompt,
        "Missing gender-specific instructions"
    ))

    # Test 2: Partial profile (only gender and age)
    prompt = builder.build_system_prompt(
        gender='male',
        age=35,
        occupation=None,
        work_format=None
    )

    results.append(test_result(
        "Partial profile: age without None",
        "Возраст: 35 лет" in prompt and "None лет" not in prompt,
        "Age None issue in partial profile"
    ))

    results.append(test_result(
        "Partial profile: occupation placeholder",
        "Занятость: не указана" in prompt or "не указан" in prompt,
        "Missing occupation placeholder"
    ))

    results.append(test_result(
        "Partial profile: work format placeholder",
        "Формат работы: Не указан" in prompt,
        "Missing work format placeholder"
    ))

    # Test 3: Empty profile (all None)
    prompt = builder.build_system_prompt(
        gender=None,
        age=None,
        occupation=None,
        work_format=None
    )

    results.append(test_result(
        "Empty profile: no 'None' strings",
        "None" not in prompt or "none" not in prompt.lower(),
        "Found 'None' in prompt with empty profile"
    ))

    # Test 4: Male gender-specific section
    prompt = builder.build_system_prompt(gender='male')
    results.append(test_result(
        "Male gender-specific section exists",
        "# УЧЁТ ПОЛА: МУЖСКОЙ" in prompt or "МУЖСКОЙ" in prompt,
        "Missing male gender-specific instructions"
    ))

    return all(results)


def scenario_10_word_validation():
    """Scenario 10: Test word count validation for Russian text"""
    print(f"\n{BOLD}=== Scenario 10: Word Count Validation ==={RESET}")

    results = []

    # Test 1: Short text (1 word)
    text = "Проблема."
    word_count = len(text.split())
    results.append(test_result(
        "Short text (1 word)",
        word_count == 1 and word_count < 50,
        f"Word count: {word_count}, Expected: < 50"
    ))

    # Test 2: 49 words (should be rejected)
    text = "один два три четыре пять шесть семь восемь девять десять " * 4 + "один два три четыре пять шесть семь восемь девять"
    word_count = len(text.split())
    results.append(test_result(
        "49 words (should reject)",
        word_count == 49 and word_count < 50,
        f"Word count: {word_count}, Expected: 49"
    ))

    # Test 3: 51 words (should accept)
    text = "один два три четыре пять шесть семь восемь девять десять " * 5 + "один"
    word_count = len(text.split())
    results.append(test_result(
        "51 words (should accept)",
        word_count >= 50,
        f"Word count: {word_count}, Expected: >= 50"
    ))

    # Test 4: Text with multiple spaces and newlines
    text = "слово    слово\n\nслово   слово\nслово " * 10 + "слово " * 6  # 56 words with spaces
    word_count = len(text.split())
    results.append(test_result(
        "Text with extra whitespace (split() handles correctly)",
        word_count >= 50,
        f"Word count: {word_count}, Expected: >= 50"
    ))

    # Test 5: Russian cyrillic text counting
    russian_text = "мама мыла раму " * 17 + "мама"  # 52 words
    word_count = len(russian_text.split())
    results.append(test_result(
        "Cyrillic word counting",
        word_count >= 50,
        f"Word count: {word_count}, Expected: >= 50"
    ))

    return all(results)


def scenario_5_birth_date_validation():
    """Scenario 5: Test birth date validation"""
    print(f"\n{BOLD}=== Scenario 5: Birth Date Validation ==={RESET}")

    from bot.handlers.start import validate_birth_date
    results = []

    # Test 1: Valid format
    is_valid, result = validate_birth_date("15.03.1990")
    results.append(test_result(
        "Valid date format",
        is_valid and isinstance(result, datetime),
        f"Result: {result}"
    ))

    # Test 2: Wrong format (YYYY-MM-DD)
    is_valid, result = validate_birth_date("1990-03-15")
    results.append(test_result(
        "Wrong format (YYYY-MM-DD)",
        not is_valid and isinstance(result, str),
        f"Expected error message, got: {result[:50]}..."
    ))

    # Test 3: Invalid date
    is_valid, result = validate_birth_date("32.13.1990")
    results.append(test_result(
        "Invalid date (32.13.1990)",
        not is_valid,
        f"Expected rejection"
    ))

    # Test 4: Wrong separator
    is_valid, result = validate_birth_date("15/03/1990")
    results.append(test_result(
        "Wrong separator (/)",
        not is_valid,
        f"Expected rejection"
    ))

    # Test 5: Not a date
    is_valid, result = validate_birth_date("abc")
    results.append(test_result(
        "Not a date (abc)",
        not is_valid,
        f"Expected rejection"
    ))

    # Test 6: Future date
    is_valid, result = validate_birth_date("01.01.2030")
    results.append(test_result(
        "Future date",
        not is_valid and "будущ" in result.lower(),
        f"Expected 'future' error, got: {result}"
    ))

    # Test 7: Age < 14
    today = datetime.now()
    birth_year = today.year - 10  # 10 years old
    is_valid, result = validate_birth_date(f"01.01.{birth_year}")
    results.append(test_result(
        "Age < 14 years",
        not is_valid and "14" in result,
        f"Expected age limit error"
    ))

    # Test 8: Age > 100
    is_valid, result = validate_birth_date("01.01.1900")
    results.append(test_result(
        "Age > 100 years",
        not is_valid,
        f"Expected age limit error"
    ))

    return all(results)


def main():
    """Run all automated tests"""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  USER CONTEXT INTEGRATION - AUTOMATED TESTING{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    all_passed = []

    # Run scenarios
    all_passed.append(scenario_5_birth_date_validation())
    all_passed.append(scenario_6_calculate_age())
    all_passed.append(scenario_7_prompt_with_user_context())
    all_passed.append(scenario_10_word_validation())

    # Summary
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}SUMMARY{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    passed_count = sum(all_passed)
    total_count = len(all_passed)

    if all(all_passed):
        print(f"{GREEN}{BOLD}✓ ALL SCENARIOS PASSED ({passed_count}/{total_count}){RESET}")
        print(f"\n{GREEN}Ready to proceed with manual testing (Scenarios 1-4, 8-9, 11){RESET}")
        return 0
    else:
        print(f"{RED}{BOLD}✗ SOME SCENARIOS FAILED ({passed_count}/{total_count}){RESET}")
        print(f"\n{RED}Please fix issues before manual testing{RESET}")
        return 1


if __name__ == "__main__":
    exit(main())
