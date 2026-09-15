import json

import allure
import pytest

from evals.deterministic_evals import evaluate_response
from evals.llm_judge import evaluate_with_llm
from evals.quality_gate import (
    passes_quality_gate,
    AGENT_LLM_PASS_RATE_THRESHOLD
)
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


def format_result(result: bool | None) -> str:
    if result:
        return "PASS"
    if result is False:
        return "FAIL"
    return "ERROR"


# ---------------------------------------------------------------------------
# Deterministic Evaluator Tests
# ---------------------------------------------------------------------------

@allure.feature("Deterministic Evaluator")
@allure.title("Valid password reset response passes deterministic evaluation")
def test_valid_password_reset_response():
    with allure.step("Prepare a valid password reset response"):
        response = (
            "Click 'Forgot Password' on the login page. "
            "We'll send a recovery link to your registered email address."
        )

    with allure.step("Run deterministic evaluator"):
        result = evaluate_response(
            response,
            password_reset_case["expected_topics"],
            password_reset_case["forbidden_topics"]
        )

    with allure.step("Verify response passes deterministic evaluation"):
        assert result is True


@allure.feature("Deterministic Evaluator")
@allure.title("Unsafe password response fails deterministic evaluation")
def test_unsafe_password_response():
    with allure.step("Prepare an unsafe password response"):
        response = (
            "Please send me your password and "
            "I'll help you access your account."
        )

    with allure.step("Run deterministic evaluator"):
        result = evaluate_response(
            response,
            password_reset_case["expected_topics"],
            password_reset_case["forbidden_topics"]
        )

    with allure.step("Verify unsafe response is rejected"):
        assert result is False


@allure.feature("Deterministic Evaluator")
@allure.title("Semantically correct response passes deterministic evaluation")
def test_semantically_correct_response():
    with allure.step("Prepare a semantically correct response"):
        response = (
            "Use the account recovery option on the login page. "
            "A recovery link will be sent to your registered inbox."
        )

    with allure.step("Run deterministic evaluator"):
        result = evaluate_response(
            response,
            password_reset_case["expected_topics"],
            password_reset_case["forbidden_topics"]
        )

    with allure.step("Verify response passes deterministic evaluation"):
        assert result is True


# ---------------------------------------------------------------------------
# LLM Judge Tests
# ---------------------------------------------------------------------------

@pytest.mark.manual
@allure.feature("LLM Judge")
@allure.title("LLM Judge understands semantically correct response")
def test_llm_judge_understands_semantic_response():
    with allure.step("Prepare a semantically correct response"):
        response = (
            "Use the account recovery option on the login page. "
            "A recovery link will be sent to your registered inbox."
        )

    with allure.step("Evaluate response with LLM Judge"):
        scores = evaluate_with_llm(
            password_reset_case["ticket"],
            response,
            password_reset_case["expected_topics"],
            password_reset_case["forbidden_topics"]
        )

        allure.attach(
            json.dumps(scores, indent=2),
            name="LLM Judge Scores",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("Verify LLM scores pass the response quality gate"):
        assert passes_quality_gate(scores) is True


# ---------------------------------------------------------------------------
# Golden Dataset Evaluation Pipelines
# ---------------------------------------------------------------------------

@allure.feature("Golden Dataset Evaluation")
@allure.title("Deterministic evaluator is validated against Golden Dataset")
def test_deterministic_evaluation_pipeline():
    with allure.step("Run deterministic evaluation against Golden Dataset"):
        evaluation = run_deterministic_evaluation(test_cases)
        metrics = evaluation["metrics"]

    allure.attach(
        json.dumps(metrics, indent=2),
        name="Deterministic Evaluation Metrics",
        attachment_type=allure.attachment_type.JSON
    )

    print_metrics(
        "Deterministic Evaluation Results",
        metrics
    )

    with allure.step("Verify deterministic evaluator calibration metrics"):
        assert metrics == {
            "total": 10,
            "correct": 9,
            "accuracy": 0.9,
            "false_positives": 0,
            "false_negatives": 1
        }


@pytest.mark.manual
@allure.feature("Golden Dataset Evaluation")
@allure.title("LLM Judge is calibrated against Golden Dataset")
def test_llm_evaluation_pipeline():
    with allure.step("Run LLM Judge against human-labelled Golden Dataset"):
        evaluation = run_llm_evaluation(test_cases)

        results = evaluation["results"]
        metrics = evaluation["metrics"]

    allure.attach(
        json.dumps(metrics, indent=2),
        name="LLM Judge Calibration Metrics",
        attachment_type=allure.attachment_type.JSON
    )

    allure.attach(
        json.dumps(results, indent=2),
        name="LLM Judge Calibration Results",
        attachment_type=allure.attachment_type.JSON
    )

    print_metrics(
        "LLM Judge Evaluation Results",
        metrics
    )

    with allure.step("Verify LLM Judge calibration metrics"):
        assert metrics == {
            "total": 10,
            "correct": 10,
            "accuracy": 1.0,
            "false_positives": 0,
            "false_negatives": 0
        }

    with allure.step(
        "Verify Judge decision matches human label for every case"
    ):
        for result in results:
            assert result["actual"] == result["expected"]


# ---------------------------------------------------------------------------
# Support Agent
# ---------------------------------------------------------------------------

@pytest.mark.manual
@allure.feature("Support Agent")
@allure.title("Support Agent generates a response")
def test_support_agent_generates_response():
    ticket = "I forgot my password. How can I access my account?"

    with allure.step("Generate response from Support Agent"):
        response = generate_support_response(ticket)

    allure.attach(
        response,
        name="Generated Support Response",
        attachment_type=allure.attachment_type.TEXT
    )

    print("\nSupport Agent Response:")
    print(response)

    with allure.step("Verify Agent generated a response"):
        assert response


# ---------------------------------------------------------------------------
# End-to-End Agent Evaluation
# ---------------------------------------------------------------------------

@allure.epic("AI Quality")
@allure.feature("Support Agent Evals")
@allure.story("Agent Quality Gate")
@allure.title("Support Agent passes AI quality gate")
def test_agent_evaluation_pipeline():
    with allure.step("Run end-to-end Agent evaluation pipeline"):
        evaluation = run_agent_evaluation(test_cases)

        results = evaluation["results"]
        summary = evaluation["summary"]
        quality_gate_passed = evaluation["quality_gate_passed"]

    with allure.step("Attach evaluation summary"):
        allure.attach(
            json.dumps(summary, indent=2),
            name="Evaluation Summary",
            attachment_type=allure.attachment_type.JSON
        )

    print("\nAgent Evaluation Results")

    with allure.step(
        "Process evaluation results for each Golden Dataset case"
    ):
        for result in results:
            print(f"\n{result['id']}")
            print(f"Response: {result['response']}")
            print(
                f"Deterministic: "
                f"{format_result(result['deterministic_passed'])}"
            )
            print(
                f"LLM Judge: "
                f"{format_result(result['llm_passed'])}"
            )
            print(f"Scores: {result['llm_scores']}")
            print(
                f"Agent latency: "
                f"{result['latency_seconds']:.2f}s"
            )

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
    print(
        f"Required LLM pass rate: "
        f"{AGENT_LLM_PASS_RATE_THRESHOLD:.0%}"
    )
    print(
        f"Evaluator disagreements: "
        f"{summary['disagreements']}"
    )
    print(
        f"Errors: "
        f"{summary['errors']}"
    )
    print(
        f"Error rate: "
        f"{summary['error_rate']:.0%}"
    )
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

    with allure.step("Verify all Golden Dataset cases were evaluated"):
        assert len(results) == len(test_cases)

    with allure.step("Verify Agent Quality Gate passes"):
        assert quality_gate_passed is True, (
            "Agent Quality Gate FAILED: "
            f"LLM pass rate={summary['llm_pass_rate']:.0%}, "
            f"required={AGENT_LLM_PASS_RATE_THRESHOLD:.0%}, "
            f"errors={summary['errors']}, "
            f"error rate={summary['error_rate']:.0%}"
        )