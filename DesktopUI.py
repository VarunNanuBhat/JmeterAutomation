import ttkbootstrap as ttk
from tkinter import filedialog, Listbox, Tk, StringVar


# Function to handle file uploads
def upload_file():
    global uploaded_file_paths
    uploaded_file_paths = filedialog.askopenfilenames(
        title="Select Files",
        filetypes=(("JMX files", "*.jmx"), ("All files", "*.*"))
    )
    if uploaded_file_paths:
        # Display the selected file paths in the listbox
        file_listbox.delete(0, 'end')  # Clear existing entries
        for file_path in uploaded_file_paths:
            file_listbox.insert('end', file_path)  # Insert file path into listbox

        # Show a message in the label indicating the files are uploaded
        status_label.config(text="Files Uploaded Successfully!", bootstyle="success")

        # Show the "Next Page" button after uploading files
        next_page_button.grid(row=3, column=0, pady=20)


# Function to navigate to the dropdown page
def go_to_next_page():
    # Hide the first page
    file_upload_frame.pack_forget()

    # Show the dropdown page
    modify_page_frame.pack(pady=20)


# Function to handle the selected dropdown option
def handle_option_selection():
    selected_option = dropdown_var.get()
    if selected_option == "Modify HTTP Header Manager":
        go_to_http_header_page()


# Function to navigate to the HTTP Header Manager page
def go_to_http_header_page():
    # Hide the dropdown page
    modify_page_frame.pack_forget()

    # Show the HTTP Header Manager page
    http_header_frame.pack(pady=20)


# Function to handle HTTP Header modifications
def modify_http_header():
    header_name = header_name_var.get()
    header_value = header_value_var.get()
    if not header_name or not header_value:
        status_label_http.config(text="Please fill in both fields.", bootstyle="danger")
    else:
        # Call the backend function to modify HTTP header
        for file_path in uploaded_file_paths:
            modify_http_header_backend(file_path, header_name, header_value)
        status_label_http.config(text="HTTP Header Modified Successfully!", bootstyle="success")


# Mock backend function for modifying HTTP Header Manager (replace with actual method)
def modify_http_header_backend(file_path, header_name, header_value):
    print(f"Modifying {file_path} with Header Name: {header_name}, Value: {header_value}")


# Create the main window with ttkbootstrap styling
app = ttk.Window(themename="darkly")  # Change theme to your preference
app.title("Modern JMeter Automation Tool")
app.geometry("800x600")  # Increased window size

# First page - File Upload
file_upload_frame = ttk.Frame(app, padding=20)
file_upload_frame.pack(pady=30)

# Add a title label
title_label = ttk.Label(file_upload_frame, text="File Upload Tool", font=("Arial", 22, "bold"), anchor="center")
title_label.grid(row=0, column=0, pady=20)

# Add upload button
upload_button = ttk.Button(file_upload_frame, text="Upload Files", bootstyle="primary", command=upload_file)
upload_button.grid(row=1, column=0, padx=10, pady=10)

# Add a Listbox to display selected files
file_listbox = Listbox(file_upload_frame, height=15, width=80)  # Increased dimensions
file_listbox.grid(row=2, column=0, padx=10, pady=10, columnspan=2)

# Add a scrollbar for the Listbox
scrollbar = ttk.Scrollbar(file_upload_frame, orient="vertical", command=file_listbox.yview)
scrollbar.grid(row=2, column=2, sticky="ns")
file_listbox.config(yscrollcommand=scrollbar.set)

# Status Label to show "Files Uploaded" message
status_label = ttk.Label(file_upload_frame, text="", font=("Arial", 14), anchor="center")
status_label.grid(row=3, column=0, pady=10)

# Next Page Button (hidden initially)
next_page_button = ttk.Button(file_upload_frame, text="Next Page", bootstyle="secondary", command=go_to_next_page)

# Second page - Dropdown and action buttons
modify_page_frame = ttk.Frame(app, padding=20)

# Dropdown for options
dropdown_var = StringVar()
dropdown_var.set("Select an Option")  # Default option

dropdown_menu = ttk.Combobox(modify_page_frame, textvariable=dropdown_var,
                             values=["Modify HTTP Header Manager",
                                     "Disable endpoints ending with certain texts",
                                     "Delete endpoints ending with certain texts",
                                     "Disable sampler"],
                             state="readonly", width=50)  # Increased width
dropdown_menu.grid(row=0, column=0, padx=20, pady=30)

# Button to handle the selected option
action_button = ttk.Button(modify_page_frame, text="Apply", bootstyle="primary", command=handle_option_selection)
action_button.grid(row=1, column=0, pady=20)

# Third page - HTTP Header Manager
http_header_frame = ttk.Frame(app, padding=20)

# Add input fields for HTTP Header Manager
header_name_label = ttk.Label(http_header_frame, text="Header Name:", font=("Arial", 14))
header_name_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

header_name_var = StringVar()
header_name_entry = ttk.Entry(http_header_frame, textvariable=header_name_var, width=50)  # Increased width
header_name_entry.grid(row=0, column=1, padx=20, pady=10)

header_value_label = ttk.Label(http_header_frame, text="Header Value:", font=("Arial", 14))
header_value_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

header_value_var = StringVar()
header_value_entry = ttk.Entry(http_header_frame, textvariable=header_value_var, width=50)  # Increased width
header_value_entry.grid(row=1, column=1, padx=20, pady=10)

# Button to apply the changes
apply_button = ttk.Button(http_header_frame, text="Apply Changes", bootstyle="primary", command=modify_http_header)
apply_button.grid(row=2, column=1, pady=20)

# Status Label for HTTP Header Manager page
status_label_http = ttk.Label(http_header_frame, text="", font=("Arial", 14), anchor="center")
status_label_http.grid(row=3, column=0, columnspan=2, pady=10)

# Run the application
app.mainloop()
