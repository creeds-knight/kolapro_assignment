from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseBid(models.Model):
    _name = 'custom.purchase.bid'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vendor Bid'

    name = fields.Char('Bid reference', required=True, default='New')
    rfq = fields.Many2one('purchase.order', string='RFQ')
    bid_amount = fields.Float('Bid Amount', required=True, default=0, compute="_compute_bid_amount")
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
    product_ids = fields.One2many('custom.purchase.bid.line', 'bid_id', string='Bid Line')

    
   
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

            self._update_bid_order_line()

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

        # partner_id = vendor.id
        # return rfq.action_send_rfq()
        
        
    @api.depends('bids_on_rfq')
    def _compute_number_of_bids_on_rfq(self):
        for record in self:
            if record.rfq:
                # Count the number of bids linked to this RFQ
                record.number_of_bids_on_rfq = self.search_count([('rfq.name', '=', record.rfq.name)])
            else:
                record.number_of_bids_on_rfq = 0

    @api.depends('product_ids')
    def _compute_bid_amount(self):
        for  record in self:
            record.bid_amount = sum(line.total_cost for line in self.product_ids)
        return True
    
    @api.onchange('rfq')
    def _update_bid_order_line(self):
        for record in self:
        # Clear existing bid lines if RFQ changes
            record.product_ids = [(5, 0, 0)]
        
        # Check if there is an associated RFQ
            if record.rfq:
                # Loop through each line in the RFQ
                bid_lines = []
                for line in record.rfq.order_line:
                    bid_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_qty,
                        'unit_cost': line.price_unit,
                        'description': line.name or "",
                    }))
                
                # Add these lines to the bid
                record.product_ids = bid_lines

    


        
class PurchaseBidLine(models.Model):
    _name = 'custom.purchase.bid.line'
    _description = 'Purchase Bid Line'

    bid_id = fields.Many2one('custom.purchase.bid', string='Bid')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_cost = fields.Float(string="Cost", required=True, default=0.0)
    total_cost = fields.Float("Total Cost", compute='_compute_total_cost')
    description = fields.Text(string="Description")

    @api.depends('unit_cost', 'quantity')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.unit_cost * record.quantity
            

