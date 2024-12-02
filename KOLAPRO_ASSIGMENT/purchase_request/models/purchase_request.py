from odoo import models, fields, api

class ProcurementRequest(models.Model):
    _name = 'procurement.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Procurement Request'

    name = fields.Char(string='Request Reference', required=True, copy=False, default='New')
    product_ids = fields.One2many('procurement.request.line', 'procurement_request_id', string='Products')
    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user)
    # suggested_partners = fields.Many2one('res.partner', string='Vendors')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('rfq', 'RFQ Created'),
    ], string='Status', default='draft', track_visibility='onchange')
    rfq_id = fields.Many2one('purchase.order', string='RFQ')
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today)
    expected_date = fields.Date(string='Expected Date')
    total_quantity = fields.Float(string='Total Quantity', compute='_compute_total_quantity', store=True)
    total_cost = fields.Float(string='Budget ', compute='_compute_total_cost', store=True)
    comments = fields.Text(string='Additional Comments')
    purchases_by_employee = fields.Integer('Purchases', compute='_compute_purchases_by_employee')


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('procurement.request') or 'New'
        return super().create(vals)

    def action_confirm(self):
        self.state = 'confirmed'

    @api.depends('product_ids')
    def _compute_total_quantity(self):
        for record in self:
            record.total_quantity = sum(line.quantity for line in record.product_ids)

    @api.depends('product_ids')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = sum(line.quantity * line.product_id.standard_price for line in record.product_ids)


    def action_create_rfq(self):
        PurchaseOrder = self.env['purchase.order']
        rfq = PurchaseOrder.create({
            'partner_id': self.requested_by.id,  # Vendor to be selected manually
            'order_line': [],
        })
        for line in self.product_ids:
            rfq.write({
                'order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'price_unit': 0.0,
                    'date_planned': fields.Datetime.now(),
                    # 'description': line.description,
                })],
            })
        self.write({'state': 'rfq', 'rfq_id': rfq.id})
        
        return {
                    'type': 'ir.actions.act_window',
                    'name': 'Request for Quotation',
                    'res_model': 'purchase.order',
                    'view_mode': 'form',
                    'res_id': rfq.id,
                    'target': 'current',

                    }
    

    def action_add_from_catalog(self):
        products = self.env['product.product'].browse(self.env.context.get('product_ids'))
        return products.action_add_from_catalog()
    
    @api.depends('requested_by')
    def _compute_purchases_by_employee(self):
        # current_employee_name = self.requested_by.name
        for record in self:
            if record.requested_by:
                record.purchases_by_employee = self.search_count([('requested_by', '=', record.requested_by.id)])
            else:
                record.purchases_by_employee = 0 