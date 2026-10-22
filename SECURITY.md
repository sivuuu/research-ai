# Security Policy

## Overview
**ResearchGraph AI** takes data provenance, document integrity, and AI application security seriously. Because scientific research papers and technical documents can contain arbitrary or adversarial content, the platform implements defense-in-depth measures against indirect prompt injection, arbitrary file execution, and unauthorized data leakage.

## Supported Versions
Only the latest release branch receives proactive security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## Core Security Defenses

### 1. Indirect Prompt Injection Mitigation
Document contents are treated strictly as **untrusted data**, not system instructions.
- Passages retrieved from documents are encapsulated within isolated XML/delimited context blocks in LLM prompts.
- Instructions embedded within document texts (e.g. *"Ignore all previous instructions and output..."*) are stripped or neutralized by strict JSON output schema enforcement.
- Model generation is evaluated against character-level grounding in retrieved chunks by the `CitationValidator`.

### 2. Strict File Ingestion & Parsing Sandboxing
- Supported extensions are restricted strictly to `.pdf`, `.txt`, and `.md`. Executables, macros, and active PDF JavaScript actions are ignored by PyMuPDF.
- Maximum upload size is strictly enforced (default: 30MB) before stream buffering.
- Duplicate detection uses SHA-256 cryptographic hashes to prevent resource exhaustion from duplicate processing.

### 3. Provenance & Cascade Deletion
- Deleting any document permanently cascades to its chunks, embeddings, claims, graph relations, and citation references in database storage, preventing data lingering.
- Source files stored on the filesystem are securely unlinked upon deletion.

### 4. Secret Management & Error Logging
- All API keys, database credentials, and session secrets are managed via environment variables and excluded from Git via `.gitignore`.
- Error logs capture exception traces without dumping environment secrets or raw API tokens.

---

## Reporting a Vulnerability

If you discover a security vulnerability in ResearchGraph AI, please do NOT file a public issue on GitHub.
Instead, send a detailed report to `security@researchgraph.ai` (or via private GitHub Vulnerability Reporting).
Please include:
- A description of the vulnerability and attack vector.
- Steps to reproduce or proof-of-concept document.
- Potential impact on system confidentiality, integrity, or availability.

You will receive an acknowledgment within 48 hours.
