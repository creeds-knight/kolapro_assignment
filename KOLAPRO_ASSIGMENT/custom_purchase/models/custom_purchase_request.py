import logging
from odoo import fields, models

logger = logging.getLogger(__name__)

class PurchaseRequest(models.Model):
    '''
        This is a class to implement Request purchases
    '''

    _name = 'custom.purchase.request'
    _description = 'Purchase Request'

    name = fields.Char('Request Reference', required=True)
    employee_id = fields.Many2one('hr.employee',string='Employee', required=True)
    product_ids = fields.Many2many('product.product', string='Requested Products')
    description = fields.Text('Description')


    def action_convert_to_rfq(self):
        rfq_obj = self.env['purchase.order']
        for request in self:
            rfq_values = {
                    'partner_id': request.employee_id.id,
                    'date_order': fields.Datetime.now(),
                    'order_line': [(0, 0, {
                        'product_id': product.id,
                        'product_qty': 1,
                        'price_unit': 0.0,
                        'date_planned': fields.Datetime.now(),
                        }) for product in request.product_ids],
                    }
            rfq = rfq_obj.create(rfq_values)

            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Request for Quotation',
                    'res_model': 'purchase.order',
                    'view_mode': 'form',
                    'res_id': rfq.id,
                    'target': 'current',

                    }
