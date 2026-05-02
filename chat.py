import warnings
import os
# Używamy tylko stabilnych, podstawowych komponentów
from langchain_community.llms import Ollama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

warnings.filterwarnings("ignore")

# Ścieżka do bazy z poprzedniego projektu
# Upewnij się, że ten folder istnieje w tej lokalizacji!
CHROMA_DB_DIR = "../n8n Workflow Architect/chroma_db"


def main():
    print("🔋 Tryb Survival: Aktywny")

    # 1. Inicjalizacja Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

    # 2. Ładowanie bazy
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"❌ BŁĄD: Nie znaleziono bazy w {CHROMA_DB_DIR}")
        return

    print("🗄️ Podłączanie lokalnego magazynu wiedzy...")
    db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

    # 3. Budzenie lokalnego mózgu
    print("🧠 Inicjalizacja modelu Llama 3 (via Ollama)...")
    llm = Ollama(model="llama3")

    print("\n" + "☢️ " * 15)
    print(" AI-POWERED DOOMSDAY CHAT ")
    print("      STATUS: OFFLINE     ")
    print("☢️ " * 15)

    while True:
        query = input("\n[O co pytasz w czasie awarii?]: ")
        if query.lower() in ['exit', 'quit', 'q']: break

        # RĘCZNY RAG (Manualny proces)
        # Krok A: Szukamy kontekstu w bazie wektorowej
        results = db.similarity_search(query, k=2)
        context = "\n---\n".join([res.page_content for res in results])

        # Krok B: Budujemy czysty prompt dla LLM
        prompt = f"""ZADANIE: Jesteś asystentem przetrwania. Odpowiedz na pytanie na podstawie KONTEKSTU.
Jeżeli w KONTEKŚCIE nie ma odpowiedzi, użyj własnej wiedzy, ale zaznacz to.

KONTEKST Z TWOJEJ BAZY:
{context}

PYTANIE UŻYTKOWNIKA: {query}

TWOJA ODPOWIEDŹ:"""

        print("\n[AI ANALIZUJE DANE...]\n")

        # Krok C: Generowanie odpowiedzi
        try:
            # .invoke() to obecnie najstabilniejsza metoda w LangChain
            response = llm.invoke(prompt)
            print(f"[DOOMSDAY AI]: {response}")
        except Exception as e:
            print(f"❌ Błąd silnika Ollama: {e}")
            print("Upewnij się, że aplikacja Ollama jest uruchomiona (ikona w trayu)!")


if __name__ == "__main__":
    main()