# Superpower-10x

**10x Productivity Framework for Coding Agents**

An enhanced agentic development framework that amplifies coding agent productivity through systematic workflows, intelligent automation, and battle-tested development methodologies.

## Overview

Superpower-10x transforms chaotic coding sessions into systematic, predictable, high-quality software delivery through enforced workflows and intelligent automation. Built upon proven patterns from the [Superpowers](https://github.com/obra/superpowers) framework by Jesse Vincent.

## Key Features

- **10x Faster Implementation** - Automated task decomposition and execution
- **Zero-Defect Code** - Systematic verification pipelines with quality gates
- **Autonomous Operation** - Work for extended periods without human intervention
- **Intelligent Context Management** - Fresh context per task, clean reviews
- **Production-Ready Code** - Enforced TDD, security scans, and coverage checks

## The 10x Workflow Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ BRAIN-   │───▶│ DESIGN   │───▶│ PLAN     │───▶│ EXECUTE  │
│ STORM    │    │ REVIEW   │    │ CREATE   │    │ WITH TDD │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │                                               │
     │         ┌─────────────────────────────────────┘
     │         │
     ▼         ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ VERIFY   │◀───│ DEBUG    │◀───│ REVIEW   │◀───│ SUBAGENT │
│ & COMMIT │    │ SYSTEMATIC│   │ & REFINE │    │ ITERATE  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## Quick Start

### 1. Setup

```bash
cd your-project
./setup-superpower-10x.sh
```

### 2. Brainstorm

```bash
# Start a brainstorming session
superpower-10x:invoke brainstorming
```

### 3. Create Spec

Edit the generated spec at `docs/superpowers/specs/YYYY-MM-DD-[feature]-design.md`

### 4. Generate Plan

```bash
./scripts/auto-plan.sh my-feature
```

### 5. Execute

```bash
python scripts/subagent_executor.py docs/superpowers/plans/plan.md \
    --project . \
    --spec docs/superpowers/specs/design.md \
    --branch feature/my-feature
```

### 6. Finish

```bash
python scripts/finish_pipeline.py --branch feature/my-feature --option pr
```

## Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` | Initialize Superpower-10x in your project |
| `auto-plan.sh` | Generate implementation plans |
| `tdd-enforce.sh` | Enforce TDD discipline |
| `quality-gate.sh` | Run comprehensive quality checks |
| `subagent_executor.py` | Execute plans with orchestration |
| `debug_engine.py` | Systematic debugging sessions |
| `finish_pipeline.py` | Complete branch workflow |

## Core Principles

1. **Test First** - RED before GREEN before REFACTOR
2. **Systematic Over Ad-hoc** - Process over guessing
3. **Root Cause Over Symptom** - Fix once, fix right
4. **Verify Before Claim** - Evidence over assumptions
5. **Simplicity First** - YAGNI ruthlessly

## Philosophy

Superpower-10x enforces disciplined workflows that experienced developers know they should follow but often skip under pressure. By automating the process and providing intelligent tooling, it makes the "right" way the "easy" way.

## Based On

This framework is built upon and inspired by [Superpowers by obra/superpowers](https://github.com/obra/superpowers), incorporating:

- Brainstorming methodology
- TDD enforcement patterns
- Subagent-driven development
- Systematic debugging processes
- Plan-driven execution

## License

MIT License

## Author

Created by MiniMax Agent, inspired by Jesse Vincent's Superpowers framework.

## Contributing

Contributions welcome! Please follow the existing patterns and ensure all scripts have tests.
