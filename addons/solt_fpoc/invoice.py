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

_vat = lambda x: x.tax_code_id.parent_id.name == 'IVA'

document_type_map = {
    "DNI":      "D",
    "CUIL":     "L",
    "CUIT":     "T",
    "CPF":      "C",
    "CIB":      "C",
    "CIK":      "C",
    "CIX":      "C",
    "CIW":      "C",
    "CIE":      "C",
    "CIY":      "C",
    "CIM":      "C",
    "CIF":      "C",
    "CIA":      "C",
    "CIJ":      "C",
    "CID":      "C",
    "CIS":      "C",
    "CIG":      "C",
    "CIT":      "C",
    "CIH":      "C",
    "CIU":      "C",
    "CIP":      "C",
    "CIN":      "C",
    "CIQ":      "C",
    "CIL":      "C",
    "CIR":      "C",
    "CIZ":      "C",
    "CIV":      "C",
    "PASS":     "P",
    "LC":       "V",
    "LE":       "E",
};

responsability_map = {
    "IVARI":  "I", # Inscripto, 
    "IVARNI": "N", # No responsable, 
    "RM":     "M", # Monotributista,
    "IVAE":   "E", # Exento,
    "NC":     "U", # No categorizado,
    "CF":     "F", # Consumidor final,
    "RMS":    "T", # Monotributista social,
    "RMTIP":  "P", # Monotributista trabajador independiente promovido.
}

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
                    "lines": [ ],
                    "salesman": _("Saleman: %s") % inv.user_id.name if inv.user_id.name else "",
                }
                for line in inv.invoice_line:
                    ticket["lines"].append({
                        "item_name": line.name,
                        "quantity": line.quantity,
                        "unit_price": line.price_unit,
                        "discount": line.discount,
                        #"vat_rate": ([ tax.amount*100 for tax in line.invoice_line_tax_id.filtered(_vat)]+[0.0])[0],
                    })
                r = inv.make_fiscal_ticket(ticket)[inv.id]

        if r and 'error' not in r:
            return True
        elif r and 'error' in r:
            raise osv.except_osv(_(u'Cancelling Validation'),
                                 _('Error: %s') % r['error'])
        else:
            raise osv.except_osv(_(u'Cancelling Validation'),
                                 _(u'Unknown error.'))
    
    _columns = {
        'use_fiscal_printer': fields.boolean('Associated to a fiscal printer'),
    }
    
fpoc_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
