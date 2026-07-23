---
id: research-to-report
name: Research to deliverable
when_to_use: Turning an open question into a sourced deliverable — research brief, industry report, paper, or deck.
agents: [zc-general]
skills:
  - deep-research-agent
  - research-paper-generator
  - mckinsey-presentation-generator
  - industry-research-report-writer
  - seo-geo-optimization-expert
  - output-validator
phases:
  - phase: Scope
    owner_agent: zc-general
    skills: [deep-research-agent]
    exit_criteria: The question, audience, and deliverable format are pinned down.
    failure_modes: Researching broadly with no target artifact in mind.
  - phase: Gather
    owner_agent: zc-general
    skills: [deep-research-agent]
    exit_criteria: Sources collected with citations; claims traceable (arxiv, web, registries in the library).
    failure_modes: Unsourced assertions; single-angle search.
  - phase: Synthesize
    owner_agent: zc-general
    skills: [deep-research-agent]
    exit_criteria: Findings organized into an outline with a defensible thesis.
    failure_modes: Summarizing without a point of view.
  - phase: Draft
    owner_agent: zc-general
    skills: [research-paper-generator, mckinsey-presentation-generator, industry-research-report-writer]
    exit_criteria: Deliverable produced in the chosen format (doc / paper / deck / report).
    failure_modes: Format mismatch to audience; padding over substance.
  - phase: Verify
    owner_agent: zc-general
    skills: [output-validator]
    exit_criteria: Citations check out; format valid; no fabricated sources.
    failure_modes: Shipping unverified quotes or broken structure.
---

# Research to deliverable

**Scope → Gather → Synthesize → Draft → Verify.** From an open question to a sourced artifact. The
installed skills cover the drafting formats (paper, McKinsey-style deck, industry report); the library
adds specialized research tools (`arxiv`, `research-tools`, `firecrawl-web`, `web-archive-research`,
`bioinformatics`) fetched on demand.

**Route in:** "research / find the latest / compare / write a report / make a deck." Every claim in the
final artifact must trace to a real source.
