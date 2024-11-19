"""
This module modifies the Purchase order model in the Purchases application
"""
from odoo import models, fields

class CustomPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vendor_ids = fields.Many2many('res.partner', string='Vendors',
                                   domain=[('supplier_rank', '>', 0)])

    def action_rfq_send(self):
        for vendor in self.vendor_ids:
            rfq_copy = self.copy(default={
                'partner_id': vendor.id,
                'state': 'draft',
            })
            rfq_copy.button_confirm()

