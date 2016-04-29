# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime

class fpoc_report_date_range_wizard(osv.TransientModel):
    _name = "fpoc.report.date.range.wizard"
    _description = 'Report Date Range Wizard'

    _columns = {
        'date_start': fields.date('Date Start', required=True),
        'date_end': fields.date('Date End', required=True),
        'type': fields.selection([
            ('Rf', 'Facturas'),
            ('Rc', 'Notas de Credito'),
            ('Rd', 'Notas de Debito'),
            ('Rn', 'Documentos No Fiscales excepto RAM Clear'),
            ('Re', 'Documentos'),
            ('Rz', 'Reportes Z'),
            ('Rx', 'Reportes X'),
            ('Ry', 'RAM Clear'),
            ('Rr', 'Reportes de Memoria Fiscal'),
            ('Rs', 'Facturas, Notas de Credito, Notas de Debito'),
            ('Ra', 'Facturas, Notas de Credito, Notas de Debito, Documentos No Fiscales y Reportes de Memoria Fiscal'),
            ('Rt', 'Documentos No Fiscales, Copias, RAM Clear y Reportes X'),
            ('Rw', 'Eventos'),
            ('R*', 'Todos los Documentos'),
        ], string='CMD', required=True)
    }

    def execute(self, cr, uid, ids, context=None):
        for wz in self.browse(cr, uid, ids, context=context):
            type = '%s0%s0%s'%(
                wz.type,
                datetime.strftime(datetime.strptime(wz.date_start, DEFAULT_SERVER_DATE_FORMAT), '%d%m%y'),
                datetime.strftime(datetime.strptime(wz.date_end, DEFAULT_SERVER_DATE_FORMAT), '%d%m%y')
            )
            self.pool.get('fpoc.fiscal_printer').report_range(cr, uid, context.get('active_id'), type)
        return True

class fpoc_report_number_range_wizard(osv.TransientModel):
    _name = "fpoc.report.number.range.wizard"
    _description = 'Report Number Range Wizard'

    _columns = {
        'number_start': fields.char('Number Start', size=7, required=True),
        'number_end': fields.char('Number End', size=7, required=True),
        'type': fields.selection([
            ('RF', 'Facturas'),
            ('RC', 'Notas de Credito'),
            ('RD', 'Notas de Debito'),
            ('RN', 'Documentos No Fiscales excepto RAM Clear'),
            ('RE', 'Documentos'),
            ('RZ', 'Reportes Z'),
            ('RX', 'Reportes X'),
            ('RY', 'RAM Clear'),
            ('RR', 'Reportes de Memoria Fiscal'),
            ('RS', 'Facturas, Notas de Credito, Notas de Debito'),
            ('RA', 'Facturas, Notas de Credito, Notas de Debito, Documentos No Fiscales y Reportes de Memoria Fiscal'),
            ('RT', 'Documentos No Fiscales, Copias, RAM Clear y Reportes X'),
            ('R@', 'Todos los Documentos'),
        ], string='CMD', required=True)
    }

    def execute(self, cr, uid, ids, context=None):
        def format_value(value):
            if len(value) == 7:
                return value
            elif len(value) > 7:
                return value[len(value)-7:]
            else:
                return "%s%s"%("0"*(7-len(value)), value)
        for wz in self.browse(cr, uid, ids, context=context):
            type = '%s%s%s'%(
                wz.type,
                format_value(wz.number_start),
                format_value(wz.number_end)
            )
            self.pool.get('fpoc.fiscal_printer').report_range(cr, uid, context.get('active_id'),type)
        return True