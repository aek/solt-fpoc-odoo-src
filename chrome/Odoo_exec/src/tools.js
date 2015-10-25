//
// Buffer Conversions
//

var port = null;
function _base64ToArrayBuffer(base64) {
    var binary_string =  window.atob(base64);
    var len = binary_string.length;
    var bytes = new Uint8Array( len );
    for (var i = 0; i < len; i++)        {
        var ascii = binary_string.charCodeAt(i);
        bytes[i] = ascii;
    }
    return bytes.buffer;
}

function ab2str(buf) {
  return String.fromCharCode.apply(null, new Uint8Array(buf));
}

function str2ab(str) {
  var buf = new ArrayBuffer(str.length); // 1 bytes for each char. Only ASCII.
  var bufView = new Uint8Array(buf);
  for (var i=0, strLen=str.length; i<strLen; i++) {
    bufView[i] = str.charCodeAt(i);
  }
  return buf;
}

function concatBuf(buf1, buf2) {
    var buf = new ArrayBuffer(buf1.byteLength + buf2.byteLength);
    var buf1View = new Uint8Array(buf1);
    var buf2View = new Uint8Array(buf2);
    var bufView = new Uint8Array(buf);
    for (var i=0; i < buf1.byteLength; i++) {
        bufView[i] = buf1View[i];
    }
    for (var j=0; i < buf2.byteLength; j++) {
        bufView[buf1.byteLength+j] = buf2View[j];
    }
    return buf;
}

//
// String tools
//
function pad(n, width, z) {
  z = z || '0';
  n = n + '';
  return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}


//
// Take keys of a dict
//
function takeKeys(dict) {
    keys = [];
    for (var key in dict) {
        if(dict.hasOwnProperty(key)){
            keys.push(key);
        }
    }
    return keys;
}


var local_printers = {};
var local_devices = {};

var query_local_printers = function(callback, onchange) {
    var change = false;
    
    var inLocalPrinters = function(device, callback) {
        var inlp = false;
        for (var p in local_printers) {
            inlp = inlp || local_printers[p].interface.sameDevice(device);
        }
        return inlp;
    };

    var cleanPrinters = function(callback) {
        // Remove disconnected printers.
        async.eachSeries(takeKeys(local_printers),
                function(pid, __callback__) {
                    local_printers[pid].get_status(function(result) {
                        if (typeof result == 'undefined' || ('error' in result  && result.error == 'disconnected')) {
                            // Remove printer spool.
                            if (session) { session.del_printer(local_printers[pid]); }
                            // Close drivers.
                            local_printers[pid].close();
                            // Remove printer from list.
                            delete local_printers[pid];
                            change=true;
                        }
                        __callback__();
                    });
                },
                function() {
                    callback();
                });
    };

    cleanPrinters(function() {});
};
// vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
