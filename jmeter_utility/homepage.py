import ttkbootstrap as ttk
from tkinter import Tk


class HomePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=40)
        self.parent = parent

        # Ensure the frame expands to fill the window
        self.grid(row=0, column=0, sticky="nsew")

        # Configure column and row weights to make elements centered
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

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

    def navigate_to_file_upload_page(self):
        """ Placeholder function for navigation. """
        #print("Navigating to main functionality page...")
        self.parent.show_page(self.parent.file_upload_page)


'''
# 🔹 Running the UI in Fullscreen
if __name__ == "__main__":
    root = ttk.Window(themename="superhero")  # Choose a modern theme
    root.title("JMeter Automation Utility")

    # Set the window to full screen
    root.state("zoomed")  # Maximizes the window (works on Windows)
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")  # Fullscreen on all OS

    # Ensure grid expands fully
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    home_page = HomePage(root)
    home_page.grid(row=0, column=0, sticky="nsew")  # Make it fill the screen

    root.mainloop()
'''