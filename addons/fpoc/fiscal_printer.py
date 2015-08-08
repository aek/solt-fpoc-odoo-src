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

from controllers.main import do_event
from datetime import datetime

from controllers.main import DenialService

class fiscal_printer_disconnected(osv.TransientModel):
    """
    Disconnected but published printers.
    """
    _name = 'fpoc.disconnected'
    _description = 'Printers not connected to the server.'

    _columns = {
        'name': fields.char(string='Name'),
        'session_id': fields.char(string='Session'),
        'user_id': fields.many2one('res.users', string='Responsable'),
    }

    def _update_(self, cr, uid, force=True, context=None):
        cr.execute('SELECT COUNT(*) FROM %s' % self._table)
        count = cr.fetchone()[0]
        if not force and count > 0:
            return 
        if count > 0:
            cr.execute('DELETE FROM %s' % self._table)
        t_fp_obj = self.pool.get('fpoc.fiscal_printer')
        R = do_event('list_printers', control=True)
        w_wfp_ids = []
        i = 0
        for resp in R:
            if not resp: continue
            for p in resp['printers']:
                if t_fp_obj.search(cr, uid, [("name", "=", p['name'])]):
                    pass
                else:
                    values = {
                        'name': p['name'],
                        'session_id': p['sid'],
                        'user_id': p['uid'],
                    }
                    pid = self.create(cr, uid, values)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        self._update_(cr, uid, force=True)
        return super(fiscal_printer_disconnected, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        self._update_(cr, uid, force=False)
        return super(fiscal_printer_disconnected, self).read(cr, uid, ids, fields=fields, context=context, load=load)

    def create_fiscal_printer(self, cr, uid, ids, context=None):
        """
        Create fiscal printers from this temporal printers
        """
        fp_obj = self.pool.get('fpoc.fiscal_printer')
        for pri in self.browse(cr, uid, ids):
            values = {
                'name': pri.name,
                'session_id': pri.session_id,
            }
            fp_obj.create(cr, uid, values)
        return {
            'name': _('Fiscal Printers'),
            'domain': [],
            'res_model': 'fpoc.fiscal_printer',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': context,
        }

fiscal_printer_disconnected()

class fiscal_printer(osv.osv):
    """
    The fiscal printer entity.
    """

    def _get_status(self, cr, uid, ids, field_name, arg, context=None):
        s = self.get_state(cr, uid, ids, context) 

        r = {}
        for p_id in ids:
            if s[p_id]:
                r[p_id] = {
                    'printerStatus': s[p_id].get('strPrinterStatus', 'Unknown'),
                    'fiscalStatus': s[p_id].get('strFiscalStatus', 'Unknown'),
                }
            else:
                r[p_id]= {
                    'printerStatus':'Offline',
                    'fiscalStatus': 'Offline',
                }
        return r

    _name = 'fpoc.fiscal_printer'
    _description = 'fiscal_printer'

    _columns = {
        'name': fields.char(string='Name', required=True),
        'lastUpdate': fields.datetime(string='Last Update'),
        'printerStatus': fields.function(_get_status, type="char", method=True, readonly="True", multi="state", string='Printer status'),
        'fiscalStatus':  fields.function(_get_status, type="char", method=True, readonly="True", multi="state", string='Fiscal status'),
        'session_id': fields.char(string='session_id'),
    }

    _defaults = {
    }

    _constraints = [
    ]

    _sql_constraints = [ ('model_serialNumber_unique', 'unique("model", "serialNumber")', 'this printer with this model and serial number yet exists') ]

    def short_test(self, cr, uid, ids, context=None):
        for fp in self.browse(cr, uid, ids):
            lines = [
                '80$TEST RECEIPT',
                '800-------------------------------------',
                '800REFERENCIA: REC-443',
                '800CLIENTE: 5 MANUEL SALVADOR RIOVALLE',
                '80*TOTAL      B/. 75.00',
                '80*Efectivo   B/. 80.00',
                '80*CAMBIO     B/. 5.00',
                '800-------------------------------------',
                '800VENDEDOR: ADMINISTRADOR ADMIN',
                '810',
            ]
            do_event('make_ticket', {'name': fp.name, 'lines': lines}, session_id=fp.session_id, printer_id=fp.name)
        return True

    def report_x(self, cr, uid, ids, context=None):
        for fp in self.browse(cr, uid, ids):
            do_event('make_report', {'name': fp.name, 'type': 'I0X'}, session_id=fp.session_id, printer_id=fp.name)
        return True

    def report_z(self, cr, uid, ids, context=None):
        for fp in self.browse(cr, uid, ids):
            do_event('make_report', {'name': fp.name, 'type': 'I0Z'}, session_id=fp.session_id, printer_id=fp.name)
        return True

    def get_state(self, cr, uid, ids, context=None):
        r = {}
        for fp in self.browse(cr, uid, ids):
            try:
                event_result = do_event('get_status', {'name': fp.name},
                     session_id=fp.session_id, printer_id=fp.name)
            except DenialService, m:
                raise osv.except_osv(_('Connectivity Error'), m)
            r[fp.id] = event_result.pop() if event_result else False
        return r

    def make_fiscal_ticket(self, cr, uid, ids, options={}, ticket={}, context=None):
        fparms = {}
        r = {}
        for fp in self.browse(cr, uid, ids):
            lines = [
                'jSNOMBRE RAZON SOCIAL', 
                'jRRUC_CEDULA', 
                'j3LINEA 3 telefono o Celular o Direccion',
                'j4LINEA 4 telefono o Celular o Direccion',
                'j5LINEA 5 telefono o Celular o Direccion',
                'j6LINEA 6 telefono o Celular o Direccion',
                '@COMENTARIO',
                '!00000010000850000001000CHRISTIE`S 3825T/3826T TITANI+ME690',
                'p-2000',
                '!000000880000001000PROG. GENERICO',
                'p-2000',
                '!000000880000001000PROG. GENERICO',
                'p-2000',
                '@prueba de comentarios para que se muestr',
                '@ en la fiscal',
                '@  ***GARANTIA***',
                '101'
            ]
            
            fparms['name'] = fp.name
            fparms['options'] = options
            fparms['ticket'] = ticket
            event_result = do_event('make_ticket', fparms, session_id=fp.session_id, printer_id=fp.name)
            r[fp.id] = event_result.pop() if event_result else False
        return r

fiscal_printer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
