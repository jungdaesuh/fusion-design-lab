# AGENTS.md

This repository is for the Fusion Design Lab hackathon submission. Treat it as a clean, public-facing artifact repository, not a general research sandbox.

## Mission

Build and ship one clear, reproducible OpenEnv environment for budget-constrained stellarator design.

The core product is the environment:

- narrow task
- legible observation space
- discrete action space
- explicit constraints
- reward function that can be explained and iterated

Training is supporting evidence. Do not let the repo drift into training-first work.

## Source of Truth

Use these docs as the repo documentation SSOT:

- `docs/FUSION_DESIGN_LAB_PLAN_V2.md` for planning and execution order
- `docs/P1_ENV_CONTRACT_V1.md` for the live technical contract
- `docs/P1_PARAMETERIZATION_DEEPDIVE.md` for blocker evidence and supporting rationale

Legacy planning docs are archived under `docs/archive/`. They are not active SSOT surfaces.

`docs/archive/PIVOT_P1_ROTATING_ELLIPSE.md` is a short supporting decision record, not a planning SSOT.

If code and docs disagree, either:

1. update code to match the docs, or
2. deliberately update the docs in the same change

Do not leave silent divergence.

## Project Priorities

1. Freeze the environment contract before heavy iteration.
2. Keep scope to one stable task.
3. Treat reward as iterative: `Reward V0`, then `Reward V1`, etc.
4. Manual-playtest before investing heavily in training.
5. Prefer behavior traces and baselines over reward-curve-only storytelling.
6. Keep claims conservative and evidence-backed.
7. Once the task family is locked, shift to implementation instead of reopening strategy.

## Engineering Principles

- `KISS`: prefer the simplest design that satisfies the locked task.
- `YAGNI`: do not add flexibility, abstractions, or features that the hackathon artifact does not need yet.
- `DRY`: avoid duplicated environment logic, reward logic, and schema definitions.
- `SSOT`: keep one canonical definition for the environment contract, reward semantics, and task wording.
- `SOLID`: keep modules focused, interfaces clear, and responsibilities separated.
- `Occam's Razor`: when two approaches work, prefer the one with fewer moving parts and fewer assumptions.
- `No Fallout`: keep refactors atomic. Do not leave stale schemas, stale consumers, or half-migrated task terms behind.

## Working Rules

- Do not broaden the task family beyond the single stellarator environment unless explicitly requested.
- Do not add broad “other sciences” claims to docs or demo copy unless there is real supporting evidence.
- Do not narrate hypotheses as validated facts.
- Do not add new tests during the hackathon unless the user explicitly requests them.
- Do not add complicated reward shaping until the simpler version has been tested against actual trajectories.
- Do not optimize notebook/training work ahead of local environment stability, remote environment stability, and baseline comparisons.
- Do not create new planning loops around decisions that are already locked in the SSOT docs unless a hard blocker appears.
- Treat supporting decision records as rationale, not as a fresh task queue.
- Do not leave fallout after contract changes. If a schema, action, reward, or task term changes, update dependent files in the same task so the repo stays coherent.
- Do not leave stale consumers behind after refactors. Task summaries, baselines, notebooks, and docs must either match the new contract or be deliberately updated.
- Do not swallow errors. No broad `except` blocks, `pass`, silent fallbacks, or ignored verifier/runtime failures unless the behavior is explicitly required and documented.

## Environment Contract Rules

Any change to the environment should preserve or deliberately update:

- observation schema
- action schema
- episode flow
- terminal conditions
- reward semantics

If you change one of these, update the corresponding documentation in the same task.

## Reward Design Rules

When changing reward logic:

- document the previous behavior
- identify the pathology or exploit
- describe the change in plain language
- preserve a readable mapping from behavior to incentive

Avoid opaque reward changes that improve a metric without making the environment easier to reason about.

## Manual Playtesting

Before calling a reward design “good,” verify that a human can:

- read the observation
- choose a plausible next action
- understand why the reward changed

If a human cannot act coherently from the observation, fix the environment contract before doing more training work.

## Repo Layout

- `fusion_lab/`: shared typed models and client code
- `server/`: environment server, task contract, physics loop
- `baselines/`: random and heuristic baselines
- `training/`: evaluation or training notebooks
- `demo/`: demo assets and scripts
- `docs/`: public-facing planning and submission docs

## Validation

For scoped changes, prefer the smallest relevant checks first.

## Environment and Tooling

- This repo uses `uv` as the package and environment manager.
- Prefer `uv sync`, `uv run`, and `uv lock` for local work, Northflank, and HF Space builds.
- Do not introduce `conda`-specific setup into this repo unless a real blocker forces it and the change is documented.

Current useful commands:

```bash
python3 -m py_compile fusion_lab/models.py fusion_lab/client.py server/environment.py server/app.py server/physics.py
```

For this hackathon repo, prefer smoke validation, manual playtesting, and runnable demos over adding test coverage.

## Git and Change Discipline

- Keep commits scoped to the task.
- Do not mix environment-contract edits with unrelated cleanup.
- Prefer small, reviewable increments.
- Work on the `main` branch unless explicitly asked to use a different branch.
- When explicitly asked to push, push directly to `origin/main` unless explicitly told otherwise.
- Branch names created for new work should use the `codex/` prefix.

## What Good Looks Like

A strong change in this repo usually does at least one of these:

- makes the environment contract clearer
- improves reproducibility
- adds or fixes a meaningful baseline
- strengthens the reward-iteration story
- makes the demo evidence easier to trust

If a change does not help one of those, question whether it belongs in this hackathon repo.

## **OpenEnv Hackathon Participant Guide**

Welcome to the [OpenEnv Hackathon](https://cerebralvalley.ai/e/open-env-hackathon), hacker! 👋 We’re thrilled to have you on board.

This guide is your all-in-one resource for the event, including schedule, rules, technical resources, problem statements, judging information, and more. Please read this carefully; most answers can be found here.

## **1. Join the [PyTorch Discord Server](https://discord.gg/VBcf6VtfY6)**

- You’ll be given a Hackathon Participant role by an admin, which will give you access to the hackathon-specific channels.

- Here, you’ll be able to interact with hackers and sponsors, introduce yourselves, and form teams (for a maximum team size of **3**).

- If you don't receive your role within **24 hours of joining,** please ping @CV.

- Please submit your Discord username below so we can grant you the role

[linkEmbed]

## **2. Location**

**|** Shack15 (1 Ferry Building, Suite 201, San Francisco CA. 94111)

- **Venue Access:** Shack15 is on the 2nd floor of the Ferry Building. Go up the Ferry Building elevator to the second floor, and turn left. Here you will see the main entrance to Shack15. 

- **Parking:** Parking near the Ferry Building is extremely limited. Consider parking farther out and taking Uber, Lyft, or Public Transportation. 

[youtube]

## **3. WiFi Information**

- **Username:** SHACK15_Members

- **Password:** M3mb3r$4L!f3

## **4. Hackathon Schedule**

**Saturday, March 7 (Outline)**

- **9:00 AM:** Doors Open •󠁏 Breakfast Served •󠁏 Team Formation

- **10:00 AM – 11:30AM**: Kick-off presentations with Meta, Hugging Face, UC Berkeley, CoreWeave, OpenPipe, Unsloth AI, Fleet AI, Mercor, Scaler AI Labs, Snorkel AI, Patronus AI, Halluminate and Scale AI

- **11:30 AM:** Hacking Begins

- **1:00 PM:** Lunch Served

- **6:00 PM:** Dinner Served

- **10:00 PM:** Doors Close •󠁏 Re-entry not permitted

**Sunday, March 8 (Outline)**

- **9:00AM:** Doors Open •󠁏 Breakfast Served

- **1:00PM:** Hacking stops •󠁏 Submissions Due

- **1:15PM:** First Round Judging Begins

- **2:00PM:** Lunch Served

- **3:00PM:** Final Round Judging Begins

- **4:00PM:** Winners Announced and Closing

- **5:00PM:** Doors Close

All presentation slides can be found here

[linkEmbed]

## **5. Hackathon and Submission Rules**

To keep things fair and aligned with our goals, all teams must follow these rules:

- **Open Source:** Please ensure your repository is public.

- **New Work Only:** All projects must be started from scratch during the hackathon with no previous work.

- **Team Size:** Teams may have up to **3** members.

- **Banned Projects:** Projects will be disqualified if they: violate legal, ethical, or platform policies, use code, data, or assets you do not have the rights to.

- Your project **must** use OpenEnv (stable release 0.2.1) deployed on HF spaces

- You must show a minimal training script for your environment using Unsloth or HF TRL in Colab.

- You must upload a **one minute** demo video to YouTube talking about your submission.

## **6. Hackathon Problem Statements**

Your project must address at least **one of the five** required problem statements.

- Some problem statements include **optional partner-sponsored sub-problem statements**, which are additional focus areas related to the main theme.

- Your project may align with **multiple partner sub-problem statements**, but you can only be **judged for a maximum of two**. Please **select up to two** when submitting.

- Projects that match these partner sub-problem statements are eligible for **extra partner prizes**, judged separately from the main track winners.

- Each partner sub-problem statement carries a prize of **$10,000 USD**.

**Statement 1: Multi-Agent Interactions**

Environments for this theme involve cooperation, competition, negotiation, and coalition formation. Learning from these environments will enable agents to model the beliefs and incentives of others in partially observable settings. This drives theory-of-mind reasoning and emergent strategic behavior.

- **Expected Outcome:** an environment that can be used to train multi-agent task handling in a LLM

- **Example Environments:** Market simulations, compute-allocation negotiations, collaborative puzzle worlds, mixed cooperative/competitive strategy games.

- **Partner Sub-Themes:**
  - **Fleet AI:** Scalable Oversight: Environments that train oversight agents to monitor, analyze, and explain the behavior of other AI agents operating in complex, multi-agent settings.
  - **Halluminate:** Multi-Actor Environments: Build a realistic environment where an agent interacts with and manages multiple actors (agents) to discover and achieve the task

**Statement 2: (Super) Long-Horizon Planning & Instruction Following**

You will build environments that require deep, multi-step reasoning with sparse or delayed rewards. After using these environments, the goal is to enable agents to decompose goals, track state over extended trajectories, and recover from early mistakes. The aim is to push beyond shallow next-token reasoning toward structured planning and durable internal representations. 

- **Expected Outcome:** an environment that can capture and improve LLM behaviour on challenging long horizon tasks that need long running sessions beyond context memory limits. 

- **Example Environments:** Research-planning simulators, large-scale codebase refactoring tasks, strategic resource management worlds, long-horizon logistics optimization, extremely complicated long-horizon instruction following (e.g., 300 instructions scattered around).

- **Partner Sub-Themes:**
  - **Mercor:** Make an environment with capped/uncapped rewards where frontier model rewards scale with token output.

  - **Scale AI:** Environments for long horizon workflows for non-code use cases within a business setting: focusing on either Sales, Project management, or HR & IT.

**Statement 3: World Modeling**

- **Statement 3.1: Professional Tasks:** Here you will develop environments that require real interaction with tools, APIs, or dynamic systems where the model is expected to do real hard work instead of exploiting short-cuts to arrive at the desired outcome. Learning from these environments will enable agents to maintain consistent internal state, update beliefs based on outcomes, and orchestrate multi-step workflows. The goal is to strengthen causal reasoning and persistent world models.
  - **Expected Outcome:** an environment capturing nuances of a defined partially observable world and improve LLM interaction with it

  - **Example Environments:** Dynamic browser/API ecosystems, enterprise applications, scientific workflow loops (papers → code → experiments), economic simulations with feedback, tool-discovery benchmarks.

  - **Partner Sub-Theme:**
    - **Scaler AI Labs:** Multi-App RL Environment for Enterprise Workflows: Create RL environments to demonstrate complex workflows, business rule nuances etc in a large enterprise

- **Statement 3.2: Personalized Tasks:** Here we will develop an environment that offers real personalized task handling, imagine replying to personal messages or handling dinner conflicts due to work conflicts, replying to tough emails. Think any personal assistant tasks.
  - **Expected Outcome:** An environment that gives the model a realistic simulation of handling personal tasks, conflicts and managing them as delegations

  - **Example Environments:** Executive Assistant Meeting Planner, Dinner and drive planning, email and message replying, etc

  - **Partner Sub-Theme:**
    - **Patronus AI:** Consumer Workflows with Schema Drift: Multi-step consumer workflow environments where the underlying data schemas, API contracts, and t&cs/policies/rules change.

**Statement 4: Self-Improvement**

The focus here is to create environments where agents can learn to generate new challenges, escalate difficulty, and improve through self-play or adaptive curricula. Rather than optimizing fixed tasks, the goal is for agents to learn to drive their own capability growth. The objective is recursive skill amplification.

- **Expected Outcome:** an environment for improving self-play of a LLM over a defined set of tasks

- **Example Environments:** Self-play negotiation arenas, auto-generated math/proof tasks, evolving coding competitions, adaptive RL curricula.

- **Partner Sub-Theme:**
  - **Snorkel AI:** Simulated Experts-in-the-Loop: Environment that simulates interactions with real subject-matter experts, with changing requirements / preferences.

**Statement 5: Wild Card - Impress Us!**

We do not want to limit your focus if your idea doesn’t fit the boxes above, we want and WILL reward out of box tasks, please be creative but remember to add submissions that meaningfully add value to LLM training on a certain task.

More details about each theme can be found here:

[linkEmbed]

## **7. CV Hackathon Winners**

[linkEmbed]

## **8. OpenEnv Provided Resources**

**Please read through the entire slideshow here. This includes:**

- OpenEnv Fundamentals, Architecture
- Local Dev, Docker, and HF Spaces Deployment
- OpenEnv in Practice
- Training (TRL & Unsloth)
- How-to-Access-Infrastructure (including GPU Request Form)

[linkEmbed]

## **9. Partner Provided Resources**

- **Unsloth AI Resources**
  - <https://unsloth.ai/docs/get-started/unsloth-notebooks#grpo-reasoning-rl-notebooks>
- **Mercor Resources**
  - Dataset: <https://huggingface.co/datasets/mercor/apex-agents>
  - Archipelago repo to run the eval: <https://github.com/Mercor-Intelligence/archipelago>
  - APEX-Agents paper: <https://arxiv.org/abs/2601.14242>
- **Hugging Face Resources**
  - **$30** in Compute and Inference Credits
  - To claim your credits, set up a HF account here: <https://huggingface.co/join>
  - Then, follow this link: <https://huggingface.co/openenv-community>
  - You will be granted **$30** of compute and inference credits!
- **Northflank Resources**
  - Each team gets an H100
  - Northflank instructions

    [linkEmbed]

  - Join the NorthFlank discord channel for any questions
  - Please fill out this form:

    [linkEmbed]

- **Cursor Resources**
  - **$50** in Cursor Credits, **apply below**

    [linkEmbed]

## **10. Judging & Submissions**

Judges will be taking place on **Sunday, March 8**. These judges are evaluating your **technical demos** in the following categories. _Show us what you have built_ to solve our problem statements. Please **do not** show us a presentation. We'll be checking to ensure your project was built **entirely during the event**; no previous work is allowed. 

**|** **Teams should submit [here](https://cerebralvalley.ai/e/openenv-hackathon-sf/hackathon/submit) when they have completed hacking.** In the submission form, you will have to upload a **one minute** demo video on YouTube talking about your submission. You must also show a minimal training script for your environment using Unsloth or HF TRL in Colab.

**Please ensure your project uses** use OpenEnv (stable release 0.2.1) deployed on HF spaces.

[linkEmbed]

**Judging Criteria**

- **Environment Innovation (40%) -** Is the environment novel, creative, or challenging? Does it meaningfully test the agent’s behavior?
- **Storytelling (30%) -** Does the team clearly explain the problem, environment, and agent behavior? Is the demo engaging and easy to follow?
- **Training Script Showing Improvement in Rewards (20%) -** Does the demo provide observable evidence of training progress (reward curves, metrics, or before/after behavior)? 
- **Reward and Training Pipeline Setup (10%) -** Is the reward logic coherent, and does the pipeline produce meaningful improvement in the agent’s inference (how it acts in the environment)?

**Judging Process**

**|** Judging proceeds in two rounds:

- Hackers will be assigned groups of judges; \~3 minutes to pitch followed by 1-2 minutes of Q/A

- The top **six** teams in ranking will get to demo on stage to a panel of judges; \~3 minutes to pitch followed by 2-3 minutes for Q/A.

## **11. Prizes**

- **1st Place:** $15,000 USD Cash

- **2nd Place:** $9,000 USD Cash

- **3rd Place:** $6,000 USD Cash
