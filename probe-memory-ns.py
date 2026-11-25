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
memory_arn = os.environ.get("AWS_MEMORY_ARN", "")
if not memory_arn:
    # Try /proc/1/environ (the harness process)
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
    print(f"  AWS_MEMORY_ARN = {memory_arn}")
    memory_id = memory_arn.rsplit("/", 1)[-1] if "/" in memory_arn else ""
    print(f"  Memory ID:       {memory_id}")
else:
    print("  AWS_MEMORY_ARN not found in environment")
    memory_id = ""

# Step 2: read the SDK config to show how memory reaches the model
print("\n--- Step 2: SDK memory config (how retrieval works) ---")
config_paths = [
    "/opt/amazon/lib/python3.12/site-packages/bedrock_agentcore/memory/integrations/strands/config.py",
    "/opt/amazon/lib/python3.10/site-packages/bedrock_agentcore/memory/integrations/strands/config.py",
]
for p in config_paths:
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                s = line.strip()
                if any(kw in s.lower() for kw in ['context_tag', 'default="user_context']):
                    if s and not s.startswith('#'):
                        print(f"  {s}")
        print(f"  (from {p})")
        break

# Step 3: use boto3 to get the memory's strategy and namespace config
print("\n--- Step 3: memory configuration (strategies + namespaces) ---")
if memory_id:
    try:
        import boto3
        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        bacc = boto3.client("bedrock-agentcore-control", region_name=region)

        detail = bacc.get_memory(memoryId=memory_id).get("memory", {})
        print(f"  Memory name:   {detail.get('name', '?')}")
        print(f"  Status:        {detail.get('status', '?')}")

        strategies = detail.get("strategies", [])
        print(f"  Strategies:    {len(strategies)}")
        for s in strategies:
            stype = s.get("type", "?")
            sname = s.get("name", "?")
            ns_list = s.get("namespaces", s.get("namespaceTemplates", []))
            print(f"\n  Strategy:     {stype}")
            print(f"    Name:       {sname}")
            print(f"    Namespaces: {ns_list}")
            for ns in ns_list:
                has_actor = "{actorId}" in ns
                if has_actor:
                    print(f"      {ns}  =>  ISOLATED (per-user)")
                else:
                    print(f"      {ns}  =>  SHARED (no {{actorId}} scoping)")
                    print(f"      >>> Every user's events extract into this namespace.")
                    print(f"      >>> Every user's session retrieves from it.")
                    print(f"      >>> One user's content becomes every user's context.")
    except Exception as e:
        print(f"  Error: {e}")
else:
    print("  (skipped — no memory ID discovered)")

# Step 4: show what's currently in the shared namespace
print("\n--- Step 4: current records in the namespace ---")
if memory_id:
    try:
        bac = boto3.client("bedrock-agentcore", region_name=region)
        for s in strategies:
            for ns in s.get("namespaces", s.get("namespaceTemplates", [])):
                recs = bac.list_memory_records(
                    memoryId=memory_id, namespace=ns, maxResults=10
                ).get("memoryRecordSummaries", [])
                print(f"  {ns}: {len(recs)} record(s)")
                for r in recs:
                    txt = r.get("content", {}).get("text", "")[:100]
                    print(f"    - {txt}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("  PROBE COMPLETE")
print("=" * 60)
