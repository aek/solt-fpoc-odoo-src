#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import time
import struct

from subprocess import Popen, PIPE
import json

from tempfile import NamedTemporaryFile

utility_path = 'C:/IntTFHKA/IntTFHKA'

def wait_lock():
    timeout = 0
    locked = False
    while timeout < 30:
        if os.path.exists('C:/opt/chrome/odoo.lock'):
            time.sleep(2)
            timeout += 2
        else:
            lock = open('C:/opt/chrome/odoo.lock','w')
            lock.write('locked')
            lock.close()
            locked = True
            break
    if not locked:
        send_response({'Retorno:': 'Impresora Ocupada'})

def clear_lock():
    os.unlink('C:/opt/chrome/odoo.lock')

def send_response(response):
    msg = json.dumps(response)
    sys.stdout.write(struct.pack('I', len(msg)))
    sys.stdout.write(msg)
    sys.stdout.flush()
    clear_lock()
    sys.exit(0)

def check_printer():
    proc = Popen([utility_path, 'CheckFprinter()'], stdout=PIPE, stderr=PIPE)
    check_out, check_err = proc.communicate()
    check_dict = {'Retorno:': check_out}
    if check_dict.get('Retorno:', 'FALSE') == 'FALSE':
        send_response({'error': 'Printer not connected'})

def make_status(status):
    report = NamedTemporaryFile( suffix=".tmp", prefix="tmp__odoo_exec__", delete=False )
    report.close()
    proc = Popen([utility_path, 'UploadStatusCmd(%s)'% status, report.name], stdout=PIPE, stderr=PIPE)
    print_out, check_err = proc.communicate()
    status_file = open(report.name,'rb')
    status_out = status_file.read()[21:29]
    status_file.close()
    return status_out
    
def make_ticket(lines):
    #check_printer()
    log = open('C:/opt/chrome/odoo_exec.log', 'w')
    report = NamedTemporaryFile( suffix=".tmp", prefix="tmp__odoo_exec__", delete=False )
    for line in lines:
        line = unicode(line).encode('utf-8')
        log.write(line)
        log.write("\n")
        report.write(line)
        report.write("\n")
    log.close()
    report.close()
    proc = Popen([utility_path, 'SendFileCmd(%s)'% report.name], stdout=PIPE, stderr=PIPE)
    print_out, check_err = proc.communicate()
    status = make_status('S1')
    print_dict = {'Retorno:': print_out, 'id': status}
    send_response(print_dict)

def make_report(report_type):
    check_printer()
    proc = Popen([utility_path, 'SendCmd(%s)'% report_type], stdout=PIPE, stderr=PIPE)
    report_out, check_err = proc.communicate()
    report_dict = {'Retorno:': report_out}
    send_response(report_dict)

if __name__ == '__main__':
    text_length_bytes = sys.stdin.read(4)
    if len(text_length_bytes) == 0:
      sys.exit(0)
    text_length = struct.unpack('i', text_length_bytes)[0]
    
    # Read the text (JSON object) of the message.
    data = sys.stdin.read(text_length).decode('utf-8')
    message = json.loads(unicode(data).encode('utf-8'))
    
    wait_lock()
    if message.get('action', False) == 'make_ticket':
        make_ticket(message.get('data',{}).get('lines', []))
    if message.get('action', False) == 'make_report':
        make_report(message.get('data',{}).get('type', 'I0X'))
    clear_lock()
