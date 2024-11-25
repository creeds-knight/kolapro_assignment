"""
This module modifies the Purchase order model in the Purchases application
"""
from odoo import models, fields

class CustomPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vendor_ids = fields.Many2many('res.partner', string='Vendors',
                                   domain=[('supplier_rank', '>', 0)])

    def action_rfq_send(self):
        if not self.vendor_ids:
            return super(CustomPurchaseOrder, self).action_rfq_send()

        template_id = self.env.ref('purchase.email_template_edi_purchase').id
        mail_template = self.env['mail.template'].browse(template_id)

        for vendor in self.vendor_ids:
            rfq_copy = self.copy(default={
                'partner_id': vendor.id,
                'state': 'draft',
            })
            rfq_copy.button_confirm()
            mail_template.with_context(email_to=vendor.email).send_mail(rfq_copy.id, force_send=True)

        res = super(CustomPurchaseOrder, self).action_rfq_send()
        if 'context' in res:
            res['context']['vendor_ids'] = [v.id for v in self.vendor_ids]
        return res

