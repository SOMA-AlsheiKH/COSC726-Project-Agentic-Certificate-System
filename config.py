import os
from crewai import LLM

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"

os.environ["OPENAI_API_KEY"] = "ollama"  # <-- مفتاح وهمي، 
os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"  

local_llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    temperature=0.0,
    supports_function_calling=True,
    max_tokens=4096,
)
