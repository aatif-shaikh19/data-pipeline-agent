import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from groq import Groq
from app.core.config import settings

def main():
    client = Groq(api_key=settings.GROQ_API_KEY)
    models = client.models.list()
    print("Available Groq Models for your key:")
    for m in models.data:
        print(f" - {m.id}")

if __name__ == "__main__":
    main()
