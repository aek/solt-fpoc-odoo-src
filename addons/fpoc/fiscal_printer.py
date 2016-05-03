# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
import simplejson

itbms = {'0': ' ','7': '!','10': '"'}
itbms_ref = {'0': '0','7': '1','10': '2'}

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
    _name = 'fpoc.fiscal_printer'
    _description = 'fiscal_printer'

    """
    The fiscal printer entity.
    """
    def _get_status_z(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        today = fields.date.context_today(self, cr, uid, context)
        for printer in self.browse(cr, uid, ids, context):
            if printer.fiscal_config_id.close_date == today:
                res[printer.id] = False
            else:
                res[printer.id] = True
        return res
    
    def _get_status(self, cr, uid, ids, field_name, arg, context=None):
        r = {}
        for p_id in ids:
            r[p_id] = {
                'printerStatus': 'active',
            }
        return r


    _columns = {
        'name': fields.char(string='Name', required=True),
        'lastUpdate': fields.datetime(string='Last Update'),
        'printerStatus': fields.function(_get_status, type="char", method=True, readonly="True", multi="state", string='Printer status'),
        'fiscalStatus':  fields.selection([('open', 'Open'),('close', 'Close')], string='Fiscal status'),
        'session_id': fields.char(string='session_id'),
        'fiscal_config_id': fields.many2one('fpoc.configuration', 'Configuration'),
        'allow_z': fields.function(_get_status_z, type="boolean", method=True, readonly="True", string='Allow Report Z'),
    }

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
            self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_ticket', 'data': simplejson.dumps(lines), 'printer_id': fp.id}, context=context)
        return True

    def report_x(self, cr, uid, ids, context=None):
        for fp in self.browse(cr, uid, ids):
            self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_report', 'data': "I0X",'printer_id': fp.id}, context=context)
        return True

    def report_x2(self, cr, uid, ids, context=None):
        for fp in self.browse(cr, uid, ids):
            self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_report', 'data': "I1X", 'printer_id': fp.id},context=context)
        return True

    def report_z(self, cr, uid, ids, context=None):
        today = fields.date.context_today(self, cr, uid, context)
        for fp in self.browse(cr, uid, ids):
            self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_report', 'data': "I0Z", 'printer_id': fp.id},context=context)
            fp.fiscal_config_id.write({'close_date': today})
        return True

    def report_z2(self, cr, uid, ids, context=None):
        today = fields.date.context_today(self, cr, uid, context)
        for fp in self.browse(cr, uid, ids):
            self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_report', 'data': "I1Z", 'printer_id': fp.id},context=context)
            fp.fiscal_config_id.write({'close_date': today})
        return True

    def report_date_range_wizard(self, cr, uid, ids, context=None):
        return {
            'name': 'Date Range Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fpoc.report.date.range.wizard',
            #'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def report_number_range_wizard(self, cr, uid, ids, context=None):
        return {
            'name': 'Number Range Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fpoc.report.number.range.wizard',
            # 'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def report_range(self, cr, uid, ids, type, context=None):
        for fp in self.browse(cr, uid, ids):
            self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_report', 'data': type, 'printer_id': fp.id},context=context)
        return True

    def fiscal_set_payment_codes(self, cr, uid, ids, context=None):
        journal_ids = self.pool.get('account.journal').search(cr, uid, [('fiscal_printer_code', '!=', False)], context=context)
        journal_data = [(j.fiscal_printer_code, j.name) for j in self.pool.get('account.journal').browse(cr, uid, journal_ids, context=context)]
        for fp in self.browse(cr, uid, ids):
            for data in journal_data:
                self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_report', 'data': 'PE%s%s' % data, 'printer_id': fp.id},context=context)
        return True

    # def get_state(self, cr, uid, ids, context=None):
    #     r = {}
    #     for fp in self.browse(cr, uid, ids):
    #         try:
    #             event_result = do_event('get_status', {'name': fp.name},
    #                  session_id=fp.session_id, printer_id=fp.name)
    #         except DenialService, m:
    #             raise osv.except_osv(_('Connectivity Error'), m)
    #         r[fp.id] = event_result.pop() if event_result else False
    #     return r

    def make_non_fiscal_ticket(self, cr, uid, ids, ticket={}, context=None):
        r = {}
        for fp in self.browse(cr, uid, ids):
            lines = [
                '80$%s'%ticket.get('partner').get('name'),#NOMBRE RAZON SOCIAL
                '800%s'%ticket.get('partner').get('document_number'),#RUC_CEDULA
                '800%s'%ticket.get('partner').get('street', ''),
                '800%s'%ticket.get('partner').get('city', ''),
                '800%s'%ticket.get('partner').get('country', ''),
                '800-------------------------',
            ]
            total = 0

            for prod_line in ticket.get('lines'):
                price = prod_line.get('unit_price') * prod_line.get('quantity')
                price = price - (price * prod_line.get('discount')/100)
                total += price
                lines.append('80*%s[%s] B/. %s'%(prod_line.get('item_name'), prod_line.get('unit_price'), prod_line.get('quantity')))
                if prod_line.get('discount', False):
                    lines.append('800Descuento:%s'%prod_line.get('discount'))
            lines.append('800-------------------------')
            lines.append('80*Total B/. %s'%total)
            lines.append('800Vendedor:%s'%prod_line.get('salesman'))
            lines.append('810')

            r[fp.id] = self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_ticket', 'data': simplejson.dumps(lines), 'printer_id': fp.id}, context=context)
        return r
    
    def make_fiscal_ticket(self, cr, uid, ids, ticket={}, context=None):
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
                    value[1] = value[1]+'0'
            return ''.join(value)
        r = {}
        for fp in self.browse(cr, uid, ids):
            lines = [
                'jR%s'%ticket.get('partner').get('document_number'),#RUC_CEDULA
            ]
            jindex = 2
            for elem in (ticket.get('partner').get('name'), ticket.get('partner').get('street', ''), ticket.get('partner').get('city', ''), ticket.get('partner').get('country', '')):
                head = elem
                tail = False
                if len(elem) > 40:
                    head = elem[:40]
                    tail = elem[40:]
                if jindex == 2:
                    lines.append('jS%s'% head)
                else:
                    lines.append('j%s%s'% (jindex,head))
                jindex += 1

                if tail:
                    while tail:
                        head = tail
                        if len(tail) > 40:
                            head = tail[:40]
                            tail = tail[40:]
                        else:
                            tail = False
                        lines.append('j%s%s'% (jindex,head))
                        jindex += 1

            for prod_line in ticket.get('lines'):
                price = format_value(prod_line.get('unit_price'))
                price = '0'*(10-len(price)) + price
                qty = str(int(prod_line.get('quantity')))
                qty = '0'*(5-len(qty)) + qty
                lines.append('%s%s%s000%s'%(itbms.get(prod_line.get('tax', ' ')), price, qty, prod_line.get('item_name')))
                if prod_line.get('discount', False):
                    discount = format_value(prod_line.get('discount'))
                    lines.append('p-%s'%discount)

            lines.append('j0Gracias por su visita')
            lines.append('j1Ref.Interna %s' % ticket.get('ref'))

            if len(ticket.get('payments')) > 1:
                for pay in ticket.get('payments'):
                    lines.append("2%s%s"%pay)
            elif len(ticket.get('payments')) == 1:
                pay = ticket.get('payments')[0]
                lines.append("1%s" % pay[0])
            else:
                lines.append("101")

            r[fp.id] = self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_ticket', 'data': simplejson.dumps(lines), 'printer_id': fp.id}, context=context)
        return r
    
    def make_fiscal_ticket_refund(self, cr, uid, ids, ticket={}, context=None):
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
                    value[1] = value[1]+'0'
            return ''.join(value)
        r = {}
        for fp in self.browse(cr, uid, ids):
            lines = [
                'jR%s'%ticket.get('partner').get('document_number'),#RUC_CEDULA
            ]
            jindex = 2
            for elem in (
                ticket.get('partner').get('name'), ticket.get('partner').get('street', ''),
                ticket.get('partner').get('city', ''), ticket.get('partner').get('country', ''),
            ):
                head = elem
                tail = False
                if len(elem) > 40:
                    head = elem[:40]
                    tail = elem[40:]
                if jindex == 2:
                    lines.append('jS%s' % head)
                else:
                    lines.append('j%s%s' % (jindex, head))
                jindex += 1

                if tail:
                    while tail:
                        head = tail
                        if len(tail) > 40:
                            head = tail[:40]
                            tail = tail[40:]
                        else:
                            tail = False
                        lines.append('j%s%s' % (jindex, head))
                        jindex += 1
            lines.append('jF%s-%s' % (fp.fiscal_config_id.serial, ticket.get('internal_number')))

            for prod_line in ticket.get('lines'):
                price = format_value(prod_line.get('unit_price'))
                price = '0'*(10-len(price)) + price
                qty = str(int(prod_line.get('quantity')))
                qty = '0'*(5-len(qty)) + qty
                lines.append('d%s%s%s000%s'%(itbms_ref.get(prod_line.get('tax', '0')), price, qty, prod_line.get('item_name')))
                if prod_line.get('discount', False):
                    discount = format_value(prod_line.get('discount'))
                    lines.append('p-%s'%discount)
            lines.append('j0Gracias por su visita')
            lines.append('j1Ref.Interna %s'%ticket.get('ref'))

            if len(ticket.get('payments')) > 1:
                for pay in ticket.get('payments'):
                    lines.append("2%s%s" % pay)
            elif len(ticket.get('payments')) == 1:
                pay = ticket.get('payments')[0]
                lines.append("1%s" % pay[0])
            else:
                lines.append("101")
            
            r[fp.id] = self.pool.get('fpoc.event').create(cr, uid, {'name': 'make_ticket', 'data': simplejson.dumps(lines), 'printer_id': fp.id}, context=context)

        return r
    
fiscal_printer()

class fpoc_journal(osv.osv):
    _inherit = 'account.journal'

    _columns = {
        'fiscal_printer_code': fields.char('Fiscal Printer Code'),
    }

class fpoc_event(osv.osv):
    _name = 'fpoc.event'

    _columns = {
        'name': fields.char('Event Name', size=16, required=True),
        'data': fields.text('Data', required=True),
        'response': fields.text('Response'),
        'consumed': fields.boolean('Consumed'),
        'printer_id': fields.many2one('fpoc.fiscal_printer', 'Printer'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
