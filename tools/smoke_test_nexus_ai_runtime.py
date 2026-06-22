
from src.core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus

runtime = NexusAIRuntime()

lily = {
    "uuid": "TEST-LILY",
    "name": "Lily",
    "use_case": "Individual",
    "abilities": ["Chat Companion", "Coding Assistant", "Research Assistant", "Creative Writer"],
    "libraries": ["Communication Library", "Project Memory Library", "Research Discipline Library", "Code Safety Library"],
    "guardrails": ["Ask before editing files", "Cite sources when researching"],
}

custom_writer = {
    "uuid": "CUSTOM-WRITER",
    "name": "Custom Writer",
    "use_case": "Individual",
    "abilities": ["Creative Writer"],
    "libraries": ["Communication Library"],
    "guardrails": [],
}

tests = [
    (lily, "chat with me about what Command Nexus can do"),
    (lily, "write a short product blurb for Command Nexus"),
    (lily, "help me fix a Python bug"),
    (lily, "research game mechanics for progression systems"),
    (custom_writer, "write a welcome paragraph for a customer"),
    (custom_writer, "help me fix a Python bug"),
]

print("COMMAND NEXUS AI RUNTIME SMOKE TEST")
print("=" * 60)

for meta, task in tests:
    name = meta["name"]
    result = runtime.run(task, ai_name=name, ai_uuid=meta["uuid"], ai_metadata=meta)
    print()
    print("AI:", name)
    print("TASK:", task)
    print("STATUS:", result.status.value)
    print("TITLE:", result.title)
    print("RESULT:", (result.result_text or "").replace("\n", " ")[:320])

print()
print("Smoke test finished.")
print("Expected:")
print("- Lily chat/writing/coding should complete or give safe local fallback.")
print("- Lily research should pause unless Brave Search + model backend are connected.")
print("- Custom Writer should write, but should pause if asked to code.")
