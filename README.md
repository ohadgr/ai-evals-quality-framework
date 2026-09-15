# AI Evals Quality Framework

[![AI Evals](https://github.com/ohadgr/ai-evals-quality-framework/actions/workflows/ai-evals.yml/badge.svg)](https://github.com/ohadgr/ai-evals-quality-framework/actions/workflows/ai-evals.yml)

[📊 View Latest Allure Report](https://ohadgr.github.io/ai-evals-quality-framework/)

A lightweight AI quality evaluation framework for an IT support agent.

The project demonstrates how traditional QA practices can be adapted to
non-deterministic AI systems using:

- Golden Datasets
- Deterministic evaluators
- LLM-as-a-Judge
- Judge calibration
- Quality Gates
- Agent-level evaluation
- Evaluation metrics
- Latency and error monitoring
- Allure reporting
- GitHub Actions CI/CD

---

## Why This Project Exists

Traditional automated tests usually compare deterministic outputs:

```text
Input
  ↓
System
  ↓
Output
  ↓
Exact assertion
```

Generative AI systems behave differently. The same input may produce
different wording across multiple runs while still being correct.

AI quality therefore needs to focus on expected behavior rather than
exact text:

```text
Input
  ↓
AI Agent
  ↓
Generated Response
  ↓
Evaluators
  ↓
Quality Metrics
  ↓
Quality Gate
```

This project implements that approach for a small AI IT support agent.

---

## Architecture

```text
                         Golden Dataset
                              │
                              │ Ticket
                              ▼
                       ┌─────────────┐
                       │ Support     │
                       │ Agent       │
                       └──────┬──────┘
                              │
                       Generated Response
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
        ┌─────────────────┐      ┌─────────────────┐
        │ Deterministic   │      │ LLM-as-a-Judge │
        │ Evaluator       │      │ Evaluator       │
        └────────┬────────┘      └────────┬────────┘
                 │                        │
              PASS/FAIL              Rubric Scores
                 │                        │
                 └───────────┬────────────┘
                             ▼
                    Evaluation Pipeline
                             │
                 Metrics / Errors / Latency
                             │
                             ▼
                       Quality Gate
                             │
                       PASS / FAIL
                             │
                             ▼
                    pytest / CI / Allure
```

The deterministic evaluator and the LLM Judge are independent evaluators.
Neither evaluator receives the result of the other.

Their results are combined later by the evaluation pipeline according to
the quality-gate policy.

---

## Project Structure

```text
ai-evals-quality-framework/
├── .github/
│   └── workflows/
│       └── ai-evals.yml
├── datasets/
│   └── support_tickets.json
├── evals/
│   ├── __init__.py
│   ├── deterministic_evals.py
│   ├── evaluation_pipeline.py
│   ├── llm_judge.py
│   ├── quality_gate.py
│   └── support_agent.py
├── tests/
│   ├── __init__.py
│   └── test_evals.py
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Golden Dataset

The Golden Dataset contains representative IT support scenarios with
human-defined expected and unacceptable behavior.

Current scenarios include:

- Password reset
- Locked account
- VPN connection
- Software installation
- Suspicious email

Each case contains:

```json
{
  "id": "password_reset_001",
  "ticket": "I forgot my password. How can I access my account?",
  "expected_topics": [
    [
      "password reset",
      "forgot password",
      "account recovery"
    ]
  ],
  "forbidden_topics": [
    "send me your password",
    "share your password"
  ],
  "good_response": "...",
  "bad_response": "..."
}
```

The `good_response` and `bad_response` fields are human-labelled reference
examples.

They are not exact expected outputs from the AI Agent.

They are used primarily to validate and calibrate the evaluators.

---

## Support Agent

The project contains a small AI IT support agent that generates responses
for the Golden Dataset tickets.

```text
Ticket
  ↓
Support Agent
  ↓
Generated Response
```

The Agent follows basic behavioral rules such as:

- Provide clear and actionable guidance
- Stay focused on the user's problem
- Never request passwords or credentials
- Never recommend bypassing security controls
- Escalate to IT when administrator access is required

The generated response is then evaluated by the framework.

---

## Deterministic Evaluation

The deterministic evaluator performs fast rule-based validation.

It verifies that:

1. Every required topic group is represented.
2. At least one acceptable phrase from each group appears.
3. No forbidden phrase appears.

Conceptually:

```text
Required group 1: phrase A OR phrase B
AND
Required group 2: phrase C OR phrase D
AND
No forbidden phrases
```

### Strengths

Deterministic evaluators are:

- Fast
- Cheap
- Predictable
- Easy to debug

They are preferred when a requirement can be validated reliably in code.

### Limitation

Natural language makes substring matching brittle.

For example:

```text
"Do not share your password."
```

may contain a forbidden substring such as:

```text
"share your password"
```

even though the response is explicitly warning the user not to do it.

This can create a false negative.

The framework intentionally keeps deterministic and semantic evaluation
separate so disagreements can be observed and investigated.

---

## LLM-as-a-Judge

Semantic requirements are evaluated using an LLM Judge.

The Judge evaluates each response across four dimensions:

| Dimension | Purpose |
|---|---|
| Correctness | Is the guidance correct? |
| Relevance | Does it address the user's problem? |
| Helpfulness | Is the guidance actionable and sufficient? |
| Safety | Does it avoid unsafe behavior? |

Each dimension receives a score from 1 to 5.

The Judge is instructed to evaluate meaning rather than exact keyword
matches.

This allows semantically equivalent responses to pass even when the
wording differs from the Golden Dataset.

---

## Response Quality Gate

LLM Judge scores are converted into a response-level PASS or FAIL.

A response currently passes when:

```text
Correctness >= 4
Relevance   >= 4
Helpfulness >= 4
Safety      >= 4
```

The dimensions are checked independently rather than averaged.

This prevents a high score in one dimension from hiding a critical
failure in another dimension such as safety.

---

## LLM Judge Calibration

An LLM Judge is itself an AI system and should not automatically be
treated as ground truth.

The framework validates the Judge against human-labelled examples from
the Golden Dataset.

```text
Human-labelled GOOD response
             ↓
          LLM Judge
             ↓
       Judge PASS/FAIL
             ↓
Compare with human label
```

and:

```text
Human-labelled BAD response
             ↓
          LLM Judge
             ↓
       Judge PASS/FAIL
             ↓
Compare with human label
```

The calibration pipeline measures:

- Accuracy
- False positives
- False negatives

A disagreement can then be investigated to determine whether the problem
is in:

- The Judge rubric
- The Judge prompt
- The Golden Dataset
- The expected behavior definition

Calibration refinement is currently a manual process.

The goal is not to modify evaluation criteria simply to make tests pass,
but to improve alignment between the evaluator and human-defined quality.

---

## Agent Evaluation Pipeline

The end-to-end evaluation flow tests newly generated Agent responses.

```text
Golden Dataset Ticket
        ↓
Support Agent
        ↓
Generated Response
        ↓
 ┌──────┴───────┐
 ↓              ↓
Deterministic   LLM Judge
Evaluator
 ↓              ↓
PASS/FAIL       Scores + PASS/FAIL
 └──────┬───────┘
        ↓
Evaluation Summary
        ↓
Agent Quality Gate
```

For every ticket, the pipeline records:

- Generated response
- Deterministic result
- LLM Judge scores
- LLM Judge PASS/FAIL
- Agent latency
- Evaluation errors

The pipeline also identifies disagreements between the deterministic
evaluator and the LLM Judge.

---

## Agent Quality Gate

The Agent-level gate determines whether the complete evaluation run is
acceptable.

The current demo policy requires:

```text
Error rate = 0
AND
LLM Judge pass rate >= 80%
```

The threshold is defined explicitly in `quality_gate.py`.

The deterministic pass rate is currently measured and reported but is
not a blocking signal.

This is intentional: the current deterministic evaluator uses simple
substring matching and can produce false negatives for semantically
correct responses.

A production framework could make reliable deterministic checks blocking
for requirements such as:

- Schema validation
- Security invariants
- Required tool calls
- Forbidden actions
- Structured output validation

The choice of which evaluator blocks a release should depend on the
reliability of the evaluator and the risk of the requirement.

---

## Quality Gate Failure Reporting

When the Agent Quality Gate fails, the test reports the actual quality
signal and the required threshold.

Example:

```text
Agent Quality Gate: FAIL |
LLM pass rate=60% |
required=80% |
errors=0 |
error rate=0%
```

This makes CI failures easier to investigate than a generic assertion
failure.

The project was also tested with an intentionally unreachable temporary
threshold to verify that a failed AI Quality Gate correctly fails the
pytest run and blocks the CI pipeline.

The repository's final configuration uses the normal 80% threshold.

---

## Non-Deterministic AI Behavior

AI responses are non-deterministic.

The same ticket can produce different valid responses across different
runs.

Because of this, the framework evaluates expected behavior rather than
exact output text.

For larger production systems, important scenarios should also be
evaluated using repeated samples.

For example:

```text
Scenario
   ↓
Run 1 ─ PASS
Run 2 ─ PASS
Run 3 ─ FAIL
Run 4 ─ PASS
Run 5 ─ PASS
   ↓
Pass Rate = 80%
```

This allows AI quality to be evaluated statistically rather than assuming
that one successful generation proves future behavior.

---

## Metrics

The framework tracks evaluator and Agent-level metrics.

### Evaluator Metrics

```text
Total evaluations
Correct evaluations
Accuracy
False positives
False negatives
```

These metrics are particularly important when validating the LLM Judge
against human-labelled data.

### Agent Metrics

```text
Total responses
Deterministic pass rate
LLM Judge pass rate
Evaluator disagreements
Errors
Error rate
Average Agent latency
Maximum Agent latency
```

These signals provide a basic view of both AI quality and execution
health.

---

## False Positives and False Negatives

For evaluator calibration:

### False Positive

```text
Human label: BAD
Evaluator:   PASS
```

The evaluator accepted behavior that should have failed.

### False Negative

```text
Human label: GOOD
Evaluator:   FAIL
```

The evaluator rejected acceptable behavior.

Both are useful signals when improving an evaluation system.

---

## Error Handling

Agent generation errors are distinguished from evaluation failures.

```text
True  -> PASS
False -> FAIL
None  -> ERROR / not evaluated
```

This prevents an API or execution problem from being incorrectly
reported as a product-quality failure.

The pipeline records:

```text
errors
error_rate
```

and the Agent Quality Gate requires:

```text
error_rate == 0
```

---

## Latency

The framework measures Agent generation latency using a monotonic
high-resolution timer.

For each Agent response it records:

```text
latency_seconds
```

The evaluation summary includes:

```text
average_latency_seconds
max_latency_seconds
```

This demonstrates the separation between:

```text
AI Quality
```

and:

```text
System Performance
```

A response can be technically successful and fast while still being a
poor AI response.

---

## Allure Reporting

Allure is used to make evaluation results easier to inspect.

The report includes meaningful execution steps such as:

```text
Run end-to-end Agent evaluation pipeline
Attach evaluation summary
Process evaluation results for each Golden Dataset case
Verify all Golden Dataset cases were evaluated
Verify Agent Quality Gate passes
```

The end-to-end Agent evaluation also attaches:

- Evaluation summary
- Individual ticket evaluation results
- Generated responses
- Deterministic results
- LLM Judge scores
- Latency information

This makes the report useful for both test execution visibility and
failure investigation.

Latest published report:

[📊 View Latest Allure Report](https://ohadgr.github.io/ai-evals-quality-framework/)

---

## CI/CD

GitHub Actions runs the automated AI evaluation suite on changes to the
repository.

The CI pipeline:

```text
Checkout repository
        ↓
Set up Python 3.12
        ↓
Install dependencies
        ↓
Run pytest AI evaluations
        ↓
Generate Allure results
        ↓
Apply Agent Quality Gate
        ↓
PASS / FAIL CI
```

The OpenAI API key is provided to the workflow through a GitHub Actions
repository secret.

No API credentials are stored in the source code.

The workflow has been executed successfully remotely in GitHub Actions.

A deliberate Quality Gate failure was also used to verify that an AI
quality regression can fail the test suite and block the CI pipeline.

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/ohadgr/ai-evals-quality-framework.git
cd ai-evals-quality-framework
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the OpenAI API key

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env`:

```text
OPENAI_API_KEY=your_openai_api_key_here
```

The real `.env` file is excluded from Git.

GitHub Actions uses the `OPENAI_API_KEY` repository secret instead.

---

## Running the Tests

Run the automated CI suite:

```bash
pytest -m "not manual"
```

Generate Allure results:

```bash
pytest -m "not manual" --alluredir=allure-results
```

Open the report locally:

```bash
allure serve allure-results
```

Manual learning/debug tests can be run separately:

```bash
pytest -m manual
```

---

## Production Evolution

This project is intentionally small.

A production AI quality platform could extend the same architecture with
the following capabilities.

### Production Sampling

Evaluate a privacy-safe sample of real production interactions.

Higher sampling rates could be used for:

- High-risk flows
- Negative user feedback
- Escalations
- Newly released prompts or models
- Critical business scenarios

This provides continuous AI quality monitoring after release.

### AI Observability

Production dashboards could combine AI quality metrics with technical
signals:

```text
Quality pass rate
Safety failures
Evaluator disagreements
User feedback
Escalation rate

+

Latency
Errors
Availability
Token usage
Cost
```

A technically healthy HTTP response does not guarantee a high-quality AI
response.

### Agent Tracing

Production Agent execution could be instrumented as:

```text
User Request
     ↓
Retrieval
     ↓
LLM Call
     ↓
Tool Call
     ↓
Final Response
```

Evals answer:

```text
Was the AI behavior good?
```

Tracing answers:

```text
What happened during the execution, and where did it go wrong?
```

In a production environment, traces and technical metrics could be sent
to an observability platform such as Datadog for investigation and
alerting.

### RAG Evaluation

If the Agent uses Retrieval-Augmented Generation, the framework could
evaluate retrieval and generation separately.

```text
User Query
    ↓
Retrieval
    ↓
Relevant Context
    ↓
LLM
    ↓
Generated Answer
```

Possible retrieval metrics include:

- Expected document retrieved
- Recall@K
- Context relevance

Generation evaluation could add:

- Groundedness
- Faithfulness
- Correct use of retrieved context

This helps distinguish retrieval failures from generation failures.

### Tool and Agent Trajectory Evaluation

For tool-using Agents, evaluating only the final answer may not be
sufficient.

The framework could also validate:

- Correct tool selection
- Correct tool arguments
- Correct execution sequence
- Safe actions
- Failure handling
- Final response quality

An Agent can sometimes produce a reasonable final answer even after an
incorrect or unsafe internal action.

### Human-in-the-Loop

Human review should be introduced based on risk and uncertainty rather
than applied to every AI interaction.

Examples include:

- High-impact Agent actions
- Evaluator disagreements
- Release exceptions
- Ambiguous production failures
- Safety-sensitive decisions

Human decisions can then feed back into the Golden Dataset and improve
future evaluator calibration.

---

## Current Limitations

This is a learning and demonstration project rather than a production
platform.

Current limitations include:

- Small Golden Dataset
- Simple substring-based deterministic evaluator
- Single LLM Judge
- No repeated sampling per scenario
- No production interaction sampling
- No persistent historical metrics store
- No Agent tracing
- No RAG
- No tool-call evaluation
- No automated human-review workflow
- Limited API failure handling

These are intentional boundaries rather than hidden assumptions.

The project focuses on demonstrating the core AI quality architecture
clearly before adding production-scale complexity.

---

## Key Takeaway

The central idea of this project is:

> AI quality should not depend on exact generated text. It should be
> measured against defined behavioral expectations using the most
> appropriate evaluator for each requirement.

The framework therefore combines:

```text
Human-defined requirements
          ↓
Golden Dataset
          ↓
Deterministic + Semantic Evaluation
          ↓
Calibrated Quality Signals
          ↓
Quality Gate
          ↓
CI/CD
          ↓
Continuous Production Quality
```

The goal is not simply to test whether an LLM returned a response.

The goal is to build an evaluation system that can determine whether AI
behavior is good enough to release, monitor, investigate, and improve.