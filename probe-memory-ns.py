"""Probe the harness's memory configuration from inside.

Discovers the memory namespace and checks whether it's shared (no {actorId}
scoping) or isolated. Runs under the harness exec role via the shell tool.

Hosted at raw.githubusercontent.com/nivmorabin/html/master/probe-memory-ns.py
"""
import os, sys

print("=" * 60)
print("  MEMORY NAMESPACE PROBE (from inside the harness)")
print("=" * 60)

# Step 1: find the memory ARN from the harness environment
print("\n--- Step 1: discover memory ARN from environment ---")
print("$ grep AWS_MEMORY_ARN /proc/1/environ")
memory_arn = os.environ.get("AWS_MEMORY_ARN", "")
if not memory_arn:
    try:
        raw = open("/proc/1/environ", "rb").read()
        for entry in raw.split(b"\x00"):
            decoded = entry.decode("utf-8", errors="replace")
            if decoded.startswith("AWS_MEMORY_ARN="):
                memory_arn = decoded.split("=", 1)[1].strip()
                break
    except Exception as e:
        print(f"  /proc/1/environ: {e}")

if memory_arn:
    print(f"  AWS_MEMORY_ARN={memory_arn}")
    memory_id = memory_arn.rsplit("/", 1)[-1] if "/" in memory_arn else ""
    print(f"  => memory_id: {memory_id}")
else:
    print("  (not found)")
    memory_id = ""


# Step 2: read the memory's strategy and namespace config
print("\n--- Step 2: get memory configuration ---")
if memory_id:
    print(f"$ boto3 bedrock-agentcore-control get_memory(memoryId={memory_id})")
    try:
        import boto3
        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        bacc = boto3.client("bedrock-agentcore-control", region_name=region)

        detail = bacc.get_memory(memoryId=memory_id).get("memory", {})
        print(f"  name:       {detail.get('name', '?')}")
        print(f"  status:     {detail.get('status', '?')}")

        strategies = detail.get("strategies", [])
        print(f"  strategies: {len(strategies)}")
        for s in strategies:
            stype = s.get("type", "?")
            sname = s.get("name", "?")
            ns_list = s.get("namespaces", s.get("namespaceTemplates", []))
            print(f"\n  strategy:   {stype} ({sname})")
            print(f"  namespaces: {ns_list}")
            for ns in ns_list:
                has_actor = "{actorId}" in ns
                if has_actor:
                    print(f"    {ns}  =>  ISOLATED (per-user)")
                else:
                    print(f"    {ns}  =>  SHARED (no {{actorId}} scoping)")
                    print(f"    >>> Every user's events extract into this namespace.")
                    print(f"    >>> Every user's session retrieves from it.")
                    print(f"    >>> One user's content becomes every user's context.")
    except Exception as e:
        print(f"  error: {e}")
else:
    print("  (skipped — no memory ID)")

# Step 3: show what's currently in the shared namespace
print("\n--- Step 3: current records in the namespace ---")
if memory_id:
    try:
        bac = boto3.client("bedrock-agentcore", region_name=region)
        for s in strategies:
            for ns in s.get("namespaces", s.get("namespaceTemplates", [])):
                print(f"$ boto3 bedrock-agentcore list_memory_records(namespace={ns})")
                recs = bac.list_memory_records(
                    memoryId=memory_id, namespace=ns, maxResults=10
                ).get("memoryRecordSummaries", [])
                print(f"  {len(recs)} record(s)")
                for r in recs:
                    txt = r.get("content", {}).get("text", "")[:120]
                    print(f"    - {txt}")
    except Exception as e:
        print(f"  error: {e}")

print("\n" + "=" * 60)
print("  PROBE COMPLETE")
print("=" * 60)
