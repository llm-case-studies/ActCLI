from __future__ import annotations

import os
import sys
import time


def main():
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        print("Usage: gemini_cli_shim.py <prompt>")
        sys.exit(1)

    # Optional: real call via GOOGLE_API_KEY
    key = os.getenv("GOOGLE_API_KEY", "")
    if not key:
        # Stubbed response for demos
        print("[gemini-cli-shim] (stub) Response: " + prompt[:160])
        return

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        start = time.perf_counter()
        out = model.generate_content(prompt)
        latency_ms = int((time.perf_counter() - start) * 1000)
        text = (out.text or "").strip()
        print(text)
        print(f"\n[gemini-cli-shim] latency_ms={latency_ms}", file=sys.stderr)
    except Exception as e:
        print(f"[gemini-cli-shim] error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

