var run_id = chrome.runtime.id;
var user_ip = null;
chrome.system.network.getNetworkInterfaces(function(details){
    user_ip = details[0].address;
    printer_id_tpl = run_id+':'+user_ip;
});

//
// Control server events.
//
control_server_events = {
    'list_printers': function(session, event_id, event_data, printers, callback) {
        console.debug("[EVENT] Query local printers.");
        var tmpPrinters = [];
        var key = printer_id_tpl;
        tmpPrinters.push({
            'uid': session.uid,
            'sid': session.session_id,
            'name': key,
            'fiscalStatus': true,
            'printerStatus': true,
        });
        console.log(key);
        console.log(printers);
        session.send({'event_id': event_id,'printer_id': key, 'printers': tmpPrinters}, callback);
    },
    'make_ticket': function(session, event_id, event_data, printers, callback) {
        console.debug("[EVENT] Make Ticket.");
        var printer_id = event_data.name;
        chrome.runtime.sendNativeMessage('solt.native.odoo.exec', {'action': 'make_ticket', 'data': event_data}, function(response) {
            console.log("Received " + JSON.stringify(response));
            session.send({'event_id': event_id, 'printer_id': printer_id, 'response': response}, callback);
        });
    },
    'make_report': function(session, event_id, event_data, printers, callback) {
        console.debug("[EVENT] Make Report.");
        var printer_id = event_data.name;
        chrome.runtime.sendNativeMessage('solt.native.odoo.exec', {'action': 'make_report', 'data': event_data}, function(response) {
            console.log("Received " + JSON.stringify(response));
            session.send({'event_id': event_id, 'printer_id': printer_id, 'response': response}, callback);
        });
    },
    'get_status': function(session, event_id, event_data, printers, callback) {
        console.debug("[EVENT] Get Status.");
        var printer_id = event_data.name;
        
        chrome.runtime.sendNativeMessage('solt.native.odoo.exec',{'action': 'check_printer'}, function(response) {
          console.log("Received " + JSON.stringify(response));
        });
        
        var response = {'event_id': event_id, 'printer_id': printer_id, 'strPrinterStatus': 'active', 'strFiscalStatus': 'active'};
        session.send(response,callback);
    },
};

printer_server_events = {};
// To take params from event:
// var parms = JSON.parse(ev.data);

// vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
