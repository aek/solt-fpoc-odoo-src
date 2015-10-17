# -*- coding: utf-8 -*-
from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _

class fiscal_printer_configuration(osv.osv):
    _name = 'fpoc.configuration'
    _description = 'Fiscal printer configuration'

    _columns = {
        'name': fields.char(string='Brand', size=64),
        'model': fields.char('Model', size=64),
        'serial': fields.char('Registry Number', size=64),
        'close_date': fields.date('Report Z Last Date'),
    }

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Name has to be unique!')
    ]

fiscal_printer_configuration()

class fiscal_printer_user(osv.AbstractModel):
    """
    Fiscal printer user is a Abstract class to be used by the owner of the fiscal printer.
    The entity responsable to print tickets must inheret this class.
    """

    _name = 'fpoc.user'
    _description = 'Fiscal printer user'

    _columns = {
        'fiscal_printer_id': fields.many2one('fpoc.fiscal_printer', 'Fiscal Printer'),
        'fiscal_printer_anon_partner_id': fields.many2one('res.partner', 'Anonymous partner'),
    }

    def make_fiscal_ticket(self, cr, uid, ids, ticket, context=None):
        """
        Create Fiscal Ticket.
        """
        fp_obj = self.pool.get('fpoc.fiscal_printer')
        context = context or {}
        r = {}
        for usr in self.browse(cr, uid, ids, context):
            if not usr.fiscal_printer_id:
                raise osv.except_osv(_('Error!'),_('Selected a printer associated.'))

            fp_id = usr.fiscal_printer_id.id
            if context.get('non_fiscal', False):
                r[usr.id] = fp_obj.make_non_fiscal_ticket(cr, uid, [fp_id], ticket=ticket, context=context)[fp_id]
            elif context.get('fiscal_refund', False):
                r[usr.id] = fp_obj.make_fiscal_ticket_refund(cr, uid, [fp_id], ticket=ticket, context=context)[fp_id]
            elif context.get('fiscal', False):
                r[usr.id] = fp_obj.make_fiscal_ticket(cr, uid, [fp_id], ticket=ticket, context=context)[fp_id]
            if isinstance(r[usr.id], RuntimeError) and r[usr.id].message == "Timeout":
                raise osv.except_osv(_('Error!'), _('Timeout happen!!'))
        return r

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
