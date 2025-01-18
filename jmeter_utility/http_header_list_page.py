import ttkbootstrap as ttk
from tkinter import StringVar


class ListHeadersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # List to store the selected headers
        self.selected_headers = []

        # Title Label
        title_label = ttk.Label(self, text="List of Headers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Scrollable Frame
        self.scrollable_frame = ttk.Frame(self)
        self.scrollable_frame.grid(row=1, column=0, columnspan=4, pady=20, sticky="nsew")

        # Add a Canvas for Scrollable Content
        self.canvas = ttk.Canvas(self.scrollable_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Add a Vertical Scrollbar
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame for the checkboxes inside the canvas
        self.checkbox_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")

        # Add a "Back" button to go back to the header modification page
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_http_header_page)
        back_button.grid(row=2, column=3, pady=20, padx=20, sticky="e")

    def populate_headers(self, headers):
        """Populate headers with checkboxes for each header."""
        self.headers = headers  # Store the headers list

        # Clear previous checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()

        self.selected_headers = []  # Reset selected headers

        # Create a Checkbutton for each header in the list
        for i, header in enumerate(self.headers):
            var = StringVar(value="off")
            check_button = ttk.Checkbutton(self.checkbox_frame, text=header, variable=var)
            check_button.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            self.selected_headers.append(var)

        # Update the scroll region of the canvas after adding checkboxes
        self.checkbox_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_selected_headers(self):
        """Return the list of selected headers."""
        selected = []
        for i, var in enumerate(self.selected_headers):
            if var.get() == "on":
                selected.append(self.headers[i])
        return selected

    def go_back_to_http_header_page(self):
        """Navigate back to the HTTP Header Page."""
        self.parent.show_page(self.parent.http_header_page)
