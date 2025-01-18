import ttkbootstrap as ttk

class ListHeadersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title
        title_label = ttk.Label(self, text="List of Unique Headers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10, sticky="w")

        # Scrollable Frame
        self.canvas = ttk.Canvas(self)
        self.scrollable_frame = ttk.Frame(self.canvas)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.grid(row=1, column=1, sticky="ns")
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Back button
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back)
        back_button.grid(row=2, column=0, pady=10)

    def populate_headers(self, headers):
        """Populate the scrollable frame with header names."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()  # Clear previous headers

        for i, header in enumerate(headers):
            label = ttk.Label(self.scrollable_frame, text=header, font=("Arial", 12))
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

    def go_back(self):
        """Navigate back to the HTTP Header page."""
        self.parent.show_page(self.parent.http_header_page)
