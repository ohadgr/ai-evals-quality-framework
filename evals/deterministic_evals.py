def evaluate_response(
    response: str,
    expected_topics: list[list[str]],
    forbidden_topics: list[str]
) -> bool:
    response = response.lower()

    has_expected_topics = all(
        any(
            phrase.lower() in response
            for phrase in topic_group
        )
        for topic_group in expected_topics
    )

    has_forbidden_topics = any(
        phrase.lower() in response
        for phrase in forbidden_topics
    )

    return has_expected_topics and not has_forbidden_topics
