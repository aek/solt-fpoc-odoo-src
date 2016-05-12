# -*- coding: utf-8 -*-

import logging
import simplejson
import time

from openerp.osv import osv, fields
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class fpoc_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = [ 'account.invoice', 'fpoc.user']
    
    def action_fiscal_printer(self, cr, uid, ids, context=None):
        r = {}
        if len(ids) > 1:
            raise osv.except_osv(_('Validation'),_('Please, validate one ticket at time.'))
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
                event_id = False
                with self.pool.cursor() as new_cr:
                    event_id = self.make_fiscal_ticket(new_cr, uid, inv.id, ticket, context=context)[inv.id]

                count = 0
                response = {}
                while count != 6:
                    count+=1
                    time.sleep(5)
                    with self.pool.cursor() as new_cr:
                        evt_id = self.pool.get('fpoc.event').browse(new_cr, uid, event_id, context=context)
                        if evt_id.response:
                            response = simplejson.loads(evt_id.response)
                            _logger.info('Respuesta de la Impresora: %s'%unicode(evt_id.response).encode('utf-8'))
                            break

                if context.get('fiscal', False) and response.get('id', False):
                    inv_count = self.search(cr, uid, [('internal_number', '=', response.get('id'))], count=True)
                    if inv_count:
                        raise osv.except_osv(_('Validation'),_('Error: The invoice was not printed. Check if the fiscal Printer is connected'))
                    inv.write({'internal_number': response['id'], 'fiscal_status': 'print'})
                elif context.get('fiscal_refund', False):
                    inv.write({'fiscal_status': 'refund'})
            if response and 'Error' not in response.get('Retorno:', '') and 'error' not in response:
                return True
            else:
                if response:
                    raise osv.except_osv(_('Validation'), response.get('Retorno:'))
                else:
                    raise osv.except_osv(_('Validation'),_('Error: Printer not Connected'))

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
