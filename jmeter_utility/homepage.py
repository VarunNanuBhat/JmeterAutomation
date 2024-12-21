import ttkbootstrap as ttk
from file_upload_page import FileUploadPage
from select_functionality import SelectFunctionality
from http_header_modify_page import HttpHeaderPage


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Modern JMeter Automation Tool")
        self.geometry("800x600")

        # Initialize frames
        self.file_upload_page = FileUploadPage(self)
        self.select_functionality = SelectFunctionality(self)
        self.http_header_page = HttpHeaderPage(self)

        # Start with the file upload page
        self.show_page(self.file_upload_page)

    def show_page(self, page):
        """Hide all pages and show the specified one."""
        for child in self.winfo_children():
            child.pack_forget()
        page.pack(pady=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()
