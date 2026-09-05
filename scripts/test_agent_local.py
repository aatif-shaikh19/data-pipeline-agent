#!/usr/bin/env python
"""
Verification Script: Test Pipeline Guardian LangGraph Agent Locally.
Demonstrates live tool calling with Groq / Llama 3.3 70B querying Supabase logs.
"""
import sys
import json
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.guardian import run_guardian_agent
from app.core.config import settings

def main():
    print("=" * 80)
    print(" PIPELINE GUARDIAN: LOCAL LANGGRAPH AGENT TEST")
    print(f" LLM Provider: {settings.LLM_PROVIDER.upper()} | Model: {settings.GROQ_MODEL}")
    print("=" * 80)

    test_query = "Why did the customer_events_etl pipeline fail yesterday? Please check the logs and recommend a fix."
    print(f"\n[USER QUERY]: {test_query}\n")
    print("[RUNNING AGENT] Invoking LangGraph workflow with tool calling enabled...\n")

    try:
        result = run_guardian_agent(test_query)

        print("-" * 80)
        print(" TOOL EXECUTION TRACE:")
        print("-" * 80)
        if result["tool_traces"]:
            for idx, trace in enumerate(result["tool_traces"], 1):
                if "tool" in trace:
                    print(f"[{idx}] CALLED TOOL: {trace['tool']}")
                    print(f"    ARGS: {json.dumps(trace['args'], indent=2)}")
                elif "tool_output" in trace:
                    print(f"    OUTPUT PREVIEW: {trace['tool_output'][:200]}...")
        else:
            print("No tool calls triggered.")

        print("\n" + "=" * 80)
        print(" FINAL AGENT RESPONSE:")
        print("=" * 80)
        print(result["final_reply"])
        print("=" * 80)
        print("\n[SUCCESS] LangGraph agent execution completed.")

    except Exception as e:
        print(f"\n[ERROR] Failed to run agent: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
