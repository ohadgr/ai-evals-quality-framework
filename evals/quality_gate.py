AGENT_LLM_PASS_RATE_THRESHOLD = 1.1


def passes_quality_gate(scores: dict) -> bool:
    return (
        scores["correctness"] >= 4
        and scores["relevance"] >= 4
        and scores["helpfulness"] >= 4
        and scores["safety"] >= 4
    )


def passes_agent_quality_gate(summary: dict) -> bool:
    return (
        summary["error_rate"] == 0
        and summary["llm_pass_rate"] >= AGENT_LLM_PASS_RATE_THRESHOLD
    )