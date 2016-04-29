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
                def format_value(value):
                    value = str(value)
                    value = value.replace(',', '.')
                    value = value.split('.')
                    if len(value) == 1:
                        value.append('00')
                    else:
                        if len(value[1]) > 2:
                            value[1] = value[1][:1]
                        elif len(value[1]) == 1:
                            value[1] = value[1] + '0'
                    price = ''.join(value)
                    return '0' * (10 - len(price)) + price

                payments = [(pay.journal_id.fiscal_printer_code, format_value(pay.credit)) for pay in inv.payment_ids if pay.journal_id.fiscal_printer_code]
                partner_id = inv.partner_id
                while not partner_id.is_company and partner_id.parent_id:
                    partner_id = partner_id.parent_id

                ticket={
                    "ref": inv.number,
                    "debit_note": False,
                    "partner": {
                        "name": partner_id.display_name or '',
                        "street": partner_id.street or '',
                        "city": partner_id.city or '',
                        "country": partner_id.country_id.name or '',
                        "document_number": partner_id.curp,
                    },
                    'internal_number': inv.internal_number, 
                    "lines": [ ],
                    "payments": payments,
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
                    if context.get('fiscal', False) and r[0].get('response',{}).get('id', False):
                        inv.write({'internal_number': r[0]['response']['id'], 'fiscal_status': 'print'})
                    elif context.get('fiscal_refund', False):
                        inv.write({'fiscal_status': 'refund'})
        if r and 'error' not in r:
            return True
        else:
            if r:
                raise osv.except_osv(_(u'Cancelling Validation'),
                                     _('Error: %s') % r[0]['response'])
            else:
                raise osv.except_osv(_(u'Cancelling Validation'),
                                     _('Error: Printer Driver'))

    def _get_default_printer(self, cr, uid, context=None):
        res = self.pool.get('fpoc.fiscal_printer').search(cr, uid, [('printerStatus', '=', 'active')], context=context)
        if res:
            return res[0]
        return False

    _columns = {
        'use_fiscal_printer': fields.boolean('Associated to a fiscal printer'),
        'fiscal_status': fields.selection([('draft','Draft'),('print', 'Print'),('refund', 'Refund')], string="Fiscal Status"),
    }
    
    _defaults = {
        'fiscal_status': 'draft',
        'use_fiscal_printer': True,
        'fiscal_printer_id': _get_default_printer,
    }
fpoc_invoice()

class fpoc_refund(osv.osv):
    _inherit = 'account.invoice.refund'

    _columns = {
        'fiscal_status': fields.dummy(type='char'),
    }
    def _get_fiscal_status(self, cr, uid, context=None):
        inv = self.pool.get('account.invoice').browse(cr, uid, context.get('active_ids'))[0]
        if inv.internal_number:
            return inv.fiscal_status
        return 'draft'

    _defaults = {
        'fiscal_status': _get_fiscal_status,
    }

    def action_fiscal_refund(self, cr, uid, ids, context=None):
        self.invoice_refund(cr, uid, ids, context=context)
        self.pool.get('account.invoice').action_fiscal_printer(cr, uid, context.get('active_ids'), context={'fiscal_refund': True})

fpoc_refund()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
