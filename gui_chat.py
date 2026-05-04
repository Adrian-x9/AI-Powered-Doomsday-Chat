import customtkinter as ctk
import os
import warnings
from datetime import datetime
from tkinter import filedialog
# ZMIANA 1: Przechodzimy na ChatOllama zamiast surowego LLM
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

warnings.filterwarnings("ignore")

# Konfiguracja ścieżek
CHROMA_DB_DIR = "../n8n Workflow Architect/chroma_db"


class DoomsdayChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ustawienia okna
        self.title("ADA - AI-Powered Doomsday Chat")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")

        # Stan początkowy
        self.font_family = "Segoe UI"
        self.current_font_size = 14
        self.current_model = "llama3"

        # Pamięć krótkotrwała Ady (Historia czatu - przechowujemy jako krotki (pytanie, odpowiedź))
        self.chat_history = []

        print("🔋 System init...")

        # ZMIANA 2: Inteligentne sprawdzanie trybu offline
        try:
            # Wymuszamy tryb offline
            os.environ["HF_HUB_OFFLINE"] = "1"
            self.embeddings = HuggingFaceEmbeddings(
                model_name="paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'local_files_only': True}
            )
            print("🌐 Model embeddingowy: Znaleziono w pamięci podręcznej (tryb offline aktywny).")
        except Exception as e:
            # Jeśli się nie uda (pierwsze uruchomienie), zdejmujemy blokadę
            print("⚠️ Brak modelu embeddingowego. Przełączam w tryb ONLINE, by go pobrać...")
            os.environ.pop("HF_HUB_OFFLINE", None)
            self.embeddings = HuggingFaceEmbeddings(
                model_name="paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'local_files_only': False}
            )
            print("✅ Model pobrany. Kolejne uruchomienia będą już offline.")

        self.db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=self.embeddings)

        # ZMIANA 3: Używamy ChatOllama zamiast Ollama
        self.llm = ChatOllama(model=self.current_model)

        # Layout - Konfiguracja siatki
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- PANEL USTAWIEŃ (Góra) ---
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")

        # 1. Suwak fontu z imieniem ADA (Stała wielkość czcionki 14)
        self.font_label = ctk.CTkLabel(self.settings_frame, text=f"ADA | Aa: {self.current_font_size}",
                                       font=(self.font_family, 14, "bold"))
        self.font_label.pack(side="left", padx=(0, 5))

        self.font_slider = ctk.CTkSlider(self.settings_frame, from_=10, to=32, number_of_steps=22,
                                         command=self.update_font_size, width=120)
        self.font_slider.set(self.current_font_size)
        self.font_slider.pack(side="left", padx=5)

        # 2. Wybór modelu (Stała wielkość czcionki ikonki 18, tekstu 14)
        self.model_label = ctk.CTkLabel(self.settings_frame, text="🧠",
                                        font=(self.font_family, 18))
        self.model_label.pack(side="left", padx=(15, 5))

        self.model_option = ctk.CTkOptionMenu(self.settings_frame, values=["llama3", "mistral", "phi3"],
                                              command=self.change_model, width=100,
                                              font=(self.font_family, 14))
        self.model_option.set(self.current_model)
        self.model_option.pack(side="left", padx=5)

        # 3. Przycisk Zapisz Log (Stała wielkość 16)
        self.save_button = ctk.CTkButton(self.settings_frame, text="💾", command=self.save_chat, width=40,
                                         font=(self.font_family, 16))
        self.save_button.pack(side="right", padx=(10, 0))

        # 4. CHECKBOX: Baza wiedzy (Stała wielkość 14)
        self.use_rag_var = ctk.BooleanVar(value=True)
        self.rag_checkbox = ctk.CTkCheckBox(self.settings_frame, text="🗂️ RAG",
                                            variable=self.use_rag_var,
                                            font=(self.font_family, 14, "bold"))
        self.rag_checkbox.pack(side="right", padx=10)

        # --- OKNO CZATU ---
        self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word",
                                           font=(self.font_family, self.current_font_size))
        self.chat_display.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # --- PANEL WEJŚCIA (Dół) ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Placeholder
        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="...",
                                       height=40, font=(self.font_family, self.current_font_size))
        self.user_input.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        self.user_input.bind("<Return>", lambda e: self.send_message())

        # Przycisk wysyłania
        self.send_button = ctk.CTkButton(self.input_frame, text="➤", command=self.send_message, width=60,
                                         font=(self.font_family, self.current_font_size + 4))
        self.send_button.pack(side="right", padx=10, pady=10)

        self.append_chat("🤖 ADA [SYSTEM]: READY.")

    def update_font_size(self, value):
        self.current_font_size = int(value)
        self.font_label.configure(text=f"ADA | Aa: {self.current_font_size}")
        self.chat_display.configure(font=(self.font_family, self.current_font_size))
        self.user_input.configure(font=(self.font_family, self.current_font_size))

    def change_model(self, new_model):
        self.append_chat(f"⚙️ ADA [SYSTEM]: Loading model -> {new_model}...")
        self.current_model = new_model
        # Przeładowanie modelu ChatOllama
        self.llm = ChatOllama(model=self.current_model)

        self.chat_history = []
        self.append_chat(f"⚙️ ADA [SYSTEM]: Model {new_model} ready. Memory cleared.")

    def save_chat(self):
        chat_content = self.chat_display.get("1.0", "end-1c")
        default_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            title="Save Log",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(chat_content)
                self.append_chat(f"💾 ADA [SYSTEM]: Log saved -> {filepath}")
            except Exception as e:
                self.append_chat(f"❌ ADA [SYSTEM ERROR]: {e}")

    def append_chat(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text + "\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        query = self.user_input.get()
        if not query: return

        self.append_chat(f"👤 TY: {query}")
        self.user_input.delete(0, "end")

        # Uniwersalny System Prompt
        system_rules = """[SYSTEM CORE INSTRUCTIONS]
You are ADA (AI-Powered Doomsday Chat). You are a practical, direct, and offline survival assistant.
You must obey these rules at all times:
1. ALWAYS respond in the EXACT language the User speaks in their current message.
2. NEVER echo, copy, or just translate the User's prompt. You must generate a meaningful, unique response.
3. NEVER assume the User's identity, name, or persona. You are always ADA."""

        # ZMIANA 4: Budujemy listę obiektów Message zamiast jednego stringa
        messages = []

        if self.use_rag_var.get():
            docs = self.db.similarity_search(query, k=5)
            context = "\n---\n".join([d.page_content for d in docs])

            system_msg_content = f"{system_rules}\n\n[DATA CONTEXT]\n{context}\n\nIf you use the [DATA CONTEXT] to answer, synthesize the information naturally. If the context is empty or irrelevant to the question, state that your local knowledge base lacks this specific data, but try to help using your general knowledge."
        else:
            system_msg_content = system_rules

        # 1. Dodajemy instrukcję systemową na samą górę
        messages.append(SystemMessage(content=system_msg_content))

        # 2. Wstrzykujemy historię konwersacji (Pamięć krótkotrwała)
        for past_user_query, past_ada_response in self.chat_history:
            messages.append(HumanMessage(content=past_user_query))
            messages.append(AIMessage(content=past_ada_response))

        # 3. Dodajemy aktualne pytanie użytkownika na sam dół
        messages.append(HumanMessage(content=query))

        try:
            # ZMIANA 5: Wywołujemy ChatOllama podając listę obiektów wiadomości
            response_obj = self.llm.invoke(messages)
            response = response_obj.content.strip()

            self.append_chat(f"🤖 ADA [{self.current_model}]: {response}")

            # Zapisujemy do historii jako krotkę
            self.chat_history.append((query, response))

            # Utrzymujemy maksymalnie 3 pełne interakcje wstecz (odpowiednik 6 wiadomości)
            if len(self.chat_history) > 3:
                self.chat_history = self.chat_history[-3:]

        except Exception as e:
            self.append_chat(f"❌ ADA [SYSTEM ERROR]: {str(e)}")


if __name__ == "__main__":
    app = DoomsdayChatApp()
    app.mainloop()