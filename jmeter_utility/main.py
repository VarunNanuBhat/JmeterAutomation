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
from sampler_modifier_page import SamplerModifierPage
from delete_selected_headers import DeleteSelectedHeadersPage
from checkout_for_domain_page import CheckoutPageForDomain
from domain_list_page import ListDomains
from modify_selected_domains_page import ModifySelectedDomainsPage
from checkout_for_replace_domain_page import CheckoutPageForReplaceDomain
from replace_selected_domains_page import ReplaceSelectedDomainsPage
from checkout_for_sampler_page import CheckoutForSamplerPage
from sampler_list_page import ListSamplers
from modify_selected_samplers_page import ModifySelectedSamplersPage
from checkout_for_endpoint_modifier_with_url import CheckoutPageForEndpointModifierWithURL
from checkout_for_replace_contents_page import CheckoutPageForReplaceText
from homepage import HomePage


# Script validator
from validator_file_upload_page import ValidatorFileUploadPage
from validator_options_page import ValidatorOptionsPage
from validator_report_page import ValidatorReportPage




class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Modern JMeter Automation Tool")

        # Set full screen dynamically
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.state("zoomed")  # Maximize window

        # Store a reference to the selected JMX files for validation, accessible across pages
        self.validator_jmx_files = []

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
        self.sampler_modifier_page = SamplerModifierPage(self)
        self.delete_selected_headers = DeleteSelectedHeadersPage(self)
        self.checkout_for_domain_page = CheckoutPageForDomain(self)
        self.domain_list_page = ListDomains(self)
        self.modify_selected_domains_page = ModifySelectedDomainsPage(self)
        self.checkout_for_replace_domain_page = CheckoutPageForReplaceDomain(self)
        self.replace_selected_domains_page = ReplaceSelectedDomainsPage(self)
        self.checkout_for_sampler_page = CheckoutForSamplerPage(self)
        self.sampler_list_page = ListSamplers(self)
        self.modify_selected_samplers_page = ModifySelectedSamplersPage(self)
        self.checkout_for_endpoint_modifier_with_url = CheckoutPageForEndpointModifierWithURL(self)
        self.checkout_for_replace_contents_page = CheckoutPageForReplaceText(self)
        self.homepage = HomePage(self)

        # --- NEW: Initialize Script Validator frames ---
        self.validator_file_upload_page = ValidatorFileUploadPage(self)
        self.validator_file_upload_page = ValidatorFileUploadPage(self)
        self.validator_options_page = ValidatorOptionsPage(self)
        self.validator_report_page = ValidatorReportPage(self)



        # Start with the file upload page
        #self.show_page(self.file_upload_page)
        self.show_page(self.homepage)

    def show_page(self, page):
        """Hide all pages and show the specified one."""
        for child in self.winfo_children():
            child.pack_forget()
        page.pack(pady=20, fill="both", expand=True)

    def set_validator_jmx_files(self, files):
        self.validator_jmx_files = files

    def get_validator_jmx_files(self):
        return self.validator_jmx_files


if __name__ == "__main__":
    app = App()
    app.mainloop()