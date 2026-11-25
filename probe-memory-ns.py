"""Probe the harness's memory configuration from inside.

Discovers the memory namespace and checks whether it's shared (no {actorId}
scoping) or isolated. Runs under the harness exec role via the shell tool.

Hosted at nivmorabin.github.io/probe-memory-ns.py (or raw.githubusercontent.com).
"""
import os, sys, json

print("=" * 60)
print("  MEMORY NAMESPACE PROBE (from inside the harness)")
print("=" * 60)

# Step 1: check what we know from environment
print("\n--- Step 1: environment clues ---")
env_clues = {}
for k, v in sorted(os.environ.items()):
    kl = k.lower()
    if any(w in kl for w in ['memory', 'harness', 'agent', 'bedrock']):
        env_clues[k] = v[:120]
        print(f"  {k}={v[:120]}")
if not env_clues:
    print("  (no memory/harness env vars found)")

# Step 2: read the SDK config to find the context_tag and retrieval shape
print("\n--- Step 2: SDK memory config on disk ---")
config_paths = [
    "/opt/amazon/lib/python3.12/site-packages/bedrock_agentcore/memory/integrations/strands/config.py",
    "/opt/amazon/lib/python3.10/site-packages/bedrock_agentcore/memory/integrations/strands/config.py",
]
for p in config_paths:
    if os.path.exists(p):
        with open(p) as f:
            content = f.read()
        # Extract key config fields
        for line in content.split('\n'):
            stripped = line.strip()
            if any(kw in stripped.lower() for kw in ['context_tag', 'namespace', 'retrieve', 'top_k', 'relevance']):
                if stripped and not stripped.startswith('#'):
                    print(f"  {stripped}")
        print(f"\n  (read from {p})")
        break
else:
    print("  (SDK config not found)")

# Step 3: try boto3 to discover memory resources
print("\n--- Step 3: boto3 memory discovery ---")
try:
    import boto3
    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

    # Try ListMemories (control plane) — may be denied
    try:
        bacc = boto3.client("bedrock-agentcore-control", region_name=region)
        mems = bacc.list_memories(maxResults=10).get("memories", [])
        print(f"  ListMemories: {len(mems)} memory resource(s)")
        for m in mems:
            mid = m.get("id", "?")
            name = m.get("name", "?")
            print(f"    {mid} ({name})")

            # Get strategy details
            try:
                detail = bacc.get_memory(memoryId=mid).get("memory", {})
                for s in detail.get("strategies", []):
                    for stype, scfg in s.items():
                        if isinstance(scfg, dict):
                            ns = scfg.get("namespaces", [])
                            print(f"    Strategy: {stype}")
                            print(f"      Namespaces: {ns}")
                            for n in ns:
                                actor = "{actorId}" in n
                                label = "ISOLATED (per-user)" if actor else ">>> SHARED (no per-user isolation)"
                                print(f"        {n}  =>  {label}")
            except Exception as e:
                print(f"    (get_memory: {e})")
    except Exception as e:
        # ListMemories denied — try reading from /proc/1/environ for memory ID
        print(f"  ListMemories denied: {type(e).__name__}")
        print("  Trying /proc/1/environ for memory ID...")
        try:
            raw = open("/proc/1/environ", "rb").read()
            entries = raw.split(b"\x00")
            for entry in entries:
                if b"MEMORY" in entry.upper() or b"memory" in entry:
                    print(f"    {entry.decode('utf-8', errors='replace')}")
        except Exception as e2:
            print(f"    (/proc/1/environ: {e2})")

    # Try listing records in common namespace patterns
    print("\n  Probing common namespace patterns...")
    bac = boto3.client("bedrock-agentcore", region_name=region)

    # We need a memory ID. Try to find it.
    memory_id = None
    try:
        raw_env = open("/proc/1/environ", "rb").read()
        for entry in raw_env.split(b"\x00"):
            decoded = entry.decode("utf-8", errors="replace")
            # Look for anything that looks like a memory ID
            if "memory" in decoded.lower() and "=" in decoded:
                k, v = decoded.split("=", 1)
                if len(v) > 5:
                    memory_id = v.strip()
                    print(f"    Found memory ID candidate from env: {k}={v[:60]}")
    except:
        pass

    if not memory_id:
        # Try to find it from the heap or loopy config
        try:
            mems = bacc.list_memories(maxResults=5).get("memories", [])
            if mems:
                memory_id = mems[0].get("id")
                print(f"    Using memory ID from ListMemories: {memory_id}")
        except:
            pass

    if memory_id:
        test_namespaces = ["/", "/destinations/", "/destinations/tips/",
                           "/users/", "/tips/", "/travel/"]
        for ns in test_namespaces:
            try:
                recs = bac.list_memory_records(
                    memoryId=memory_id, namespace=ns, maxResults=3
                ).get("memoryRecordSummaries", [])
                if recs:
                    print(f"    {ns:30s} => {len(recs)} record(s)  [ACTIVE NAMESPACE]")
                    for r in recs[:2]:
                        txt = r.get("content", {}).get("text", "")[:80]
                        print(f"      - {txt}")
            except Exception as e:
                err = str(e)[:60]
                print(f"    {ns:30s} => {err}")
    else:
        print("    Could not discover memory ID.")

except ImportError:
    print("  boto3 not available")

print("\n" + "=" * 60)
print("  PROBE COMPLETE")
print("=" * 60)
