import time

from evals.deterministic_evals import evaluate_response
from evals.llm_judge import evaluate_with_llm
from evals.quality_gate import (
    passes_quality_gate,
    passes_agent_quality_gate
)
from evals.support_agent import generate_support_response


def calculate_metrics(results: list[dict]) -> dict:
    total = len(results)

    correct = sum(
        result["actual"] == result["expected"]
        for result in results
    )

    false_positives = sum(
        result["actual"] is True and result["expected"] is False
        for result in results
    )

    false_negatives = sum(
        result["actual"] is False and result["expected"] is True
        for result in results
    )

    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }


def run_deterministic_evaluation(test_cases: list[dict]) -> dict:
    results = []

    for test_case in test_cases:
        good_result = evaluate_response(
            test_case["good_response"],
            test_case["expected_topics"],
            test_case["forbidden_topics"]
        )

        results.append({
            "id": test_case["id"],
            "response_type": "good",
            "expected": True,
            "actual": good_result
        })

        bad_result = evaluate_response(
            test_case["bad_response"],
            test_case["expected_topics"],
            test_case["forbidden_topics"]
        )

        results.append({
            "id": test_case["id"],
            "response_type": "bad",
            "expected": False,
            "actual": bad_result
        })

    return {
        "results": results,
        "metrics": calculate_metrics(results)
    }


def run_llm_evaluation(test_cases: list[dict]) -> dict:
    results = []

    for test_case in test_cases:
        good_scores = evaluate_with_llm(
            test_case["ticket"],
            test_case["good_response"],
            test_case["expected_topics"],
            test_case["forbidden_topics"]
        )

        results.append({
            "id": test_case["id"],
            "response_type": "good",
            "expected": True,
            "actual": passes_quality_gate(good_scores),
            "scores": good_scores
        })

        bad_scores = evaluate_with_llm(
            test_case["ticket"],
            test_case["bad_response"],
            test_case["expected_topics"],
            test_case["forbidden_topics"]
        )

        results.append({
            "id": test_case["id"],
            "response_type": "bad",
            "expected": False,
            "actual": passes_quality_gate(bad_scores),
            "scores": bad_scores
        })

    return {
        "results": results,
        "metrics": calculate_metrics(results)
    }


def run_agent_evaluation(test_cases: list[dict]) -> dict:
    results = []

    for test_case in test_cases:
        start_time = time.perf_counter()

        try:
            response = generate_support_response(
                test_case["ticket"]
            )
        except Exception as error:
            latency_seconds = time.perf_counter() - start_time

            results.append({
                "id": test_case["id"],
                "response": None,
                "deterministic_passed": None,
                "llm_passed": None,
                "llm_scores": None,
                "latency_seconds": latency_seconds,
                "error": str(error)
            })

            continue

        latency_seconds = time.perf_counter() - start_time

        deterministic_result = evaluate_response(
            response,
            test_case["expected_topics"],
            test_case["forbidden_topics"]
        )

        llm_scores = evaluate_with_llm(
            test_case["ticket"],
            response,
            test_case["expected_topics"],
            test_case["forbidden_topics"]
        )

        llm_result = passes_quality_gate(llm_scores)

        results.append({
            "id": test_case["id"],
            "response": response,
            "deterministic_passed": deterministic_result,
            "llm_passed": llm_result,
            "llm_scores": llm_scores,
            "latency_seconds": round(latency_seconds, 2),
            "error": None
        })

    total = len(results)

    deterministic_passed = sum(
        result["deterministic_passed"] is True
        for result in results
    )

    llm_passed = sum(
        result["llm_passed"] is True
        for result in results
    )

    disagreements = sum(
        result["deterministic_passed"] is not None
        and result["llm_passed"] is not None
        and result["deterministic_passed"] != result["llm_passed"]
        for result in results
    )

    errors = sum(
        result["error"] is not None
        for result in results
    )

    average_latency = sum(
        result["latency_seconds"]
        for result in results
    ) / total

    max_latency = max(
        result["latency_seconds"]
        for result in results
    )

    summary = {
        "total": total,
        "deterministic_passed": deterministic_passed,
        "deterministic_pass_rate": deterministic_passed / total,
        "llm_passed": llm_passed,
        "llm_pass_rate": llm_passed / total,
        "disagreements": disagreements,
        "errors": errors,
        "error_rate": errors / total,
        "average_latency_seconds": round(average_latency, 2),
        "max_latency_seconds": round(max_latency, 2)
    }
    quality_gate_passed = passes_agent_quality_gate(summary)

    return {
        "results": results,
        "summary": summary,
        "quality_gate_passed": quality_gate_passed
    }
