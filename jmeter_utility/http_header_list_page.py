import ttkbootstrap as ttk

class ListHeadersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent
        self.selected_headers = []  # Store boolean variables for checkboxes

        # Configure grid layout for responsiveness
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # Title Label (Centered)
        title_label = ttk.Label(self, text="📜 List of Headers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, sticky="n")

        # Scrollable Frame
        self.scrollable_frame = ttk.Frame(self, padding=10)
        self.scrollable_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="nsew")

        # Add a Canvas for Scrollable Content
        self.canvas = ttk.Canvas(self.scrollable_frame, width=400, height=312)  # Increased height by 25%
        self.canvas.pack(side="left", fill="both", expand=True)

        # Add a Vertical Scrollbar
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame for the checkboxes inside the canvas
        self.checkbox_frame = ttk.Frame(self.canvas, padding=10, width=380)
        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")

        # Buttons (Compact Layout)
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")

        modify_button = ttk.Button(button_frame, text="✏ Modify", bootstyle="primary", command=self.navigate_to_modify_headers)
        modify_button.pack(side="left", fill="x", expand=True, padx=5)

        delete_button = ttk.Button(button_frame, text="🗑 Delete", bootstyle="danger", command=self.navigate_to_delete_headers)
        delete_button.pack(side="left", fill="x", expand=True, padx=5)

        back_button = ttk.Button(button_frame, text="🔙 Back", bootstyle="secondary", command=self.go_back_to_http_header_page)
        back_button.pack(side="left", fill="x", expand=True, padx=5)

    def populate_headers(self, headers):
        """Populate headers with checkboxes for each header."""
        self.headers = headers
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()  # Clear previous checkboxes

        self.selected_headers = []
        for i, header in enumerate(self.headers):
            var = ttk.BooleanVar(value=False)
            check_button = ttk.Checkbutton(self.checkbox_frame, text=header, variable=var, bootstyle="info")
            check_button.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.selected_headers.append(var)

        # Update the canvas size dynamically
        self.checkbox_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_selected_headers(self):
        """Return the list of selected headers."""
        return [self.headers[i] for i, var in enumerate(self.selected_headers) if var.get()]

    def navigate_to_modify_headers(self):
        """Navigate to ModifySelectedHeadersPage."""
        selected_headers = self.get_selected_headers()
        if not selected_headers:
            print("⚠ No headers selected for modification!")
            return

        self.parent.modify_selected_headers_page.populate_headers(selected_headers)
        self.parent.show_page(self.parent.modify_selected_headers_page)

    def navigate_to_delete_headers(self):
        """Navigate to DeleteSelectedHeadersPage."""
        selected_headers = self.get_selected_headers()
        if not selected_headers:
            print("⚠ No headers selected for deletion!")
            return

        self.parent.delete_selected_headers.populate_headers(selected_headers)
        self.parent.show_page(self.parent.delete_selected_headers)

    def go_back_to_http_header_page(self):
        """Navigate back to HTTP Header Page."""
        self.parent.show_page(self.parent.http_header_modify_page)
