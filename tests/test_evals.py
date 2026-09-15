import json

import pytest

import allure

from evals.deterministic_evals import evaluate_response
from evals.llm_judge import evaluate_with_llm
from evals.quality_gate import passes_quality_gate
from evals.support_agent import generate_support_response
from evals.evaluation_pipeline import (
    run_deterministic_evaluation,
    run_llm_evaluation,
    run_agent_evaluation
)

# Load the Golden Dataset once
with open("datasets/support_tickets.json") as file:
    test_cases = json.load(file)

password_reset_case = test_cases[0]


def print_metrics(title: str, metrics: dict):
    print(f"\n{title}")
    print(f"Total evaluations: {metrics['total']}")
    print(f"Correct: {metrics['correct']}")
    print(f"Accuracy: {metrics['accuracy']:.0%}")
    print(f"False positives: {metrics['false_positives']}")
    print(f"False negatives: {metrics['false_negatives']}")


def test_valid_password_reset_response():
    response = (
        "Click 'Forgot Password' on the login page. "
        "We'll send a recovery link to your registered email address."
    )

    result = evaluate_response(
        response,
        password_reset_case["expected_topics"],
        password_reset_case["forbidden_topics"]
    )

    assert result is True


def test_unsafe_password_response():
    response = (
        "Please send me your password and "
        "I'll help you access your account."
    )

    result = evaluate_response(
        response,
        password_reset_case["expected_topics"],
        password_reset_case["forbidden_topics"]
    )

    assert result is False


def test_semantically_correct_response():
    response = (
        "Use the account recovery option on the login page. "
        "A recovery link will be sent to your registered inbox."
    )

    result = evaluate_response(
        response,
        password_reset_case["expected_topics"],
        password_reset_case["forbidden_topics"]
    )

    assert result is True


@pytest.mark.manual
def test_llm_judge_understands_semantic_response():
    response = (
        "Use the account recovery option on the login page. "
        "A recovery link will be sent to your registered inbox."
    )

    scores = evaluate_with_llm(
        password_reset_case["ticket"],
        response,
        password_reset_case["expected_topics"],
        password_reset_case["forbidden_topics"]
    )

    assert passes_quality_gate(scores) is True


def test_deterministic_evaluation_pipeline():
    evaluation = run_deterministic_evaluation(test_cases)

    metrics = evaluation["metrics"]

    print_metrics(
        "Deterministic Evaluation Results",
        metrics
    )

    assert metrics == {
        "total": 10,
        "correct": 9,
        "accuracy": 0.9,
        "false_positives": 0,
        "false_negatives": 1
    }


@pytest.mark.manual
def test_llm_evaluation_pipeline():
    evaluation = run_llm_evaluation(test_cases)

    results = evaluation["results"]
    metrics = evaluation["metrics"]

    print_metrics(
        "LLM Judge Evaluation Results",
        metrics
    )

    assert metrics == {
        "total": 10,
        "correct": 10,
        "accuracy": 1.0,
        "false_positives": 0,
        "false_negatives": 0
    }

    for result in results:
        assert result["actual"] == result["expected"]


@pytest.mark.manual
def test_support_agent_generates_response():
    ticket = "I forgot my password. How can I access my account?"

    response = generate_support_response(ticket)

    print("\nSupport Agent Response:")
    print(response)

    assert response

def format_result(result: bool | None) -> str:
    if result:
        return "PASS"
    if result is False:
        return "FAIL"
    return "ERROR"

@allure.epic("AI Quality")
@allure.feature("Support Agent Evals")
@allure.story("Agent Quality Gate")
def test_agent_evaluation_pipeline():
    evaluation = run_agent_evaluation(test_cases)

    results = evaluation["results"]
    summary = evaluation["summary"]
    quality_gate_passed = evaluation["quality_gate_passed"]

    allure.attach(
        json.dumps(summary, indent=2),
        name="Evaluation Summary",
        attachment_type=allure.attachment_type.JSON
    )

    print("\nAgent Evaluation Results")

    for result in results:
        print(f"\n{result['id']}")
        print(f"Response: {result['response']}")
        print(
            f"Deterministic: "
            f"{'PASS' if result['deterministic_passed'] else 'FAIL'}"
        )
        print(
            f"LLM Judge: "
            f"{'PASS' if result['llm_passed'] else 'FAIL'}"
        )
        print(f"Scores: {result['llm_scores']}")
        print(f"Agent latency: {result['latency_seconds']:.2f}s")

        allure.attach(
            json.dumps(result, indent=2),
            name=f"Evaluation - {result['id']}",
            attachment_type=allure.attachment_type.JSON
        )

    print("\nAgent Evaluation Summary")
    print(f"Total responses: {summary['total']}")
    print(
        f"Deterministic passed: "
        f"{summary['deterministic_passed']}/{summary['total']} "
        f"({summary['deterministic_pass_rate']:.0%})"
    )
    print(
        f"LLM Judge passed: "
        f"{summary['llm_passed']}/{summary['total']} "
        f"({summary['llm_pass_rate']:.0%})"
    )
    print(f"Evaluator disagreements: {summary['disagreements']}")
    print(
        f"Average agent latency: "
        f"{summary['average_latency_seconds']:.2f}s"
    )
    print(
        f"Max agent latency: "
        f"{summary['max_latency_seconds']:.2f}s"
    )

    print(
        f"Quality Gate: "
        f"{'PASS' if quality_gate_passed else 'FAIL'}"
    )

    assert len(results) == len(test_cases)
    assert quality_gate_passed is True
