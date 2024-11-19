from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseBid(models.Model):
    _name = 'custom.purchase.bid'
    _description = 'Vendor Bid'

    name = fields.Char('Bid reference', required=True, default='unknown')
    order_id = fields.Many2one('purchase.order', string='RFQ')
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    bid_amount = fields.Float('Bid Amount', required=True, default=0)
    bid_date = fields.Datetime('Bid Date', default=fields.Datetime.now)
    is_winning_bid = fields.Boolean('Winning Bid', default=False)

    @api.onchange('is_winning_bid')
    def _onchange_is_winning_bid(self):
        for bid in self:
            if bid.is_winning_bid and bid.id:
                other_bids = self.search([
                    ('order_id', '=', bid.order_id.id),
                    ('is_winning_bid', '=', True),
                    ('id', '!=', bid.id)
                ])
                if other_bids:
                    other_bids.write({'is_winning_bid': False})

    @api.constrains('is_winning_bid')
    def _check_winning_bid(self):
        for bid in self:
            if bid.is_winning_bid:
                other_winning_bids = self.search([
                    ('order_id', '=', bid.order_id.id),
                    ('is_winning_bid', '=', True),
                    ('id', '!=', bid.id)
                ])
                if other_winning_bids:
                    raise ValidationError('Only one winning bid is allowed per RFQ.')
                bid.order_id.update({
                    'partner_id': bid.vendor_id.id,
                    'amount_total': bid.bid_amount
                })

