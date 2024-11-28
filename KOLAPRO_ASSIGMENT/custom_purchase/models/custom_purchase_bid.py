from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseBid(models.Model):
    _name = 'custom.purchase.bid'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vendor Bid'

    name = fields.Char('Bid reference', required=True, default='New')
    rfq = fields.Many2one('purchase.order', string='RFQ')
    bid_amount = fields.Float('Bid Amount', required=True, default=0)
    bid_date = fields.Datetime('Bid Date', default=fields.Datetime.now)
    vendor = fields.Many2one("res.partner", string="Vendor", required=True, domain="[('id', 'in', vendors_with_bids)]")
    vendors_with_bids = fields.Many2many("res.partner", string="Vendors with Bids", compute="_compute_vendors_with_bids")
    status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='pending', track_visibility='onchange')
    bid_details = fields.Text('Bid Description')
    bids_on_rfq = fields.Many2many('custom.purchase.bid','RFQ Bids', compute="_compute_bids_on_rfq")
    number_of_bids_on_rfq = fields.Integer('Number of bids', compute='_compute_number_of_bids_on_rfq')

    
   
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('custom.purchase.bid') or 'New'
        return super().create(vals)
    
    def action_accept_bid(self):
        for record in self:
            record.status = 'accepted'
            
            # Reject other bids with the same RFQ name
            other_bids = self.search([('rfq.name', '=', record.rfq.name), ('id', '!=', record.id)])
            other_bids.write({'status': 'rejected'})
            
            # Set the partner_id to the accepted vendor and confirm the RFQ
            record.message_post(body=f"Bid accepted by {self.env.user.name}. Vendor: {record.vendor.name}")

            if record.rfq:
                record.rfq.partner_id = record.vendor.id
                record.rfq.button_confirm()  # Confirm the RFQ

                # Send email to the accepted vendor
                self.send_po_email(record.rfq, record.vendor)
                

    def action_refuse_bid(self):
        for record in self:
            record.status = "rejected"
            record.message_post(body=f"Bid rejected by {self.env.user.name}. Vendor: {record.vendor.name}")


    @api.constrains('rfq')
    def _validate_vendor(self):
        for record in self:
            if record.vendor not in record.rfq.vendor_ids:
                raise ValidationError(
                    f"Unknown Vendor: '{record.vendor.name}' cannot bid on this order")
            
    @api.depends('rfq')
    def _compute_vendors_with_bids(self):
        for bid in self:
            new_vendor_ids = [vendor.id for vendor in self.rfq.vendor_ids]
            bid.vendors_with_bids = [(6, 0, new_vendor_ids)]


    @api.depends('rfq')
    def _compute_bids_on_rfq(self):
        for record in self:
            if record.rfq:
                # Search for bids with the same RFQ name
                similar_bids = self.search([('rfq.name', '=', record.rfq.name)])
                print([val for val in similar_bids])
                #Use a list of IDs to update the Many2many field
                record.bids_on_rfq = [(6, 0, similar_bids.ids)]
                
            else:
                record.bids_on_rfq = [(5, 0, 0)]
        
    

    def send_po_email(self, rfq, vendor):
        """
        Send the purchase order email to the accepted vendor.
        """
        # Reference the email template for Purchase Order
        template_id = self.env.ref('purchase.email_template_edi_purchase_done').id
        mail_template = self.env['mail.template'].browse(template_id)
        
        # Ensure the vendor has an email
        if vendor.email:
            mail_template.with_context(email_to=vendor.email).send_mail(rfq.id, force_send=True)
        else:
            # Log or handle vendors without an email
            print(f"Vendor {vendor.name} does not have an email address.")
        
    @api.depends('bids_on_rfq')
    def _compute_number_of_bids_on_rfq(self):
        for record in self:
            if record.rfq:
                # Count the number of bids linked to this RFQ
                record.number_of_bids_on_rfq = self.search_count([('rfq.name', '=', record.rfq.name)])
            else:
                # If no RFQ, set the count to 0
                record.number_of_bids_on_rfq = 0