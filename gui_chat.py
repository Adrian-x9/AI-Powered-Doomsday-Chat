import customtkinter as ctk
import os
import warnings
from datetime import datetime
from tkinter import filedialog
from langchain_community.llms import Ollama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

warnings.filterwarnings("ignore")

# 1. TWARDE WYMUSZENIE TRYBU OFFLINE DLA HUGGING FACE
os.environ["HF_HUB_OFFLINE"] = "1"

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

        # Pamięć krótkotrwała Ady (Historia czatu)
        self.chat_history = []

        # Inicjalizacja silnika AI
        print("🔋 System init...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'local_files_only': True}  # Zabezpieczenie przed pingowaniem serwera
        )
        self.db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=self.embeddings)
        self.llm = Ollama(model=self.current_model)

        # Layout - Konfiguracja siatki
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- PANEL USTAWIEŃ (Góra) ---
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")

        # 1. Suwak fontu z imieniem ADA
        self.font_label = ctk.CTkLabel(self.settings_frame, text=f"ADA | Aa: {self.current_font_size}",
                                       font=(self.font_family, self.current_font_size, "bold"))
        self.font_label.pack(side="left", padx=(0, 5))

        self.font_slider = ctk.CTkSlider(self.settings_frame, from_=10, to=32, number_of_steps=22,
                                         command=self.update_font_size, width=120)
        self.font_slider.set(self.current_font_size)
        self.font_slider.pack(side="left", padx=5)

        # 2. Wybór modelu
        self.model_label = ctk.CTkLabel(self.settings_frame, text="🧠",
                                        font=(self.font_family, self.current_font_size + 4))
        self.model_label.pack(side="left", padx=(15, 5))

        self.model_option = ctk.CTkOptionMenu(self.settings_frame, values=["llama3", "mistral", "phi3"],
                                              command=self.change_model, width=100,
                                              font=(self.font_family, self.current_font_size))
        self.model_option.set(self.current_model)
        self.model_option.pack(side="left", padx=5)

        # 3. Przycisk Zapisz Log
        self.save_button = ctk.CTkButton(self.settings_frame, text="💾", command=self.save_chat, width=40,
                                         font=(self.font_family, self.current_font_size + 2))
        self.save_button.pack(side="right", padx=(10, 0))

        # 4. CHECKBOX: Baza wiedzy (zmniejszony border_spacing dla mniejszego odstępu)
        self.use_rag_var = ctk.BooleanVar(value=True)
        self.rag_checkbox = ctk.CTkCheckBox(self.settings_frame, text="🗂️ RAG",
                                            variable=self.use_rag_var,
                                            font=(self.font_family, self.current_font_size, "bold"))
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

        self.append_chat("🤖 ADA [SYSTEM]: OFFLINE MODE ACTIVE. READY.")

    def update_font_size(self, value):
        self.current_font_size = int(value)
        self.font_label.configure(text=f"ADA | Aa: {self.current_font_size}",
                                  font=(self.font_family, self.current_font_size, "bold"))
        self.model_label.configure(font=(self.font_family, self.current_font_size + 4))
        self.model_option.configure(font=(self.font_family, self.current_font_size))
        self.save_button.configure(font=(self.font_family, self.current_font_size + 2))
        self.rag_checkbox.configure(font=(self.font_family, self.current_font_size, "bold"))
        self.chat_display.configure(font=(self.font_family, self.current_font_size))
        self.user_input.configure(font=(self.font_family, self.current_font_size))
        self.send_button.configure(font=(self.font_family, self.current_font_size + 4))

    def change_model(self, new_model):
        self.append_chat(f"⚙️ ADA [SYSTEM]: Loading model -> {new_model}...")
        self.current_model = new_model
        self.llm = Ollama(model=self.current_model)

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

        # 1. Budowanie czytelnego tekstu historii
        history_str = ""
        if self.chat_history:
            history_str = "--- CHAT HISTORY ---\n" + "\n".join(self.chat_history) + "\n--------------------\n"

        # 2. Żelazne zasady z odpowiednim "kagańcem"
        system_rules = """System: You are Ada, a helpful AI survival assistant.
CRITICAL RULES:
1. DETECT THE LANGUAGE OF THE 'CURRENT MESSAGE'. YOU MUST RESPOND IN THAT EXACT LANGUAGE. IF THE USER WRITES IN POLISH, YOU MUST REPLY IN POLISH.
2. DO NOT echo or just translate the user's prompt. You must formulate a proper, meaningful reply.
3. If the user asks you to repeat, translate, or say "the same thing" in another language, look at the CHAT HISTORY and translate YOUR OWN previous answer, NOT the user's question."""

        if self.use_rag_var.get():
            docs = self.db.similarity_search(query, k=2)
            context = "\n---\n".join([d.page_content for d in docs])

            prompt = f"""{system_rules}

User's Data Context:
{context}

{history_str}
CURRENT MESSAGE: {query}
Ada (replying strictly in the language of the CURRENT MESSAGE):"""

        else:
            prompt = f"""{system_rules}

{history_str}
CURRENT MESSAGE: {query}
Ada (replying strictly in the language of the CURRENT MESSAGE):"""

        try:
            response = self.llm.invoke(prompt).strip()

            # 3. Zmiana wyświetlania na "🤖 ADA [model]"
            self.append_chat(f"🤖 ADA [{self.current_model}]: {response}")

            self.chat_history.append(f"CURRENT MESSAGE: {query}")
            self.chat_history.append(f"Ada: {response}")

            if len(self.chat_history) > 6:
                self.chat_history = self.chat_history[-6:]

        except Exception as e:
            self.append_chat(f"❌ ADA [SYSTEM ERROR]: {str(e)}")


if __name__ == "__main__":
    app = DoomsdayChatApp()
    app.mainloop()