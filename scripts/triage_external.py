#!/usr/bin/env python3
"""
Gemini-powered triage assistant for External-Inputs.

Usage:
    python scripts/triage_external.py intake/2025-09-30-topic.md
    python scripts/triage_external.py --all
    python scripts/triage_external.py --help
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import re

# Add src to path for ActCLI imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import google.generativeai as genai
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("\nInstall with: pip install google-generativeai rich")
    sys.exit(1)

console = Console()

# Gemini configuration
GEMINI_MODEL = "gemini-2.0-flash-exp"  # 2M token context, fast, cheap
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
EXTERNAL_INPUTS = PROJECT_ROOT / "External-Inputs"
INTAKE_DIR = EXTERNAL_INPUTS / "intake"
TRIAGED_DIR = EXTERNAL_INPUTS / "triaged"
TEMPLATES_DIR = EXTERNAL_INPUTS / "templates"

# Load triage criteria
TRIAGE_CHECKLIST = (TEMPLATES_DIR / "triage-checklist.md").read_text()

# ActCLI context for Gemini
ACTCLI_CONTEXT = """
ActCLI is a terminal-native toolkit for actuarial workflows with multi-model "roundtable" chat capabilities.

Core components:
- Seminar Orchestration: Multi-model coordination (Ollama, OpenAI, Anthropic, Gemini)
- Backend (Semhost): FastAPI server with WebSocket streaming
- CLI: Typer-based terminal interface with VSCode-style TUI
- MCP Integration: Model Context Protocol client
- Browser Extension: Generic chat bridge (experimental)
- Excel Tools: Legacy code inspection (planned)

Ownership areas:
- Core Platform (@alex): Backend, CLI, seminar, MCP
- Browser Extension (@Codex-BrExt, @Claude-BrExt)
- Refactoring: Technical debt elimination (TIER 0 complete)

Current priorities:
1. Anthropic prompt caching for multi-round seminars
2. Gate-0 triage with extended thinking
3. Browser extension E2E testing
4. Studio SPA scaffolding

See docs/STATUS.md and docs/ARCHITECTURE.md for full details.
"""


def get_next_triaged_number(category: str) -> int:
    """Get next available number for triaged file."""
    category_dir = TRIAGED_DIR / category
    if not category_dir.exists():
        return 1

    existing = list(category_dir.glob("*.md"))
    if not existing:
        return 1

    # Extract numbers from filenames like "001-topic.md"
    numbers = []
    for f in existing:
        match = re.match(r"(\d+)-", f.name)
        if match:
            numbers.append(int(match.group(1)))

    return max(numbers, default=0) + 1


def sanitize_content(content: str) -> tuple[str, list[str]]:
    """Remove sensitive data from content.

    Returns:
        (sanitized_content, list_of_redactions)
    """
    redactions = []

    # Common sensitive patterns
    patterns = [
        (r"(sk-[a-zA-Z0-9]{32,})", "API_KEY"),  # OpenAI-style keys
        (r"(AIza[a-zA-Z0-9_-]{35})", "GOOGLE_API_KEY"),  # Google API keys
        (r"-----BEGIN[^-]+KEY-----[^-]+-----END[^-]+KEY-----", "PRIVATE_KEY"),
        (r"password\s*[:=]\s*['\"]?([^'\"\s]+)", "PASSWORD"),
        (r"token\s*[:=]\s*['\"]?([^'\"\s]+)", "TOKEN"),
    ]

    sanitized = content
    for pattern, label in patterns:
        matches = re.finditer(pattern, sanitized, re.IGNORECASE | re.DOTALL)
        for match in matches:
            redactions.append(f"{label}: {match.group(0)[:20]}...")
            sanitized = re.sub(pattern, f"[REDACTED:{label}]", sanitized, flags=re.IGNORECASE | re.DOTALL)

    return sanitized, redactions


def analyze_with_gemini(intake_file: Path) -> dict:
    """Use Gemini to analyze intake and suggest triage."""

    if not GEMINI_API_KEY:
        console.print("[red]Error: GOOGLE_API_KEY environment variable not set[/red]")
        console.print("Set it with: export GOOGLE_API_KEY='your-key-here'")
        sys.exit(1)

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Read the intake file
    content = intake_file.read_text()

    # Sanitize first
    sanitized_content, redactions = sanitize_content(content)

    if redactions:
        console.print(f"[yellow]⚠️  Redacted {len(redactions)} sensitive item(s):[/yellow]")
        for r in redactions:
            console.print(f"   - {r}")

    # Construct prompt for Gemini
    prompt = f"""
You are a technical triage assistant for ActCLI, an actuarial workflow toolkit.

# Your Task
Analyze this external AI conversation import and recommend triage decisions.

# ActCLI Context
{ACTCLI_CONTEXT}

# Triage Criteria
{TRIAGE_CHECKLIST}

# Conversation to Analyze
{sanitized_content}

# Instructions
1. Read the full conversation carefully
2. Apply the 5 quality gates: Relevance, Novelty, Feasibility, Safety, Maintainability
3. Suggest ONE primary category: code-suggestions, architecture-ideas, docs-improvements, or rejected
4. Assign priority: P0 (critical), P1 (high), P2 (medium), P3 (low)
5. Recommend owner assignment
6. Flag any risks or concerns
7. Provide brief rationale

# Output Format (JSON)
Return ONLY valid JSON with this structure:
{{
  "passes_quality_gates": true/false,
  "quality_assessment": {{
    "relevance": "explanation",
    "novelty": "explanation",
    "feasibility": "explanation",
    "safety": "explanation",
    "maintainability": "explanation"
  }},
  "recommended_category": "code-suggestions|architecture-ideas|docs-improvements|rejected",
  "recommended_priority": "P0|P1|P2|P3",
  "recommended_owner": "@username",
  "risks_and_concerns": ["risk1", "risk2"],
  "rationale": "1-2 sentence explanation of recommendation",
  "suggested_next_steps": ["action1", "action2"],
  "github_issue_title": "Brief title if code-suggestions or architecture-ideas",
  "confidence": "high|medium|low"
}}

Analyze now:
"""

    console.print("[cyan]🤖 Analyzing with Gemini...[/cyan]")

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent analysis
                max_output_tokens=2048,
            )
        )

        # Extract JSON from response
        text = response.text.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:].strip()

        analysis = json.loads(text)
        return analysis

    except Exception as e:
        console.print(f"[red]Error during Gemini analysis: {e}[/red]")
        console.print(f"[yellow]Response: {response.text[:500] if 'response' in locals() else 'N/A'}[/yellow]")
        sys.exit(1)


def display_analysis(analysis: dict):
    """Display Gemini's analysis in a nice format."""

    # Quality assessment
    qa = analysis["quality_assessment"]
    console.print("\n[bold]Quality Gates Assessment:[/bold]")
    for gate, explanation in qa.items():
        console.print(f"  • {gate.title()}: {explanation}")

    # Recommendation
    console.print(f"\n[bold]Recommendation:[/bold]")
    console.print(f"  Category: [cyan]{analysis['recommended_category']}[/cyan]")
    console.print(f"  Priority: [yellow]{analysis['recommended_priority']}[/yellow]")
    console.print(f"  Owner: {analysis['recommended_owner']}")
    console.print(f"  Confidence: {analysis['confidence']}")

    # Rationale
    console.print(f"\n[bold]Rationale:[/bold]")
    console.print(f"  {analysis['rationale']}")

    # Risks
    if analysis.get("risks_and_concerns"):
        console.print(f"\n[bold red]⚠️  Risks/Concerns:[/bold red]")
        for risk in analysis["risks_and_concerns"]:
            console.print(f"  • {risk}")

    # Next steps
    console.print(f"\n[bold]Suggested Next Steps:[/bold]")
    for step in analysis.get("suggested_next_steps", []):
        console.print(f"  - [ ] {step}")

    # GitHub issue title if applicable
    if analysis.get("github_issue_title") and analysis["recommended_category"] in ["code-suggestions", "architecture-ideas"]:
        console.print(f"\n[bold]Suggested GitHub Issue:[/bold]")
        console.print(f"  Title: {analysis['github_issue_title']}")


def triage_file(intake_file: Path, auto_approve: bool = False):
    """Triage a single intake file with Gemini assistance."""

    console.print(f"\n[bold]Triaging:[/bold] {intake_file.name}")
    console.print("─" * 60)

    # Analyze with Gemini
    analysis = analyze_with_gemini(intake_file)

    # Display results
    display_analysis(analysis)

    # Human decision
    if not auto_approve:
        console.print("\n[bold]Review Gemini's recommendation:[/bold]")
        accept = Confirm.ask("Accept this triage recommendation?", default=True)

        if not accept:
            console.print("[yellow]Manual triage needed. Options:[/yellow]")
            console.print("1. Edit the intake file and re-run triage")
            console.print("2. Manually move to triaged/ with your own assessment")
            return

    # If rejected, move to rejected/ with rationale
    if analysis["recommended_category"] == "rejected":
        target_dir = TRIAGED_DIR / "rejected"
        target_dir.mkdir(parents=True, exist_ok=True)
        num = get_next_triaged_number("rejected")

    else:
        target_dir = TRIAGED_DIR / analysis["recommended_category"]
        target_dir.mkdir(parents=True, exist_ok=True)
        num = get_next_triaged_number(analysis["recommended_category"])

    # Generate filename
    topic = intake_file.stem.split("-", 3)[-1] if "-" in intake_file.stem else intake_file.stem
    target_file = target_dir / f"{num:03d}-{topic}.md"

    # Read original content and append triage notes
    content = intake_file.read_text()

    # Add triage notes
    triage_notes = f"""

---

## Triage Notes (AI-Assisted)

**Triaged By:** @alex (with Gemini assistance)
**Triage Date:** {datetime.now().strftime('%Y-%m-%d')}
**Category:** {analysis['recommended_category']}
**Priority:** {analysis['recommended_priority']}
**Assigned To:** {analysis['recommended_owner']}
**Gemini Confidence:** {analysis['confidence']}

**Decision:**
{analysis['rationale']}

**Quality Gates:**
- Relevance: {analysis['quality_assessment']['relevance']}
- Novelty: {analysis['quality_assessment']['novelty']}
- Feasibility: {analysis['quality_assessment']['feasibility']}
- Safety: {analysis['quality_assessment']['safety']}
- Maintainability: {analysis['quality_assessment']['maintainability']}

**Next Steps:**
{chr(10).join(f'- [ ] {step}' for step in analysis.get('suggested_next_steps', []))}

{"**Risks/Concerns:**" if analysis.get('risks_and_concerns') else ""}
{chr(10).join(f'- {risk}' for risk in analysis.get('risks_and_concerns', []))}
"""

    # Write triaged file
    target_file.write_text(content + triage_notes)

    console.print(f"\n[green]✅ Triaged successfully![/green]")
    console.print(f"   Moved to: {target_file.relative_to(PROJECT_ROOT)}")

    # Suggest GitHub issue creation
    if analysis["recommended_category"] in ["code-suggestions", "architecture-ideas"]:
        if Confirm.ask("\nCreate GitHub issue now?", default=False):
            create_github_issue(target_file, analysis)


def create_github_issue(triaged_file: Path, analysis: dict):
    """Create GitHub issue for triaged item."""

    issue_body = f"""
From external AI conversation triage.

**Source:** {triaged_file.relative_to(PROJECT_ROOT)}
**Category:** {analysis['recommended_category']}
**Priority:** {analysis['recommended_priority']}

## Rationale
{analysis['rationale']}

## Next Steps
{chr(10).join(f'- [ ] {step}' for step in analysis.get('suggested_next_steps', []))}

{"## Risks" if analysis.get('risks_and_concerns') else ""}
{chr(10).join(f'- {risk}' for risk in analysis.get('risks_and_concerns', []))}

See full analysis in `{triaged_file.relative_to(PROJECT_ROOT)}`
"""

    import subprocess

    try:
        # Use GitHub CLI
        cmd = [
            "gh", "issue", "create",
            "--title", analysis.get("github_issue_title", f"[External Input] {triaged_file.stem}"),
            "--body", issue_body,
            "--label", "external-input",
            "--assignee", analysis["recommended_owner"].replace("@", "")
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            console.print(f"[green]✅ GitHub issue created: {result.stdout.strip()}[/green]")
        else:
            console.print(f"[red]Failed to create issue: {result.stderr}[/red]")
            console.print("\n[yellow]Manual creation command:[/yellow]")
            console.print(f"gh issue create --title \"{analysis.get('github_issue_title', triaged_file.stem)}\" \\")
            console.print(f'  --body "See {triaged_file.relative_to(PROJECT_ROOT)}" \\')
            console.print(f"  --label external-input --assignee {analysis['recommended_owner'].replace('@', '')}")

    except FileNotFoundError:
        console.print("[yellow]GitHub CLI not installed. Install with: brew install gh[/yellow]")
        console.print("\nOr create issue manually at: https://github.com/llm-case-studies/ActCLI/issues/new")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Triage external AI conversation inputs with Gemini assistance"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Intake file to triage (e.g., intake/2025-09-30-topic.md)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Triage all pending intake files"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve Gemini's recommendations without prompting"
    )

    args = parser.parse_args()

    # Check for API key
    if not GEMINI_API_KEY:
        console.print("[red]Error: GOOGLE_API_KEY environment variable not set[/red]")
        console.print("\nSet it with:")
        console.print("  export GOOGLE_API_KEY='your-key-here'")
        console.print("\nOr add to ~/.bashrc or ~/.zshrc for persistence")
        sys.exit(1)

    # Validate paths
    if not INTAKE_DIR.exists():
        console.print(f"[red]Error: {INTAKE_DIR} does not exist[/red]")
        console.print("Run this script from ActCLI project root")
        sys.exit(1)

    # Triage all or single file
    if args.all:
        intake_files = list(INTAKE_DIR.glob("*.md"))
        if not intake_files:
            console.print("[yellow]No intake files to triage[/yellow]")
            return

        console.print(f"[cyan]Found {len(intake_files)} intake file(s) to triage[/cyan]")

        for intake_file in intake_files:
            triage_file(intake_file, args.auto_approve)
            console.print("\n" + "=" * 60 + "\n")

    elif args.file:
        intake_file = Path(args.file)
        if not intake_file.exists():
            # Try prepending INTAKE_DIR
            intake_file = INTAKE_DIR / args.file

        if not intake_file.exists():
            console.print(f"[red]Error: File not found: {args.file}[/red]")
            sys.exit(1)

        triage_file(intake_file, args.auto_approve)

    else:
        parser.print_help()
        console.print("\n[yellow]Tip: List pending intakes with: ls External-Inputs/intake/[/yellow]")


if __name__ == "__main__":
    main()
