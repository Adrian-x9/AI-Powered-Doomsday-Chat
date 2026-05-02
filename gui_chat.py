import customtkinter as ctk
import os
import warnings
from datetime import datetime
from tkinter import filedialog
from langchain_community.llms import Ollama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

warnings.filterwarnings("ignore")

# Konfiguracja ścieżek
CHROMA_DB_DIR = "../n8n Workflow Architect/chroma_db"


class DoomsdayChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ustawienia okna
        self.title("AI-Powered Doomsday Chat")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")

        # Stan początkowy
        self.font_family = "Segoe UI"
        self.current_font_size = 14
        self.current_model = "llama3"

        # Inicjalizacja silnika AI
        print("🔋 System init...")
        self.embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        self.db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=self.embeddings)
        self.llm = Ollama(model=self.current_model)

        # Layout - Konfiguracja siatki
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- PANEL USTAWIEŃ (Góra) ---
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")

        # 1. Suwak fontu (Ikona Aa)
        self.font_label = ctk.CTkLabel(self.settings_frame, text=f"Aa: {self.current_font_size}",
                                       font=(self.font_family, self.current_font_size, "bold"))
        self.font_label.pack(side="left", padx=(0, 5))

        self.font_slider = ctk.CTkSlider(self.settings_frame, from_=10, to=32, number_of_steps=22,
                                         command=self.update_font_size, width=120)
        self.font_slider.set(self.current_font_size)
        self.font_slider.pack(side="left", padx=5)

        # 2. Wybór modelu (Ikona Mózgu)
        self.model_label = ctk.CTkLabel(self.settings_frame, text="🧠",
                                        font=(self.font_family, self.current_font_size + 4))
        self.model_label.pack(side="left", padx=(15, 5))

        self.model_option = ctk.CTkOptionMenu(self.settings_frame, values=["llama3", "mistral", "phi3"],
                                              command=self.change_model, width=100,
                                              font=(self.font_family, self.current_font_size))
        self.model_option.set(self.current_model)
        self.model_option.pack(side="left", padx=5)

        # 3. Przycisk Zapisz Log (Ikona Dyskietki)
        self.save_button = ctk.CTkButton(self.settings_frame, text="💾", command=self.save_chat, width=40,
                                         font=(self.font_family, self.current_font_size + 2))
        self.save_button.pack(side="right", padx=(10, 0))

        # 4. CHECKBOX: Baza wiedzy (Ikona Folderu + RAG)
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

        # Przycisk wysyłania to symbol strzałki
        self.send_button = ctk.CTkButton(self.input_frame, text="➤", command=self.send_message, width=60,
                                         font=(self.font_family, self.current_font_size + 4))
        self.send_button.pack(side="right", padx=10, pady=10)

        self.append_chat("🤖 [SYSTEM]: OFFLINE MODE ACTIVE. READY.")

    def update_font_size(self, value):
        """Aktualizuje rozmiar WSZYSTKICH elementów interfejsu proporcjonalnie."""
        self.current_font_size = int(value)

        # Etykieta suwaka
        self.font_label.configure(text=f"Aa: {self.current_font_size}",
                                  font=(self.font_family, self.current_font_size, "bold"))

        # Górny panel
        self.model_label.configure(font=(self.font_family, self.current_font_size + 4))
        self.model_option.configure(font=(self.font_family, self.current_font_size))
        self.save_button.configure(font=(self.font_family, self.current_font_size + 2))
        self.rag_checkbox.configure(font=(self.font_family, self.current_font_size, "bold"))

        # Główne okna i dolny panel
        self.chat_display.configure(font=(self.font_family, self.current_font_size))
        self.user_input.configure(font=(self.font_family, self.current_font_size))
        self.send_button.configure(font=(self.font_family, self.current_font_size + 4))

    def change_model(self, new_model):
        self.append_chat(f"⚙️ [SYSTEM]: Loading model -> {new_model}...")
        self.current_model = new_model
        self.llm = Ollama(model=self.current_model)
        self.append_chat(f"⚙️ [SYSTEM]: Model {new_model} ready.")

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
                self.append_chat(f"💾 [SYSTEM]: Log saved -> {filepath}")
            except Exception as e:
                self.append_chat(f"❌ [SYSTEM ERROR]: {e}")

    def append_chat(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text + "\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        query = self.user_input.get()
        if not query: return

        self.append_chat(f"👤: {query}")
        self.user_input.delete(0, "end")

        if self.use_rag_var.get():
            docs = self.db.similarity_search(query, k=2)
            context = "\n---\n".join([d.page_content for d in docs])

            # Żelazny prompt RAG
            prompt = f"""You are Ada, a helpful AI survival assistant. 
CRITICAL RULE: You MUST answer in the EXACT SAME LANGUAGE that the user used in the QUESTION. If the user writes in Polish, you MUST answer in Polish. If German, in German.

The CONTEXT below contains the user's private data, workflows, and personal information. Treat this as facts about the user.

CONTEXT:
{context}

QUESTION: {query}"""

        else:
            # Żelazny prompt ogólny
            prompt = f"""You are Ada, a helpful AI survival assistant. 
CRITICAL RULE: You MUST answer in the EXACT SAME LANGUAGE that the user used in the QUESTION. If the user writes in Polish, you MUST answer in Polish.

Answer the question using your general knowledge.

QUESTION: {query}"""

        try:
            response = self.llm.invoke(prompt)
            self.append_chat(f"🤖 [{self.current_model}]: {response}")
        except Exception as e:
            self.append_chat(f"❌ [SYSTEM ERROR]: {str(e)}")


if __name__ == "__main__":
    app = DoomsdayChatApp()
    app.mainloop()