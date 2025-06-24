from odoo import models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_all_product_transfer(self):
        for picking in self:
            if picking.state not in ['draft', 'confirmed', 'assigned']:
                raise UserError(_("Only draft or ready transfers can be used for this action."))

            source_location = picking.location_id

            # Get all quant records for source location with qty > 0
            quants = self.env['stock.quant'].sudo().search([
                ('location_id', '=', source_location.id),
                ('quantity', '>', 0),
            ])

            if not quants:
                raise UserError(_("No products with available quantity in source location: %s") % source_location.display_name)

            # Clear previous moves if needed (optional)
            # picking.move_ids.unlink()

            for quant in quants:
                product = quant.product_id

                self.env['stock.move'].sudo().create({
                    'picking_id': picking.id,
                    'product_id': product.id,
                    'product_uom_qty': quant.quantity,
                    'product_uom': product.uom_id.id,
                    'name': product.display_name,
                    'location_id': source_location.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'company_id': picking.company_id.id,
                })

            picking.message_post(body=_("All available products from source location <b>%s</b> have been added to this transfer.") % source_location.display_name)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('All Products Added'),
                    'message': _('Products from %s have been added to the internal transfer.') % source_location.display_name,
                    'type': 'success',
                }
            }
