"""SGR (Schema-Guided-Reasoning) workflow spec.

The Agent never calls runtime tools directly. Each step, the model emits ONE structured
pydantic schema (defined in `sgr.schemas`); the surrounding code (`core.py`) executes any
named tool calls against the Playground's `EcomRuntime` surface (`runtime_client.py`)
and feeds results back as transcript turns. `sgr.tools` routes each SGR tool-call schema
to its `EcomRuntimeClient` RPC.

Workflow shape::

    Init (no LLM, prefetch) -> NextStep(router)
      NextStep --collect--> Collect -> back to NextStep
      NextStep --modify---> Modify  -> back to NextStep
      NextStep --finish---> Complete -> AuditRefs -> FinalAnswer

Steps:
- **Init**: prefetch `AGENTS.md`, the root tree, and `/bin/id`; seed the transcript with
  the task prompt + prefetch and record a successful `/AGENTS.md` read as a collected
  ref. No LLM call.
- **NextStep** (`NextStepSchema`): recap state, then choose an exclusive decision. A
  continue decision describes the task gap and selects `collect` / `modify`; a finish
  decision selects an outcome-specific finish step and explains it.
- **Collect** (`CollectSchema`): read-only tool calls (`ReadCall` / `ListCall` /
  `TreeCall` / `FindCall` / `SearchCall` / `StatCall` / `ExecCall`), each reinforced
  with an `explanation`. Returns to NextStep.
- **Modify** (`ModifySchema`): mutating tool calls (`WriteCall` / `DeleteCall` /
  `ModifyExecCall`), each reinforced with an `explanation` AND a `policy_grounding`
  authorizing the mutation. Returns to NextStep.
- **Complete** (`CompleteSchema`): produced first on finish, using the Cascade pattern
  (format_source -> required_shape -> outcome -> bare_value -> message ->
  format_verified) - each field grounds the next.
- **AuditRefs** (`AuditRefsSchema`): runs AFTER Complete, reviewing the auto-tracked
  `collected_refs` against the produced answer and returning keep/refuse decisions with
  reasons.

Refs discipline: refs are recorded only for successful `read` / `write` / `delete` calls,
including the automatic `/AGENTS.md` read; `list` / `tree` / `find` / `search` / `stat` /
`exec` output is never a ref source.

Single shared transcript: all steps append to ONE growing `list[Message]`
(`WorkflowState.messages`); the LLM provider itself holds no state between calls. Every
step re-sends its own instruction prompt on every call, even on repeated loop turns -
the schema alone does not carry the task.

The final answer leaves the Agent ONLY via this repo's own `AgentService.Run` stream
(`RunEvent.final_answer`); the bitgn `EcomRuntime.Answer` RPC is deliberately never
wrapped by `EcomRuntimeClient` and is never called by any step.
"""
