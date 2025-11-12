# External Input: Anthropic Prompt Caching for Multi-Round Seminars

---
**Source:** ChatGPT
**Date:** 2025-10-07
**Conversation URL:** https://chatgpt.com/share/example-123 (hypothetical)
**Captured By:** @alex
**Related to:** Seminar Orchestration

---

## Context

I was exploring how to reduce costs for ActCLI's multi-round seminars. Currently, each round re-sends the full seminar context (domain knowledge, rules, participant list) which wastes tokens. I asked ChatGPT about Anthropic's prompt caching feature and whether it would fit our architecture.

The conversation helped me understand:
- How prompt caching works with Pydantic system prompts
- That our existing round structure is perfect for caching
- 90% cost reduction potential for rounds 2+

## Key Insights

- **Caching Strategy:** Mark system prompts with `cache_control: {type: "ephemeral"}`
- **Cache Hit Timing:** Caches last ~5 minutes, perfect for our 1-2 min round intervals
- **Backward Compatible:** Can add caching without breaking existing adapter interface
- **Cost Impact:** Round 1 normal cost, rounds 2-5 cost ~10% (90% savings)
- **Speed Bonus:** Cached tokens process ~10x faster, reducing latency

## Relevant Code/Designs

ChatGPT suggested this implementation pattern:

```python
# src/actcli/seminar/adapters/anthropic.py

class AnthropicAdapter(BaseAdapter):
    async def generate(self, prompt: str, context: SeminarContext) -> str:
        system_prompt = self._build_domain_knowledge()

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}  # Cache this!
                    }
                ]
            }
        ]

        # Add peer responses from previous round (also cacheable)
        if context.round > 1:
            peer_summary = self._format_peer_responses(context.peer_responses)
            messages.append({
                "role": "assistant",
                "content": peer_summary,
                "cache_control": {"type": "ephemeral"}  # Cache peer context
            })

        # User prompt is NOT cached (changes each round)
        messages.append({
            "role": "user",
            "content": prompt
        })

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            max_tokens=2048
        )

        # Log cache performance to audit trail
        self._log_cache_stats(response.usage)

        return response.content[0].text

    def _log_cache_stats(self, usage):
        """Track cache hits for cost analysis."""
        stats = {
            "cache_creation_tokens": usage.cache_creation_input_tokens,
            "cache_read_tokens": usage.cache_read_input_tokens,
            "regular_tokens": usage.input_tokens
        }
        # Append to audit.json for transparency
        self.audit.log_event("cache_stats", stats)
```

## Proposed Next Steps

- [x] **Incorporate into code** → Target: `src/actcli/seminar/adapters/anthropic.py`
- [ ] Update `docs/ARCHITECTURE.md` to document caching strategy
- [ ] Add cache performance metrics to audit trail
- [ ] Test with 5-round seminar to verify 90% cost reduction
- [ ] Consider adding cache stats to seminar reports

## Risk Assessment

**Security:** None - caching is Anthropic-side, no data leaves our control

**Compatibility:**
- ✅ Backward compatible - only affects Anthropic adapter
- ✅ Graceful fallback if caching unavailable (older API versions)
- ⚠️ Need to handle cache misses gracefully

**Complexity:**
- ✅ Low - just adding cache_control markers
- ⚠️ Need to track cache performance for transparency

**Dependencies:**
- Requires Anthropic Python SDK >=0.25.0 (check current version)
- No new external dependencies

**Cost Impact:**
- ✅ Positive! Reduces costs by 90% for multi-round seminars
- First round slightly higher (cache creation overhead ~10%)
- Net savings: ~70-80% for typical 3-round seminar

## Original Conversation

<details>
<summary>Full conversation transcript (click to expand)</summary>

**Me:** How does Anthropic's prompt caching work? I have a multi-model seminar system that runs 2-5 rounds with the same system prompt each time.

**ChatGPT:** Anthropic's prompt caching allows you to cache portions of your prompts that don't change between requests. Here's how it works:

1. **Cache Markers:** You add `cache_control: {type: "ephemeral"}` to any message content
2. **Cache Lifetime:** ~5 minutes (enough for your round intervals)
3. **Cost Savings:** Cached tokens cost 90% less than regular tokens
4. **Speed Boost:** Cached tokens process ~10x faster

For your seminar system, you'd want to cache:
- System prompt (domain knowledge, rules)
- Participant list
- Previous round responses (for rounds 2+)

Here's an example implementation:

[... rest of conversation with code examples ...]

**Me:** What about cache misses? How should I handle that?

**ChatGPT:** Cache misses happen when:
- Cache expired (>5 min since last use)
- Different content (even 1 char change invalidates cache)
- API region change (rare)

Handle gracefully:
- Don't assume cache hit in your cost estimates
- Log cache stats from response.usage for monitoring
- Fallback is just regular processing (no error)

[... more discussion ...]

</details>

---

## Triage Notes (filled by reviewer)

**Triaged By:** _[Will be filled by Gemini or human reviewer]_
**Triage Date:** _[Auto-filled during triage]_
**Category:** _[code-suggestions | architecture-ideas | docs-improvements | rejected]_
**Priority:** _[P0 - Critical | P1 - High | P2 - Medium | P3 - Low]_
**Assigned To:** _[@owner]_
**GitHub Issue:** _[#XXX if created]_

**Decision:**
_[Brief explanation of triage decision]_

**Implementation Notes:**
_[Any additional context for whoever implements this]_
