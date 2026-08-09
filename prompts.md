# ProbeIQ — Live Demo Verification Prompts

## Purpose

This document contains a comprehensive set of **live-demo prompts and
verification scenarios** for the ProbeIQ Interview Agent.

It is intended for hackathon live demonstrations, evaluator
walkthroughs, manual QA, regression testing, and final submission
verification.

The goal is to verify that ProbeIQ behaves like a realistic,
personalized, curriculum-grounded technical interviewer rather than a
scripted questionnaire.

------------------------------------------------------------------------

# 1. Recommended Primary Live Demo

Use this flow first during a hackathon presentation.

## Start the interview

> Start my technical interview based on my learning journey. Please
> interview me as a real technical interviewer rather than giving me a
> list of predefined questions.

**Verify:** - Relevant opening technical question. - Candidate
curriculum is used for calibration. - Internal candidate signals are not
exposed. - One question is asked at a time. - Interview tone feels
realistic.

## Strong RAG answer

> RAG combines retrieval with generation. Instead of relying only on
> what the language model already knows, the system retrieves relevant
> external information and provides that information as context to the
> model before generating the answer.

**Verify:** The interviewer should probe the reasoning instead of simply
saying “correct.”

## Reasoning answer

> I would choose the retrieval strategy based on the data and latency
> requirements. For semantic search I would use embeddings and a vector
> database, but for exact identifiers or highly structured information I
> would also consider keyword or metadata filtering.

**Verify:** The next question should build on this answer.

## Trade-off answer

> I would probably use hybrid retrieval in a production system because
> semantic similarity alone may miss exact identifiers, while keyword
> search alone can miss semantically related information.

**Verify:** Look for a deeper question about when hybrid retrieval is
useful, how it would be evaluated, or what its failure modes are.

## Weak answer

> I think vector databases are mainly used because they make searching
> embeddings faster. I don’t know much beyond that.

**Verify:** Difficulty should decrease or the interviewer should move
toward foundational probing. Internal scores or mission history must not
be exposed.

## Context answer

> I would keep the retrieved context small and relevant because sending
> unnecessary context increases token usage and can reduce answer
> quality.

**Verify:** A later question should remain connected to this reasoning.

## Production answer

> I would separate the inference service from the application layer,
> containerize the service, expose a controlled API, add observability,
> and monitor latency, failures, and model behavior.

**Verify:** The interviewer may probe observability, scaling,
reliability, security, latency, or deployment architecture.

## Completion

Continue answering naturally until the interview completes.

**Verify:** - At least 8 questions. - At least 4 distinct curriculum
days. - Context maintained. - Follow-ups generated. - Structured
feedback produced.

------------------------------------------------------------------------

# 2. RAG Verification

### Prompt

> Explain RAG to me as if you were designing it for a production
> enterprise application.

Verify that the interviewer stays grounded in relevant RAG concepts.

### Prompt

> I would split documents into chunks before generating embeddings.

Verify potential follow-ups around chunk size, overlap, semantic
boundaries, metadata, and retrieval quality.

### Prompt

> I would use a vector database to store embeddings and retrieve
> semantically similar content.

Verify potential probing around similarity search, metadata filtering,
indexing, distance metrics, and retrieval quality.

### Prompt

> A high retrieval score does not necessarily mean that the retrieved
> information is actually useful to the final answer.

Verify that the interviewer recognizes this as an evaluation insight.

### Prompt

> If retrieval is poor, I would investigate chunking, embeddings, query
> formulation, metadata filtering, and ranking before blaming the
> language model.

Verify that the next question builds on this diagnosis.

------------------------------------------------------------------------

# 3. Vector Database Verification

### Prompt

> Why would I use a vector database instead of a traditional relational
> database for semantic retrieval?

### Prompt

> I would probably use both PostgreSQL and a vector database because the
> two systems solve different retrieval problems.

### Prompt

> How would you evaluate whether my vector search is actually working
> well?

### Prompt

> What would make you choose pgvector over a dedicated vector database?

Verify that the interviewer probes reasoning rather than merely asking
definitions.

------------------------------------------------------------------------

# 4. Prompt Engineering Verification

### Prompt

> What makes a production prompt different from a simple instruction
> given to an LLM?

### Prompt

> I would explicitly define the expected output structure instead of
> relying on the model to format the response correctly every time.

### Prompt

> Prompt quality should be evaluated against actual task outcomes rather
> than judged only by how well the prompt reads.

Verify that the interviewer moves toward reliability, structured
generation, evaluation, and failure handling.

------------------------------------------------------------------------

# 5. Agentic AI Verification

### Prompt

> What makes an AI system agentic rather than simply an LLM call?

### Prompt

> I would not automatically use an agent for every AI problem. A
> deterministic workflow may be easier to test and more reliable.

### Prompt

> In a production agent, I would constrain the tools and state
> transitions instead of allowing unrestricted model behavior.

Verify discussion of tools, planning, state, iterative execution,
guardrails, and failure handling.

------------------------------------------------------------------------

# 6. LangGraph Verification

### Prompt

> Why might I use LangGraph instead of implementing an agent loop
> manually?

### Prompt

> I would represent the workflow as explicit states and transitions so
> that execution is easier to inspect and control.

Verify possible follow-ups around state, nodes, edges, conditional
routing, persistence, checkpointing, and failure recovery.

------------------------------------------------------------------------

# 7. MCP Verification

### Prompt

> Explain what the Model Context Protocol solves.

### Prompt

> I see MCP as a standardized way for AI applications to interact with
> external tools and resources.

### Prompt

> If an MCP server exposes a dangerous tool, the model should not
> automatically receive unrestricted access to it.

Verify that the interviewer can discuss interoperability,
tools/resources, architecture, permissions, and security.

------------------------------------------------------------------------

# 8. AI Deployment Verification

### Prompt

> How would you deploy an AI application so that the frontend does not
> directly manage model credentials?

### Prompt

> I would keep provider API keys on the backend and expose only
> controlled application endpoints to the frontend.

Verify discussion of backend boundaries, secrets, authentication, and
controlled APIs.

------------------------------------------------------------------------

# 9. Production AI Systems

### Prompt

> What changes when an AI prototype becomes a production system?

### Prompt

> A production AI system needs more than model accuracy. I would also
> monitor latency, cost, failures, retrieval quality, and user outcomes.

Verify that the interviewer can probe latency, reliability,
observability, security, cost, evaluation, scalability, and versioning.

------------------------------------------------------------------------

# 10. Deliberate Wrong Answer Test

### Prompt

> RAG means training the LLM again every time a new document is added to
> the knowledge base.

**Verify:** The interviewer should challenge or correct the
misconception and distinguish RAG from fine-tuning.

------------------------------------------------------------------------

# 11. Deliberate Partial Answer Test

### Prompt

> Embeddings turn text into vectors, and vector databases let us search
> those vectors.

**Verify:** This should be treated as a potentially shallow answer that
deserves probing.

------------------------------------------------------------------------

# 12. Deliberate Strong Answer Test

### Prompt

> For an enterprise RAG system, I would evaluate retrieval separately
> from generation. I would create a representative query set, measure
> retrieval relevance and recall, inspect failure cases, and then
> evaluate end-to-end answer faithfulness and usefulness.

**Verify:** The interviewer should recognize deeper understanding and
increase difficulty appropriately.

------------------------------------------------------------------------

# 13. Difficulty Adaptation Test

### Strong answer

> I would evaluate retrieval quality independently before optimizing the
> generator because otherwise it is difficult to determine whether
> failures originate in retrieval or generation.

**Verify:** The interviewer should be comfortable moving toward advanced
trade-offs.

### Weak answer

> I don’t know why retrieval needs to be evaluated separately.

**Verify:** The next question should become more foundational.

------------------------------------------------------------------------

# 14. Follow-Up Quality Test

### Candidate answer

> I would use metadata filtering before vector similarity when I already
> know attributes such as tenant, document type, or access scope.

**Verify:** A good follow-up should probe the reasoning, for example:

> Why would you apply metadata filtering before semantic retrieval?

or:

> How would you prevent cross-tenant data from appearing in retrieval
> results?

A poor follow-up would simply ask:

> What is RAG?

because that ignores the previous answer.

------------------------------------------------------------------------

# 15. Context Retention Test

Early in the interview say:

> I would choose hybrid retrieval because the application contains both
> natural-language questions and exact identifiers.

Later, when retrieval is discussed again, verify that the interviewer
can build on that decision.

A good continuation could be:

> Given your choice of hybrid retrieval, how would you decide when
> keyword matching should dominate semantic similarity?

------------------------------------------------------------------------

# 16. Candidate Personalization Test

### Prompt

> Start my interview and calibrate the difficulty based on my learning
> journey.

**Verify:** - Difficulty reflects candidate progress. - Candidate
signals influence calibration. - Internal signals are not leaked.

The interviewer should not say things such as:

> You completed 30 missions, so I will give you an advanced question.

or:

> You failed Mission X.

------------------------------------------------------------------------

# 17. Skipped Topic Test

### Prompt

> Interview me based on what I have actually learned rather than
> assuming that I know every topic in the curriculum.

**Verify:** Skipped content is not treated as established knowledge.

------------------------------------------------------------------------

# 18. Curriculum Grounding Test

### Prompt

> Ask me questions only from topics covered by my assigned curriculum.

**Verify:** Questions remain grounded in the supplied curriculum and
relevant candidate progress.

------------------------------------------------------------------------

# 19. Cross-Day Coverage Test

Run a complete interview.

Verify:

``` text
minimum questions >= 8
distinct curriculum days >= 4
```

Questions should remain relevant and should respect the application’s
configured topic/question caps.

------------------------------------------------------------------------

# 20. Question Repetition Test

### Prompt

> Please interview me normally.

Answer each question reasonably.

**Verify:** The system should not repeatedly ask the same question with
only minor wording changes. Follow-ups should probe a different
dimension when appropriate.

------------------------------------------------------------------------

# 21. Per-Topic Follow-Up Test

When a topic is introduced, verify that the interviewer can ask useful
follow-ups while respecting the application’s per-topic cap and
eventually broadening the interview.

------------------------------------------------------------------------

# 22. Multi-Turn Realistic Interview Test

Use:

### Turn 1

> Explain RAG in a production system.

### Turn 2

> I would use embeddings and a vector database for semantic retrieval.

### Turn 3

> I would also add metadata filtering because enterprise documents have
> tenant and permission boundaries.

### Turn 4

> I would evaluate retrieval separately from generation.

### Turn 5

> If retrieval quality is poor, I would inspect chunking, embeddings,
> query formulation, filtering, and ranking.

**Verify:** The interviewer should progressively deepen the same
conversation rather than resetting context.

------------------------------------------------------------------------

# 23. Architecture Trade-Off Test

### Prompt

> I have a small internal application with a deterministic workflow. I
> don’t think I need an autonomous agent.

**Verify:** The interviewer should discuss when an agent is or is not
justified.

------------------------------------------------------------------------

# 24. Failure Handling Test

### Prompt

> What should happen if an external tool used by an AI agent fails?

Verify potential discussion of retry, timeout, fallback, validation,
error reporting, state recovery, and observability.

------------------------------------------------------------------------

# 25. Security Test

### Prompt

> How would you secure an enterprise AI agent that can call external
> tools?

Verify potential discussion of authorization, least privilege, secret
management, input validation, tool allowlists, audit logs, and tenant
isolation.

------------------------------------------------------------------------

# 26. Cost Optimization Test

### Prompt

> Suppose the interview agent is technically correct but expensive to
> run. What would you optimize first?

Verify discussion of model selection, token budgets, prompt size,
caching, routing, unnecessary calls, and fallback behavior.

------------------------------------------------------------------------

# 27. Latency Test

### Prompt

> How would you reduce latency in a production AI interview system?

Verify discussion of faster models, token limits, smaller prompts,
avoiding unnecessary calls, caching, timeout configuration, routing, and
fallback strategies.

------------------------------------------------------------------------

# 28. Observability Test

### Prompt

> What would you monitor in a production AI interview agent?

Look for:

- request latency
- model latency
- token usage
- errors
- timeout rate
- fallback rate
- completion rate
- interview duration
- question-generation failures
- evaluation failures

------------------------------------------------------------------------

# 29. Evaluation Test

### Prompt

> How would you evaluate whether an AI interviewer is actually good?

Look for:

- question relevance
- curriculum coverage
- follow-up quality
- factual correctness
- difficulty calibration
- context retention
- candidate usefulness
- consistency
- latency
- completion rate

------------------------------------------------------------------------

# 30. Real Interview Style Test

### Prompt

> Interview me as if you were a senior AI engineer conducting a real
> technical interview. Do not explain the answer unless I ask. Challenge
> my reasoning when appropriate.

Verify one-question-at-a-time behavior, professional tone, challenge of
weak assumptions, follow-ups, and avoidance of tutoring-chatbot
behavior.

------------------------------------------------------------------------

# 31. Candidate Asks for the Answer

### Prompt

> I don’t know. Can you just explain the answer?

Verify graceful handling without corrupting session state or
unexpectedly terminating the interview.

------------------------------------------------------------------------

# 32. Candidate Changes Their Answer

### Prompt

> Actually, I want to revise my previous answer. I would use hybrid
> retrieval instead.

Verify that the interviewer handles the correction naturally and uses
the latest answer as context.

------------------------------------------------------------------------

# 33. Very Long Answer Test

Paste a long but relevant technical explanation.

Verify that the system:

- remains usable
- identifies important reasoning
- retains context
- asks a focused follow-up

------------------------------------------------------------------------

# 34. Extremely Short Answer Test

### Prompt

> Embeddings.

Verify that the interviewer probes rather than immediately concluding
that the candidate has no knowledge.

------------------------------------------------------------------------

# 35. “I Don’t Know” Test

### Prompt

> I don’t know the answer to that.

Verify graceful handling without repeated-question loops or exposed
internal scoring.

------------------------------------------------------------------------

# 36. Off-Topic Answer Test

### Prompt

> My favorite programming language is Python because it has many
> libraries.

Verify that the interviewer redirects toward the technical question.

------------------------------------------------------------------------

# 37. Candidate Challenges the Interviewer

### Prompt

> I disagree with that assumption. Why would you choose a vector
> database instead of PostgreSQL with pgvector?

Verify that the interviewer engages with the technical disagreement.

------------------------------------------------------------------------

# 38. Curriculum Tool Grounding Test

### Prompt

> Why would you choose the tool you learned for this part of the
> pipeline instead of another approach?

Verify that the interviewer grounds the discussion in actual curriculum
tools and objectives.

------------------------------------------------------------------------

# 39. Production Scenario Test

### Prompt

> Imagine this AI system is being deployed for an enterprise with
> sensitive internal documents. Design the architecture and explain your
> reasoning.

Verify discussion of retrieval, permissions, deployment, security,
observability, model selection, and reliability.

------------------------------------------------------------------------

# 40. End-of-Interview Feedback Verification

Complete a normal interview.

Verify that feedback contains the application’s structured fields, such
as:

- summary
- overall score
- confidence, where supported
- strengths
- weaknesses
- next steps

Feedback should reflect the actual interview rather than generic advice.

------------------------------------------------------------------------

# 41. Feedback Grounding Test

During an interview intentionally demonstrate:

- one strong area
- one weak area
- one partially correct area

Verify that final feedback distinguishes these areas.

------------------------------------------------------------------------

# 42. Feedback Actionability Test

After completion, inspect next steps.

Good feedback should connect recommendations to demonstrated weaknesses.

For example:

> Practice evaluating retrieval quality separately from generation and
> build a small benchmark set.

Poor feedback would be:

> Study AI more.

------------------------------------------------------------------------

# 43. API Contract Verification

Use the project’s existing technical specification and integration
tests.

The existing response shape should remain compatible, for example:

``` json
{
  "reply": "...",
  "done": false
}
```

and on completion:

``` json
{
  "reply": "...",
  "done": true,
  "feedback": {}
}
```

Do not alter the established API contract merely for the demo.

------------------------------------------------------------------------

# 44. Authentication Verification

Attempt to access the protected interview endpoint without valid
authentication.

Verify rejection according to the existing technical specification and
implementation.

------------------------------------------------------------------------

# 45. Candidate Ownership Verification

Attempt to operate on a session belonging to another candidate.

Verify that ownership enforcement remains intact.

------------------------------------------------------------------------

# 46. Session Continuity Verification

Start an interview and answer several questions.

Verify that subsequent requests continue the same session rather than
restarting.

------------------------------------------------------------------------

# 47. Duplicate Submission Verification

Submit the same candidate response twice rapidly.

Verify that duplicate-submission protection prevents accidental
duplicate turns.

------------------------------------------------------------------------

# 48. Error Recovery Verification

If a temporary provider failure is intentionally simulated in a safe
test environment:

Verify:

- controlled error
- no corrupted session state
- retry where supported
- no fake successful response

Do not intentionally break the production provider during the public
demo.

------------------------------------------------------------------------

# 49. Offline Engine Verification

If offline/deterministic mode is available:

### Prompt

> Start an interview using the available interview mode.

Verify that the offline path remains usable and satisfies the core
interview requirements.

------------------------------------------------------------------------

# 50. Live LLM Verification

When live LLM mode is enabled:

### Prompt

> Start my technical interview based on my curriculum and candidate
> profile.

Measure:

- time to first response
- per-turn latency
- timeout rate
- fallback behavior
- interview completion
- final feedback generation

Do not judge live performance using only a trivial one-word model probe.

------------------------------------------------------------------------

# 51. Model Health Probe

Before a live demo, each configured model can be checked independently
with:

> Reply with exactly one word: ready

This is only a provider/model health check. It does not prove that the
full Interview Agent request will be fast.

------------------------------------------------------------------------

# 52. Full Live Interview Performance Test

Run one complete interview and record:

``` text
Start latency:
Average question latency:
Maximum question latency:
Average evaluation latency:
Maximum evaluation latency:
Fallback count:
Timeout count:
Total interview duration:
Questions completed:
Curriculum days covered:
Feedback generated:
```

The important result is successful completion of the actual interview
path, not merely an isolated model response.

------------------------------------------------------------------------

# 53. Responsive UI Verification

Test:

- 390px
- 768px
- 1024px
- 1280px
- 1440px

Verify:

- no horizontal scrolling
- question area fits
- response composer fits
- timer remains visible
- progress remains visible
- controls remain usable
- thinking state is clear
- completion state is clear
- logo remains responsive
- navigation remains usable

------------------------------------------------------------------------

# 54. Logo Verification

Verify that the ProbeIQ logo:

- is the primary application branding
- uses the approved asset
- preserves aspect ratio
- is not stretched
- is not clipped
- remains responsive
- does not create horizontal overflow
- remains readable on mobile
- does not interfere with interview controls

------------------------------------------------------------------------

# 55. Loading State Verification

During a live LLM request verify that:

- the UI clearly communicates processing
- the page does not appear frozen
- duplicate submissions are prevented

------------------------------------------------------------------------

# 56. Completion State Verification

Verify that the UI clearly transitions from:

``` text
Active Interview
```

to:

``` text
Interview Complete
```

and displays structured feedback.

------------------------------------------------------------------------

# 57. Progress Verification

Verify that the progress indicator updates correctly and never:

- moves backward unexpectedly
- exceeds configured limits
- displays impossible counts
- becomes inconsistent with the actual conversation

------------------------------------------------------------------------

# 58. Realistic Candidate Demo Script

Use this sequence for a polished hackathon presentation.

### Opening

> Start my technical interview based on my learning journey.

### Strong answer

> RAG retrieves external information and gives that context to the model
> before generation, which helps the system answer using information
> that is not necessarily contained in the model’s original parameters.

### Deeper answer

> I would evaluate retrieval separately from generation because
> otherwise I can’t tell whether an incorrect answer came from poor
> retrieval or from generation.

### Trade-off

> For an enterprise system, I would consider hybrid retrieval because
> semantic search is useful for meaning while keyword and metadata
> filtering are useful for exact identifiers and access constraints.

### Production answer

> I would keep authorization and tenant filtering before or during
> retrieval so that the model never receives documents the user is not
> allowed to access.

### Agent answer

> I would only introduce an agent where dynamic tool selection or
> iterative decisions are actually needed. A deterministic workflow is
> preferable when the process is known in advance.

### Weak answer

> I’m not sure how I would evaluate that.

### Recovery

> I would start by creating a small evaluation dataset and inspect
> retrieval relevance before changing the model.

### Final

> Give me my interview feedback based only on how I performed in this
> interview.

------------------------------------------------------------------------

# 59. Anti-Script Test

### Prompt

> Ask me a technical question.

Provide different answers across multiple runs.

Verify that the sequence is not always identical and that questions can
reflect:

- candidate profile
- curriculum
- previous answer
- interview state
- difficulty
- follow-up opportunities

------------------------------------------------------------------------

# 60. Same Candidate, Different Answers Test

Start another interview with the same candidate and provide
substantially different answers.

Verify that the follow-up trajectory can change based on the answers.

------------------------------------------------------------------------

# 61. Different Candidate Personalization Test

If multiple synthetic candidate profiles are available, run interviews
for candidates with meaningfully different progress.

Verify that the interviews can differ in initial calibration or topic
focus without exposing private/internal profile signals.

------------------------------------------------------------------------

# 62. Curriculum Coverage Demonstration

After a completed interview, inspect question coverage.

Verify:

``` text
questions >= 8
distinct curriculum days >= 4
```

and confirm that questions remain relevant to the candidate.

------------------------------------------------------------------------

# 63. Follow-Up Demonstration

Capture a sequence such as:

``` text
Q1 → Candidate Answer
      ↓
Q2 Follow-up
      ↓
Candidate Answer
      ↓
Q3 Deeper Probe
```

Verify that Q2 and Q3 clearly relate to previous reasoning.

------------------------------------------------------------------------

# 64. Context Demonstration

Early in the interview:

> I would use hybrid retrieval because exact identifiers are important
> in this system.

Several turns later, verify whether the interviewer can build on that
decision.

------------------------------------------------------------------------

# 65. Difficulty Calibration Demonstration

### Strong answer

> I would evaluate the retrieval component independently using a
> representative query set, compare relevant-document recall, inspect
> ranking failures, and then measure end-to-end answer faithfulness.

Verify that the interviewer can probe advanced trade-offs.

### Weak answer

> I don’t know what retrieval evaluation means.

Verify that the interviewer moves toward simpler concepts.

------------------------------------------------------------------------

# 66. Interviewer Behavior Checklist

During the live demo:

- [ ] asks one question at a time
- [ ] does not dump a questionnaire
- [ ] uses curriculum information
- [ ] uses candidate progress for calibration
- [ ] does not expose internal learning signals
- [ ] adapts to answers
- [ ] asks follow-ups
- [ ] remembers relevant context
- [ ] varies difficulty
- [ ] challenges incorrect answers
- [ ] probes shallow answers
- [ ] gives strong answers deeper treatment
- [ ] avoids unnecessary repetition
- [ ] eventually broadens curriculum coverage
- [ ] completes the required interview
- [ ] produces structured feedback

------------------------------------------------------------------------

# 67. Hackathon Requirement Checklist

## Conversational technical interview

> Interview me as a real AI engineering interviewer. Ask one question at
> a time and adapt based on my answers.

**PASS:** The interaction is conversational rather than scripted.

## Assess candidate understanding

> Don’t just ask definitions. Probe my reasoning and ask why I would
> make specific engineering decisions.

**PASS:** The interviewer evaluates depth and reasoning.

## Adapt naturally

Give both strong and weak answers during the same interview.

**PASS:** Difficulty and follow-up style change appropriately.

## Intelligent follow-ups

Give a detailed technical answer containing a specific architectural
decision.

**PASS:** The next question probes that decision.

## Maintain context

Introduce a technical decision early and reference it indirectly later.

**PASS:** The interviewer maintains continuity.

## Minimum 8 questions

Complete the interview.

**PASS:** At least 8 questions are asked.

## At least 4 curriculum days

Inspect completed interview coverage.

**PASS:** At least 4 distinct curriculum days are represented.

## Structured feedback

Complete the interview.

**PASS:** Structured feedback is returned.

## Required HTTP endpoint

Exercise the documented endpoint and existing API integration test.

**PASS:** The endpoint follows the technical specification.

------------------------------------------------------------------------

# 68. Final Demo Acceptance Checklist

## Backend

- [ ] Backend starts successfully
- [ ] Required endpoint is available
- [ ] Authentication works
- [ ] Candidate ownership works
- [ ] Session creation works
- [ ] Session continuation works
- [ ] Interview completion works
- [ ] Feedback generation works
- [ ] Offline mode works
- [ ] Live LLM mode works when enabled
- [ ] LLM timeout behavior is controlled
- [ ] Provider failures do not corrupt state

## Interview Intelligence

- [ ] Curriculum is actually used
- [ ] Candidate profile is actually used
- [ ] Skipped topics are respected
- [ ] Questions are relevant
- [ ] Follow-ups depend on previous answers
- [ ] Context is maintained
- [ ] Difficulty adapts
- [ ] Weak answers are probed
- [ ] Strong answers receive deeper questions
- [ ] Incorrect answers are challenged
- [ ] Repetition is controlled
- [ ] 8+ questions are possible
- [ ] 4+ curriculum days are covered
- [ ] Final feedback is grounded in performance

## Frontend

- [ ] Logo is correctly integrated
- [ ] Navbar/header works
- [ ] Interview page is structured
- [ ] Question area is clear
- [ ] Answer composer works
- [ ] Timer works
- [ ] Progress works
- [ ] Thinking state works
- [ ] Error state works
- [ ] Retry works
- [ ] Completion state works
- [ ] Feedback is readable
- [ ] No horizontal overflow
- [ ] Mobile layout works
- [ ] Desktop layout works

## Quality

- [ ] Backend tests pass
- [ ] Ruff passes
- [ ] Mypy passes
- [ ] Frontend lint passes
- [ ] Frontend build passes
- [ ] E2E tests pass
- [ ] Live LLM path has been measured
- [ ] Demo model/provider has been health-checked
- [ ] Full live interview has been tested
- [ ] No secrets are exposed
- [ ] No unnecessary code changes were introduced

------------------------------------------------------------------------

# 69. Recommended 5-Minute Hackathon Demo

1.  **Introduce** \> Start my technical interview based on my learning
    journey.

2.  **Show personalization** Let the interviewer ask its first question
    and explain that curriculum and candidate information calibrate the
    interview.

3.  **Give a strong answer** \> I would evaluate retrieval separately
    from generation because otherwise I cannot identify whether the
    failure came from retrieval or generation.

4.  **Show the adaptive follow-up.**

5.  **Give a trade-off** \> I would use hybrid retrieval because
    semantic similarity and exact identifier matching solve different
    problems.

6.  **Show a deeper follow-up.**

7.  **Give a weak answer** \> I don’t know much about that.

8.  **Show difficulty adaptation.**

9.  **Continue until completion.**

10. **Show structured feedback.**

11. **Briefly explain:**

``` text
Candidate Profile
       ↓
Curriculum
       ↓
Interview Planning
       ↓
Question Agent
       ↓
Candidate Answer
       ↓
Evaluation
       ↓
Adaptive Follow-up
       ↓
Interview Completion
       ↓
Structured Feedback
```

------------------------------------------------------------------------

# 70. Demo Safety Rules

1.  Never expose API keys.
2.  Never paste secrets into the chat or screenshots.
3.  Do not change production configuration immediately before presenting
    unless it has been tested.
4.  Prefer a previously verified provider/model configuration.
5.  Run one complete live interview before the presentation.
6.  Keep an offline/deterministic fallback available when supported.
7.  Do not demonstrate only isolated model health checks.
8.  Measure the actual interview path.
9.  Do not claim a model is fast solely because a trivial probe is fast.
10. Do not modify the API contract for the demo.
11. Do not remove curriculum grounding to simplify the demo.
12. Do not remove personalization to shorten prompts.
13. Keep the presentation focused on adaptive interviewing.

------------------------------------------------------------------------

# 71. Evidence to Capture for Submission

Capture evidence of:

### Candidate personalization

``` text
Candidate Profile
        ↓
Calibrated Interview
```

### Curriculum grounding

``` text
Question
        ↓
Relevant Curriculum Topic/Day
```

### Follow-up reasoning

``` text
Candidate Answer
        ↓
Evaluation
        ↓
Follow-up Question
```

### Context

``` text
Previous Technical Decision
        ↓
Later Question Builds On It
```

### Completion

``` text
8+ Questions
4+ Curriculum Days
        ↓
Structured Feedback
```

### Frontend

Capture:

- desktop interview page
- mobile interview page
- responsive logo
- active interview state
- thinking state
- completed feedback state

------------------------------------------------------------------------

# 72. Final Golden Prompt

> Start a realistic technical interview based on my curriculum progress
> and learning journey. Interview me like a real AI engineering
> interviewer, not like a static quiz. Ask one question at a time,
> evaluate my answers, adapt the difficulty, and ask intelligent
> follow-up questions based on what I actually say. Cover multiple areas
> of my completed curriculum and maintain context throughout the
> interview. Do not reveal internal candidate signals or profile
> details. At the end, provide structured, actionable feedback based on
> my actual performance.

------------------------------------------------------------------------

# 73. Final Verification Principle

The strongest proof that ProbeIQ is an **AI Interview Agent** is not
simply that it can generate technical questions.

The strongest proof is:

> **The next question is meaningfully influenced by the candidate’s
> previous answer, the candidate’s learning journey, and the curriculum
> context.**

The complete expected loop is:

``` text
Candidate Profile
       +
Curriculum
       ↓
Personalized Question
       ↓
Candidate Answer
       ↓
Answer Evaluation
       ↓
Context + Reasoning
       ↓
Adaptive Follow-up
       ↓
Difficulty Adjustment
       ↓
Broader Curriculum Coverage
       ↓
Interview Completion
       ↓
Structured Feedback
```
