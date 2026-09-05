import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_groq import ChatGroq
from app.core.config import settings

def check_model(model_name: str):
    print(f"\n--- Testing model: {model_name} ---")
    try:
        llm = ChatGroq(model=model_name, api_key=settings.GROQ_API_KEY, temperature=0)
        res = llm.invoke("Hello, answer in 5 words.")
        print(f"[SUCCESS] {model_name} responded: {res.content}")
        return True
    except Exception as e:
        print(f"[FAILED] {model_name}: {e}")
        return False

def main():
    candidate_models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.6-27b",
        "groq/compound-mini",
    ]
    for m in candidate_models:
        check_model(m)

if __name__ == "__main__":
    main()
