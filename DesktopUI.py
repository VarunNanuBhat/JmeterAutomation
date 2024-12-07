import ttkbootstrap as ttk
from tkinter import filedialog, Listbox, Tk, StringVar


# Function to handle file uploads
def upload_file():
    file_paths = filedialog.askopenfilenames(
        title="Select Files",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    if file_paths:
        # Display the selected file paths in the listbox
        file_listbox.delete(0, 'end')  # Clear existing entries
        for file_path in file_paths:
            file_listbox.insert('end', file_path)  # Insert file path into listbox

        # Show a message in the label indicating the files are uploaded
        status_label.config(text="Files Uploaded Successfully!", bootstyle="success")

        # Show the "Next Page" button after uploading files
        next_page_button.grid(row=3, column=0, pady=20)


# Function to navigate to the next page
def go_to_next_page():
    # Hide the first page
    file_upload_frame.pack_forget()

    # Show the second page with the dropdown and action button
    modify_page_frame.pack(pady=10)


# Function to handle the selected dropdown option
def handle_option_selection():
    selected_option = dropdown_var.get()
    print(f"Selected option: {selected_option}")
    # Here you can add logic based on the selected option (e.g., modify headers, delete endpoints, etc.)
    # Example: if selected_option == "Modify HTTP header Manager": ...


# Create the main window with ttkbootstrap styling
app = ttk.Window(themename="darkly")  # Change theme to your preference (darkly, flatly, etc.)
app.title("Modern File Upload Tool")
app.geometry("600x400")

# First page - File Upload
file_upload_frame = ttk.Frame(app, padding=10)
file_upload_frame.pack(pady=20)

# Add a title label
title_label = ttk.Label(file_upload_frame, text="File Upload Tool", font=("Arial", 18, "bold"), anchor="center")
title_label.grid(row=0, column=0, pady=20)

# Add upload button
upload_button = ttk.Button(file_upload_frame, text="Upload Files", bootstyle="primary", command=upload_file)
upload_button.grid(row=1, column=0, padx=10)

# Add a Listbox to display selected files (using tkinter.Listbox)
file_listbox = Listbox(file_upload_frame, height=12, width=60)
file_listbox.grid(row=2, column=0, padx=10, pady=10, columnspan=2)

# Add a scrollbar for the Listbox
scrollbar = ttk.Scrollbar(file_upload_frame, orient="vertical", command=file_listbox.yview)
scrollbar.grid(row=2, column=2, sticky="ns")
file_listbox.config(yscrollcommand=scrollbar.set)

# Status Label to show "Files Uploaded" message
status_label = ttk.Label(file_upload_frame, text="", font=("Arial", 12), anchor="center")
status_label.grid(row=3, column=0, pady=10)

# Next Page Button (hidden initially)
next_page_button = ttk.Button(file_upload_frame, text="Next Page", bootstyle="secondary", command=go_to_next_page)

# Second page - Dropdown and action buttons
modify_page_frame = ttk.Frame(app, padding=10)

# Dropdown for options
dropdown_var = StringVar()
dropdown_var.set("Select an Option")  # Default option

dropdown_menu = ttk.Combobox(modify_page_frame, textvariable=dropdown_var,
                             values=["Modify HTTP Header Manager",
                                     "Disable endpoints ending with certain texts",
                                     "Delete endpoints ending with certain texts",
                                     "Disable sampler"],
                             state="readonly", width=40)
dropdown_menu.grid(row=0, column=0, padx=10, pady=20)

# Button to handle the selected option
action_button = ttk.Button(modify_page_frame, text="Apply", bootstyle="primary", command=handle_option_selection)
action_button.grid(row=1, column=0, pady=20)

# Run the application
app.mainloop()
