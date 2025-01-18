import ttkbootstrap as ttk
from tkinter import StringVar

class ModifySelectedHeadersPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # Title Label
        title_label = ttk.Label(self, text="Modify Selected Headers", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Frame to hold selected headers and their corresponding textboxes
        self.headers_frame = ttk.Frame(self)
        self.headers_frame.grid(row=1, column=0, columnspan=4, pady=10)

        # Add a "Back" button to go back to the ListHeadersPage
        back_button = ttk.Button(self, text="Go Back", bootstyle="danger", command=self.go_back_to_list_headers_page)
        back_button.grid(row=2, column=3, pady=20, padx=20, sticky="e")

    def populate_headers(self, selected_headers):
        """Populate the selected headers with textboxes to modify their values."""
        self.selected_headers = selected_headers  # Store the selected headers

        # Clear the previous entries
        for widget in self.headers_frame.winfo_children():
            widget.destroy()

        # Create a Label and Entry for each selected header
        for i, header in enumerate(self.selected_headers):
            # Display the header as a label
            header_label = ttk.Label(self.headers_frame, text=header, font=("Arial", 14))
            header_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

            # Create an Entry widget to input the new value for this header
            new_value_entry = ttk.Entry(self.headers_frame, width=40)
            new_value_entry.grid(row=i, column=1, padx=10, pady=5)

    def go_back_to_list_headers_page(self):
        """Navigate back to the ListHeadersPage."""
        self.parent.show_page(self.parent.http_header_list_page)
