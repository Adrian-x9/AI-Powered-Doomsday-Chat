import customtkinter as ctk
import os
import warnings
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
        self.title("AI-Powered Doomsday Chat (ADA)")
        self.geometry("800x700")
        ctk.set_appearance_mode("dark")

        # Stan początkowy fontów
        self.font_family = "Segoe UI"
        self.current_font_size = 14

        # Inicjalizacja silnika AI
        print("🔋 Inicjalizacja systemów survivalowych...")
        self.embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        self.db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=self.embeddings)
        self.llm = Ollama(model="llama3")

        # Layout - Konfiguracja siatki
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- PANEL USTAWIEŃ (Góra) ---
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.font_label = ctk.CTkLabel(self.settings_frame, text=f"Rozmiar tekstu: {self.current_font_size}px",
                                       font=(self.font_family, 12))
        self.font_label.pack(side="left", padx=10)

        self.font_slider = ctk.CTkSlider(self.settings_frame, from_=10, to=32, number_of_steps=22,
                                         command=self.update_font_size)
        self.font_slider.set(self.current_font_size)
        self.font_slider.pack(side="left", fill="x", expand=True, padx=10)

        # --- OKNO CZATU ---
        self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word",
                                           font=(self.font_family, self.current_font_size))
        self.chat_display.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # --- PANEL WEJŚCIA (Dół) ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Inicjalizacja user_input z uwzględnieniem fontu
        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Zadaj pytanie Adzie...",
                                       height=40, font=(self.font_family, self.current_font_size))
        self.user_input.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        self.user_input.bind("<Return>", lambda e: self.send_message())

        self.send_button = ctk.CTkButton(self.input_frame, text="Wyślij", command=self.send_message, width=100)
        self.send_button.pack(side="right", padx=10, pady=10)

        self.append_chat("ADA: System gotowy. Status: OFFLINE. W czym mogę pomóc?")

    def update_font_size(self, value):
        """Aktualizuje rozmiar czcionki w obu polach jednocześnie."""
        self.current_font_size = int(value)
        self.font_label.configure(text=f"Rozmiar tekstu: {self.current_font_size}px")

        # Aktualizacja czatu
        self.chat_display.configure(font=(self.font_family, self.current_font_size))
        # AKTUALIZACJA POLA WPISYWANIA
        self.user_input.configure(font=(self.font_family, self.current_font_size))

    def append_chat(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text + "\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        query = self.user_input.get()
        if not query: return

        self.append_chat(f"TY: {query}")
        self.user_input.delete(0, "end")

        docs = self.db.similarity_search(query, k=2)
        context = "\n---\n".join([d.page_content for d in docs])

        prompt = f"""Jesteś Ada, asystentka przetrwania. 
        ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM.
        Użyj KONTEKSTU poniżej, by odpowiedzieć. Jeśli tam nie ma info, użyj swojej wiedzy.

        KONTEKST:
        {context}

        PYTANIE: {query}"""

        try:
            response = self.llm.invoke(prompt)
            self.append_chat(f"ADA: {response}")
        except Exception as e:
            self.append_chat(f"SYSTEM BŁĄD: {str(e)}")


if __name__ == "__main__":
    app = DoomsdayChatApp()
    app.mainloop()