---
name: nuedc-code-planner
description: Use when Codex needs to plan or implement code for NUEDC/electronic-design-contest projects with multiple scoring tasks, staged goals, maintainable architecture, task cycles, MVP/basic functions first, module interfaces, main contradiction analysis, hard-part code design, verification gates, and iterative implementation from simple to difficult.
---

# NUEDC Code Planner

Use this skill when a contest task is ready to become code. It turns a multi-score-task NUEDC project into a staged implementation plan and then guides code changes cycle by cycle.

This skill complements `analyze-nuedc-task`: use that skill to compile a raw problem statement into an engineering task package; use this skill when the next step is framework design, code implementation, and staged verification.

## Core Rule

Do not start by writing isolated feature code. First design the code framework, module responsibilities, module interfaces, shared state, logs, and verification gates. Then implement the easiest scoring loop and grow toward the full goal in 2 to 3 cycles.

## Required Assumptions

Before coding, state:

- Contest goal: the final code goal, usually "finish all scoring tasks that software can support."
- Known inputs: problem statement, scoring rules, hardware, sensors, actuators, current code, and confirmed constraints.
- Reasonable defaults: only for parameters that can be safely changed later.
- Unknowns that block code: sensor interface, actuator driver, pin map, timing, protocol, physical behavior, or acceptance criteria.

If the scoring path or key hardware interface is unclear, stop and ask. Do not invent pins, protocols, units, thresholds, or final PID/filter parameters.

## Step 1: Score Task Ladder

Convert the scoring tasks into an implementation ladder:

| Level | Meaning |
|---|---|
| Basic function | The smallest runnable behavior that proves hardware and framework are alive. |
| Basic score task | The easiest complete scoring loop. |
| Shared prerequisite | Code capability needed by many tasks, such as sensing, motion, state machine, logging, or calibration. |
| Advanced score task | Adds accuracy, speed, autonomy, or multi-stage behavior. |
| Final integration | Runs all required task phases with robust state transitions and logs. |

Implementation order must follow dependencies, not the problem statement order. If an advanced task depends on a shared prerequisite, implement and verify the prerequisite first.

## Step 2: Framework Before Features

Design a minimal maintainable architecture before writing task logic:

```text
app/
  task_state_machine        owns contest stages and transitions
  scheduler_or_main_loop    owns timing and periodic execution
  telemetry_or_log          prints key observability data
drivers/
  sensor drivers            expose raw data and health
  actuator drivers          expose safe low-level commands
modules/
  estimator                 converts raw data into state
  controller                converts target + state into output
  task_logic                owns scoring task decisions
config/
  pin map, constants, calibration placeholders
```

Keep names and layout consistent with the existing project. If the repo already has a structure, adapt to it instead of forcing this tree.

Each module must have:

- Responsibility: one sentence.
- Inputs: data it consumes.
- Outputs: data or commands it produces.
- Update rate or call timing.
- Failure signal: what it reports when it cannot be trusted.

## Step 3: Main Contradiction Code Design

Identify one or two hard points that decide whether scoring is possible. For code implementation, a main contradiction is usually where two concerns meet:

- raw sensing to reliable state
- state estimate to control output
- single loop to multi-stage task switching
- fast response to stability
- calibration to runtime robustness
- safety/protection to performance

For each main contradiction, design the code deliberately:

```text
Hard point:
Why it controls the score:
Data needed:
State variables:
Algorithm skeleton:
Logs:
Verification gate:
Fallback or degradation:
Do not implement yet:
```

Do not bury the hard point inside a generic helper. Put the important logic where it can be inspected, logged, tuned, and tested.

## Step 4: Two Or Three Cycles

Break implementation into 2 to 3 cycles. Each cycle must produce runnable code.

### Cycle 1: Framework + Basic Function

Goal:
- Build the module skeleton and interfaces.
- Make hardware or simulated IO observable.
- Implement the simplest runnable behavior.

Typical output:
- drivers compile and expose stable APIs
- state machine has idle/test/basic states
- logs show raw sensor values, commands, and task state
- one actuator or one sensor loop works

Gate:
- Code builds.
- Basic IO works or simulated data can drive the framework.
- Logs can locate the first failing link.

### Cycle 2: Basic Score Loop

Goal:
- Implement the easiest complete scoring loop.
- Use conservative parameters.
- Prove the shared prerequisite.

Typical output:
- estimator/controller/task logic connected
- one full task path can start, run, finish, timeout, or fail safely
- main contradiction has explicit logs and a first-pass algorithm

Gate:
- The basic score task runs end to end under controlled conditions.
- Failure reason is visible in logs.
- No advanced task is started if this gate fails.

### Cycle 3: Advanced Tasks + Integration

Goal:
- Add advanced scoring tasks in dependency order.
- Integrate multi-stage flow.
- Improve robustness only where logs show need.

Typical output:
- task state machine covers all selected scoring tasks
- shared modules reused, not duplicated
- calibration and fallback paths are explicit
- final logs are concise enough for competition debugging

Gate:
- All selected tasks build and can be run independently.
- Integrated flow has clear start, transition, finish, timeout, and recovery behavior.

If the project is small, merge Cycle 2 and Cycle 3. If the project is large, do not create more than three high-level cycles; split subtasks inside a cycle instead.

## Step 5: Implementation Contract

Before editing code, output:

```text
Goal:
Cycle:
Files/modules to touch:
Interfaces to add or change:
Behavior to implement:
Logs to add:
Verification command:
Stop conditions:
```

During implementation:

- Touch only files needed for the current cycle.
- Preserve existing style and hardware abstractions.
- Prefer explicit structs/enums/state machines over scattered globals.
- Add configuration constants only when used by current code.
- Add logs for raw input, processed state, control output, state transitions, and failure reasons.
- Keep placeholder functions small and clearly marked as not yet implemented.
- Do not optimize parameters without measurements.

## Step 6: Verification And Next Cycle

After each cycle:

1. Build or run the strongest available verification.
2. Summarize what passed, what failed, and the first failing link.
3. Update the next cycle only from evidence, not wishful feature expansion.
4. Keep a short remaining-task list ordered by scoring dependency.

Use this completion format:

```text
Cycle completed:
Implemented:
Verified:
Observed risk:
Next cycle:
Blocked by:
```

## Stop Conditions

Stop and ask, or produce only a verification task, when:

- Hardware interface or pin map is unknown.
- The task requires final thresholds, PID, filters, timing, or protection values without measurements.
- The main contradiction has no observable variables.
- A requested advanced task depends on an unverified basic loop.
- The failure is likely mechanical, power, sensor placement, or signal integrity rather than code.
- The user asks to implement all tasks at once without a buildable intermediate cycle.
