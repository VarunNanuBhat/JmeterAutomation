import ttkbootstrap as ttk
from file_upload_page import FileUploadPage
from select_functionality import SelectFunctionality
from http_header_modify_page import HttpHeaderPage
from http_header_delete_page import HttpHeaderDeletePage
from endpoint_modifier_with_url import EndpointActionPage
from endpoint_modifier_with_domain import EndpointActionPageForDomain
from replace_domain_name_page import ReplaceDomainNamePage
from replace_contents_page import ReplaceContentPage
from http_header_list_page import ListHeadersPage
from modify_selected_headers_page import ModifySelectedHeadersPage
from checkout_for_http_header_modify import CheckoutPageForHeaderModify
from checkout_for_http_header_delete import CheckoutPageForHeaderDelete


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Modern JMeter Automation Tool")
        self.geometry("800x600")

        # Initialize frames
        self.file_upload_page = FileUploadPage(self)
        self.select_functionality = SelectFunctionality(self)
        self.http_header_modify_page = HttpHeaderPage(self)
        self.http_header_delete_page = HttpHeaderDeletePage(self)
        self.endpoint_modifier_with_url = EndpointActionPage(self)
        self.endpoint_modifier_with_domain = EndpointActionPageForDomain(self)
        self.replace_domain_name_page = ReplaceDomainNamePage(self)
        self.replace_contents_page = ReplaceContentPage(self)
        self.http_header_list_page = ListHeadersPage(self)
        self.modify_selected_headers_page = ModifySelectedHeadersPage(self)
        self.checkout_for_http_header_modify = CheckoutPageForHeaderModify(self)
        self.checkout_for_http_header_delete = CheckoutPageForHeaderDelete(self)


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