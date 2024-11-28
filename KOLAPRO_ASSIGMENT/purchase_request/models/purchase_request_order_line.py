from odoo import models, fields

class ProcurementRequestLine(models.Model):
    _name = 'procurement.request.line'
    _description = 'Procurement Request Line'

    procurement_request_id = fields.Many2one('procurement.request', string='Procurement Request')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    description = fields.Text(string="Description")