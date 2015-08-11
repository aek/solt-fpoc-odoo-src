# -*- coding: utf-8 -*-
from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _

class fiscal_printer_configuration(osv.osv):
    """
    This configuration is independent of the printer, is related to point of sale.

    Must be used as entry for diferent calls:

    open_fiscal_ticket
    add_fiscal_item
    close_fiscal_ticket
    """

    _name = 'fpoc.configuration'
    _description = 'Fiscal printer configuration'

    def _get_type(self, cr, uid, context=None):
        return []

    def _get_protocol(self, cr, uid, context=None):
        return []

    _columns = {
        'name': fields.char(string='Name'),
        'type': fields.selection(_get_type, 'Type'),
        'protocol': fields.char('Protocol'),
        'user_ids': fields.one2many('fpoc.user', 'fiscal_printer_configuration_id', 'User entities'),
    }

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Name has to be unique!')
    ]

    def onchange_type(self, cr, uid, ids, type, context=None):
        return { 'value': { 'protocol': None } }

    def toDict(self, cr, uid, ids, context=None):
        return { id: {} for id in ids }

    def solve_status(self, cr, uid, ids, status, context=None):
        """
        This function compute paper_state, fiscal_state and printer_state for this configuration type.
        """
        return status

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
        'fiscal_printer_configuration_id': fields.many2one('fpoc.configuration', 'Configuration'),
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

    def cancel_fiscal_ticket(self, cr, uid, ids, context=None):
        """
        """
        fp_obj = self.pool.get('fpoc.fiscal_printer')
        context = context or {}
        r = {}
        for usr in self.browse(cr, uid, ids, context):
            fp_id = usr.fiscal_printer_id.id
            r[usr.id] = fp_obj.cancel_fiscal_ticket(cr, uid, fp_id,
                                                   context=context)[fp_id]
        return r

    def open_fiscal_journal(self, cr, uid, ids, context=None):
        context = context or {}
        r = {}
        for usr in self.browse(cr, uid, ids, context):
            #if not usr.fiscal_printer_state in ['ready']:
            #    raise osv.except_osv(_('Error!'), _('Printer is not ready to open.'))
            if not usr.fiscal_printer_id.fiscalStatus in ['close']:
                raise osv.except_osv(_('Error!'), _('You can\'t open a opened printer.'))
            r[usr.id] = usr.fiscal_printer_id.open_fiscal_journal()
        return r

    def close_fiscal_journal(self, cr, uid, ids, context=None):
        context = context or {}
        r = {}
        for usr in self.browse(cr, uid, ids, context):
            #if not usr.fiscal_printer_state in ['ready']:
            #    raise osv.except_osv(_('Error!'), _('Printer is not ready to close.'))
            if not usr.fiscal_printer_id.fiscalStatus in ['open']:
                raise osv.except_osv(_('Error!'), _('You can\'t close a closed printer.'))
            r[usr.id] = usr.fiscal_printer_id.report_z()
        return r

    def shift_change(self, cr, uid, ids, context=None):
        context = context or {}
        r = {}
        for usr in self.browse(cr, uid, ids, context):
            #if not usr.fiscal_printer_state in ['ready']:
            #    raise osv.except_osv(_('Error!'), _('Printer is not ready to close.'))
            if not usr.fiscal_printer_id.fiscalStatus in ['open']:
                raise osv.except_osv(_('Error!'), _('You can\'t shift a closed printer.'))
            r[usr.id] = usr.fiscal_printer_id.report_x()
        return r

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
