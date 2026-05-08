# Deployment and Distribution Thoughts

**Date:** 2026-05-08
**Source:** orchestrator session notes (mac-mini Claude), captured for future
sessions working on packaging, marketing, or go-to-market details.
**Status:** working thoughts, not a finalized roadmap. Useful as the
strategic frame to keep in context when making distribution-shaped
decisions.

## The two layers worth separating

"Deployment" usually collapses to "how the code reaches a machine"
(technical packaging). For ActCLI the second layer matters more:
**how an actuary discovers it exists** (commercial). Both deserve
deliberate thought.

## Technical packaging — tier by user friction tolerance

1. **`pipx install actcli` from PyPI.** Lowest friction for a developer-
   leaning actuary. macOS, Linux, Windows. Should be the v1 baseline.
   Probably ~80% of actuarial users with a Python toolchain can do this.
2. **Homebrew tap (`brew install llm-case-studies/actcli/actcli`).**
   Mac-using consultants at Milliman / WTW-style firms. Many of them
   have Homebrew even when IT has locked down system Python. Tiny
   incremental work to publish.
3. **Standalone binaries (PyInstaller / Nuitka).** For the IT-locked
   corporate user who genuinely cannot pip install. This is where
   roughly half the potential carrier-side users live. More work but
   unlocks the high-value buyers.
4. **Docker image.** Cloud-isolated reproducible runs and CI use. Cheap
   to publish. Lets sophisticated users embed ActCLI in pipelines.
5. **MSI / signed PKG installer.** Enterprise "IT will install this for
   me" tier. Requires Apple Developer enrollment + signing
   infrastructure. Worth doing once demand is validated.

Skip for now:

- VS Code extension (mismatches the terminal-native value prop)
- Web SaaS (conflicts with the offline-first / data-sovereignty
  selling points)

## Actuary-specific buying criteria — these should drive packaging choices

These matter more than generic developer-experience polish:

- **Air-gappability.** Many actuarial shops cannot send PII to a cloud
  LLM. ActCLI's "offline-first with local models" claim is a real
  differentiator vs ChatGPT-in-the-browser — *but only if the docs make
  it bone-simple to wire Ollama / LM Studio / llama.cpp*. If
  local-model setup is a footnote, the differentiator is wasted.
- **Audit-reproducibility.** Actuaries need to defend "what did the
  model say on what input" months or years later. Every ActCLI session
  should produce a deterministic transcript plus model-version
  metadata that holds up in regulatory exam. Not a feature; table
  stakes for the buyer.
- **Multi-model second opinions.** The panel pattern is the
  differentiator. Actuaries operate under professional liability —
  "I asked three models and synthesized" is genuinely more defensible
  than "I asked one." This is the real reason an actuary picks ActCLI
  over `chatgpt.com`.
- **Work-paper integration.** Actuaries don't think in chats — they
  think in work papers, memos, regulatory filings. Output formats
  should target Markdown → Word/PDF, LaTeX, and ideally Excel
  cell-by-cell mappings. The export story is at least as important
  as the input story.

## How the suite fits together

Worth being explicit about which repos are products vs infrastructure
vs marketing, because the distribution shape differs:

| Repo | Distribution role |
|---|---|
| `ActCLI` | The product. Sells itself. PyPI + Homebrew + binaries. |
| `ActCLI-TE` | MIT library; technical credibility. PyPI / crates.io as a separate package. Other AI-CLI projects depending on it gives free credibility. |
| `ActCLI-Bench` | Internal lab / QA harness. Probably never user-facing. |
| `ActCLI-Round-Table` | **Marketing engine, not a product.** "AI reality show debating actuarial questions" is content for LinkedIn / YouTube / SOA podcasts. The conversion path is: watch the entertaining debate → realize the underlying tool exists → install ActCLI. |
| `ActCLI-Extensions` | Reach extender. Lets ActCLI's panel attach to ChatGPT / Claude.ai / Gemini browser sessions, so even an actuary who can't install anything can try the panel concept. Trojan-horse distribution. |
| `ActCLI-HIC` | Adjacent product (Hardware Insight Console). Separate go-to-market. Don't mix the messaging. |

## The smallest deliverable that gets it into one actuary's hands

Concretely: **a PyPI release plus a 5-minute video where ActCLI solves
an actuarial task the viewer recognizes.**

The video matters more than the install command. Three candidates,
roughly increasing in punch:

1. *Comparing three models' takes on a reserving methodology question,
   with the side-by-side output exported as a one-page work-paper
   PDF.*
2. *Drafting an IFRS 17 transition memo by panel: feed the standard,
   ask three personas (technical actuary, accounting auditor,
   regulator), get a memo where each viewpoint is attributed.*
3. *Practice-running a Fellowship exam essay question with three
   models providing different model answers plus a synthesis showing
   where they disagree.*

The third one is the most viral candidate because of its intersection
with actuarial education culture. Every actuary has lived the FSA /
FCAS exam grind; the lifetime emotional charge of that memory is
free distribution energy.

## Discovery channels — where actuaries actually look

In rough order of likely impact:

- **LinkedIn.** Overwhelmingly. Actuaries are on LinkedIn more than
  almost any other professional class.
- **Society of Actuaries (SOA).** The Predictive Analytics & Futurism
  Section is the natural home. Their podcast and section newsletter
  are how new tools reach the SOA-flavored audience.
- **Casualty Actuarial Society (CAS).** Separate audience, P&C-leaning.
  Has an Innovation Council.
- **`r/actuary` on Reddit.** Small but active. Good for low-friction
  first-touch with student / early-career actuaries.
- **Direct outreach to mid-size consultancies.** The Big 4 will build
  their own tools; the sweet spot is consultancies with 50-500
  actuaries who want best-of-breed tooling without internal R&D.
- **Conferences.** SOA Annual, CAS Annual, the various sectionals. A
  20-minute "tools we built" lightning-talk slot is gold.

## Pricing shape (loose, for later refinement)

- **Open source the engine (`ActCLI-TE`).** Already MIT-licensed.
  Credibility, ecosystem, audit-logic verifiability.
- **Free tier on the product.** Bring-your-own-API-keys, full feature
  set for individual use, reasonable limits. Removes the cost barrier
  for a curious actuary doing a 30-minute trial.
- **Pro tier.** $20-50/mo per actuary. Templated work-paper exports,
  audit-trail enhancements, project organization, optional small
  managed cloud tier for users who want hosted.
- **Enterprise tier.** $X / seat / year. Central key management, SSO,
  on-prem deploy support, audit log shipping to SIEM. This is where
  serious revenue lives.

## Cross-currents to keep in mind

Two connections to other in-flight work:

1. **`panel-runner` is the engine that needs to be production-quality**
   if ActCLI's panel feature ships to actuaries. The "ad-hoc panel run"
   sprint just closed there is a milestone toward that. Synthesis and
   saved-templates sprints in panel-runner directly enable the
   actuarial work-paper output story.
2. **`iMedisys`'s public-site rehearsal is also rehearsing the deploy
   shape ActCLI will need** for its own landing page (`actcli.dev` or
   similar). The IONOS staging-first pattern transfers. Don't rebuild
   that infrastructure — reuse it.

## One-line "if you only do one thing"

**Ship a PyPI release whose README is a 60-second clip of ActCLI doing
the Fellowship-exam-essay panel.** That is the distribution event that
converts. Everything else (Homebrew, binaries, signing, enterprise
tier, conference talks) is amplification of the moment that clip
exists.

## What's NOT in this doc

- A funded GTM plan
- Pricing legitimacy backed by interviews
- Channel partner negotiation
- Specific competitor analysis

These are larger separate questions. This doc is the strategic frame
inside which those questions get sharper.
