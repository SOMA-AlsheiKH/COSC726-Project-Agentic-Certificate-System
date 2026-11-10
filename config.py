import os
from crewai import LLM

os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"

# عشان CrewAI يشتغل مع LiteLLM بدون ما يطلب OPENAI_API_KEY حقيقي
os.environ.setdefault("OPENAI_API_KEY", "ollama")

# تعريف الـ LLM المحلي
local_llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    temperature=0.0,  # عشان الوكيل ما يألف، ودرجة إجابة ثابتة ودقيقة
    supports_function_calling=True,  # دي أهم سطر - هي البتخلي الوكيل ينادي الأدوات بجد
    max_tokens=4096,
)

# كده local_llm جاهز للاستيراد في main.py