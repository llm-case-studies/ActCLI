# ActCLI Expert Briefs

This folder holds initiative-first sprint packs for work that spans agents,
hosts, or validation lanes.

Use this process when a task should be handed from an orchestrator to an
implementer and then independently validated. Keep durable project memory here,
not in host-local agent chats.

Folder shape:

```text
docs/expert-briefs/
  INDEX.md
  LESSONS.md
  initiatives/<initiative>/
    README.md
    INDEX.md
    LESSONS.md
    active/<YYYY-MM-DD_slug>/
    completed/<YYYY-MM>/<YYYY-MM-DD_slug>/

testing/initiatives/<initiative>/<YYYY-MM-DD_slug>/
  request.md
  result.md
  evidence/
```

The first active initiative is `evaluation-path`: making ActCLI easy for a
Pricing R&D actuary to try safely in the first 10 minutes.
