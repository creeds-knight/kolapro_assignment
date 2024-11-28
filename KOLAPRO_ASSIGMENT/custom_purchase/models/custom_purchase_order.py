from odoo import models, fields,api
from odoo.exceptions import UserError

class CustomPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vendor_ids = fields.Many2many("res.partner", required=True, tracking=True, help="You can find vendors by Name, TIN, Email or Internal Reference.", string="Vendors")
   
    
    @api.onchange('vendor_ids')
    def _onchange_vendor_ids(self):
        '''
        set the first vendor in the list as the partner to avoid changing lots of code
        '''
        if self.vendor_ids:
            self.partner_id = self.vendor_ids[0]
          
            


    def action_rfq_send(self):
        """
        Custom method to send RFQs to all vendors associated with this record.
        """
        # Check if there are vendors to process
        if not self.vendor_ids:
            return super(CustomPurchaseOrder, self).action_rfq_send()

        # Reference the email template for RFQ
        template_id = self.env.ref('purchase.email_template_edi_purchase').id
        mail_template = self.env['mail.template'].browse(template_id)

        original_name = self.name

       
        for vendor in self.vendor_ids:
            # Create a copy of the RFQ for each vendor
            if self.partner_id != vendor:
                rfq_copy = self.copy()
                rfq_copy.partner_id = vendor.id
                rfq_copy.name = original_name  # Retain the original RFQ name
                
                # rfq_copy.button_confirm()

                # Send the email to the vendor
                if vendor.email:
                    mail_template.with_context(email_to=vendor.email).send_mail(
                        rfq_copy.id,
                        force_send=True,
                    )
                    rfq_copy.state = 'sent'
                else:
                    # Log or handle vendors without an email
                    print(f"Vendor {vendor.name} does not have an email address.")

        
        return super(CustomPurchaseOrder, self).action_rfq_send()
