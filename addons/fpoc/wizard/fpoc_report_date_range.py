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
    }

    def execute(self, cr, uid, ids, context=None):
        for wz in self.browse(cr, uid, ids, context=context):
            self.pool.get('fpoc.fiscal_printer').report_range(cr, uid, context.get('active_id'), datetime.strptime(wz.date_start, DEFAULT_SERVER_DATE_FORMAT), datetime.strptime(wz.date_end, DEFAULT_SERVER_DATE_FORMAT))
        return True