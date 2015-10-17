# -*- coding: utf-8 -*-
##############################################################################
#
#    fiscal_printer
#    Copyright (C) 2014 No author.
#    No email
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import re
from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _
import logging
import json

_logger = logging.getLogger(__name__)

class fpoc_invoice(osv.osv):
    """"""
    _name = 'account.invoice'
    _inherit = [ 'account.invoice', 'fpoc.user']
    
    def action_fiscal_printer(self, cr, uid, ids, context=None):
        r = {}
        if len(ids) > 1:
            raise osv.except_osv(_(u'Cancelling Validation'),
                                 _(u'Please, validate one ticket at time.'))
            return False

        for inv in self.browse(cr, uid, ids, context):
            if inv.use_fiscal_printer:
                ticket={
                    "debit_note": False,
                    "partner": {
                        "name": inv.partner_id.name,
                        "street": inv.partner_id.street,
                        "city": inv.partner_id.city,
                        "country": inv.partner_id.country_id.name,
                        "document_number": inv.partner_id.curp,
                    },
                    'internal_number': inv.internal_number, 
                    "lines": [ ],
                    "salesman": _("Saleman: %s") % inv.user_id.name if inv.user_id.name else "",
                }
                for line in inv.invoice_line:
                    taxes = line.invoice_line_tax_id
                    if taxes:
                        tax = int(taxes[0].amount * 100)
                    else:
                        tax = 0
                    ticket["lines"].append({
                        "item_name": line.product_id.name,
                        "quantity": line.quantity,
                        "unit_price": line.price_unit,
                        "discount": line.discount,
                        "tax": str(tax),
                    })
                r = inv.make_fiscal_ticket(ticket)[inv.id]
                if r:
                    _logger.info('Respuesta de la Impresora: %s'%str(r))
                    if context.get('fiscal', False):
                        inv.write({'internal_number': r[0]['response']['id'], 'fiscal_status': 'print'})
                    elif context.get('fiscal_refund', False):
                        inv.write({'fiscal_status': 'refund'})
        if r and 'error' not in r:
            return True
        else:
            raise osv.except_osv(_(u'Cancelling Validation'),
                                 _('Error: %s') % r[0]['response'])
    
    _columns = {
        'use_fiscal_printer': fields.boolean('Associated to a fiscal printer'),
        'fiscal_status': fields.selection([('draft','Draft'),('print', 'Print'),('refund', 'Refund')], string="Fiscal Status"),
    }
    
    _defaults = {
        'fiscal_status': 'draft',
        'use_fiscal_printer': True,
    }
fpoc_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
