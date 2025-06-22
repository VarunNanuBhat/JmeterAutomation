import ttkbootstrap as ttk
from tkinter import Tk


class HomePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent

        # Ensure the frame expands to fill the window
        self.pack(fill="both", expand=True)

        # Configure column and row weights to make elements centered
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)  # Added for the new button

        # 🔹 ICON-Based Introduction using Unicode (⚙️)
        icon_label = ttk.Label(self, text="⚙️", font=("Arial", 80))  # Larger Gear Icon
        icon_label.grid(row=0, column=0, pady=(50, 20), sticky="n")

        # 🔹 Welcome Message
        ttk.Label(
            self, text="JMeter Automation Utility", font=("Arial", 32, "bold"), bootstyle="primary"
        ).grid(row=1, column=0, pady=(10, 10), sticky="n")

        ttk.Label(
            self, text="Simplify Your Load Testing Workflow 🚀", font=("Arial", 18), bootstyle="secondary"
        ).grid(row=2, column=0, pady=(0, 30), sticky="n")

        # 🔹 Get Started Button
        ttk.Button(
            self, text="Get Started", bootstyle="success outline",
            command=self.navigate_to_file_upload_page
        ).grid(row=3, column=0, ipadx=40, ipady=16, pady=50, sticky="n")

        # 🔹 NEW: Script Validator Button
        ttk.Button(
            self, text="Script Validator", bootstyle="info outline",
            command=self.navigate_to_validator_file_upload_page
        ).grid(row=4, column=0, ipadx=40, ipady=16, pady=20, sticky="n")  # New row and pady



    def navigate_to_file_upload_page(self):
        """ Placeholder function for navigation. """
        #print("Navigating to main functionality page...")
        self.parent.show_page(self.parent.file_upload_page)

    def navigate_to_validator_file_upload_page(self):
        """ Navigates to the new file upload page for script validation. """
        self.parent.show_page(self.parent.validator_file_upload_page)
