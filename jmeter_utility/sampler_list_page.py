import ttkbootstrap as ttk

class ListSamplers(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.parent = parent

        # List to store selected samplers
        self.selected_samplers = []

        # Title Label
        title_label = ttk.Label(self, text="List of Samplers", font=("Arial", 16, "bold"))
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

        # Frame for checkboxes inside the canvas
        self.checkbox_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")

        # Add Modify Buttons
        modify_button = ttk.Button(self, text="Modify Samplers", bootstyle="primary", command=self.navigate_to_modify_samplers)
        modify_button.grid(row=2, column=0, pady=10, padx=10, sticky="w")


        # Go Back Button
        back_button = ttk.Button(self, text="Go Back", bootstyle="secondary", command=self.go_back_to_sampler_page)
        back_button.grid(row=3, column=3, pady=20, padx=20, sticky="e")

    def populate_sampler_names(self, sampler_names):
        """Populate samplers with checkboxes."""
        self.sampler_names = sampler_names  # Store sampler names list

        # Clear previous checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()

        self.selected_samplers = []  # Reset selected samplers

        # Create a Checkbutton for each sampler
        for i, sampler in enumerate(self.sampler_names):
            var = ttk.BooleanVar(value=False)  # Unselected by default
            check_button = ttk.Checkbutton(self.checkbox_frame, text=sampler, variable=var)
            check_button.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            self.selected_samplers.append(var)  # Store BooleanVar

        # Update the scroll region of the canvas
        self.checkbox_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_selected_samplers(self):
        """Return the list of selected samplers."""
        selected = []
        for i, var in enumerate(self.selected_samplers):
            if var.get():
                selected.append(self.sampler_names[i])
        return selected

    def navigate_to_modify_samplers(self):
        """Navigate to modify page with selected samplers."""
        selected_samplers = self.get_selected_samplers()
        if not selected_samplers:
            print("No samplers selected for modification!")  # Debugging message
            return

        # Pass selected samplers to the modify page
        self.parent.modify_selected_samplers_page.populate_sampler_names(selected_samplers)

        # Show modify samplers page
        self.parent.show_page(self.parent.modify_selected_samplers_page)


    def go_back_to_sampler_page(self):
        """Navigate back to the Sampler Modifier Page."""
        self.parent.show_page(self.parent.sampler_modifier_page)
