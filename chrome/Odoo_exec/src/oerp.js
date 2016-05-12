//
// OpenERP Session object.
//

//
// Counter to make unique messages in same connection.
//
var idCounter = 0;
uniqueId = function(prefix) {
  var id = ++idCounter + '';
  return prefix ? prefix + id : id;
};

//
// Class to create a session associated to a server.
//
oerpSession = function(server, session_id) {
    EventTarget.call(this);

    this.server = server;
    this.session_id = session_id;
    this.id = uniqueId('p');

    this.onlogout = null;
    this.onmessage = null;
    this.onlogerror = null;
    this.onexpired = null;
    this.onchange = null;
    
    this.lastOperationStatus = 'No info';
    this.event_tasks = {}
    //
    // Init general server event listener.
    //
    this.set_server_events = function(params, event_function_map, data, return_callback, callback, retry) {
        var self = this;
        //console.log("Polling for print task ", params);

        var _callback = function() {
            if (callback) callback();
        };

        async.each(takeKeys(event_function_map), function(event_key, __callback) {
                var event_callback = function(ev) {
                    event_function_map[ev.type](self, ev.event_id, ev.data, return_callback);
                };
                self.addListener(event_key, event_callback, false);
                __callback();
            },
            _callback);
        function find_events(){
            self._call('fpoc.event', 'search',[
                [['printer_id.session_id','=',self.session_id], ['consumed','=',false]]
            ], {}, function(e, fps) {
                if (e != 'error') {
                    fps_def = []
                    if(fps.length > 0){
                        async.each(fps, function(fp) {
                            if(self.event_tasks[fp] === undefined){
                                self.event_tasks[fp] = true;
                                deff = self._call('fpoc.event', 'read',[ fp, []], {}, function(e, event_data) {
                                    self.dispatchEvent({type: event_data.name, event_id: fp, data: event_data});
                                    console.log(event_data);
                                });
                                fps_def.push(deff);
                            }
                        });
                    }
                    $.when(fps_def).done(function(){
                        setTimeout(find_events, 3000);
                    });
                } else {
                    setTimeout(find_events, 3000);
                }
            });
        }
        setTimeout(find_events, 3000);
    };

    //
    // Init control event-sent server listener.
    //
    this.init_server_events = function(event_function_map, callback) {
        var self = this;
        var return_callback = function(mess, res) {
            if (mess == 'error') {
                setTimeout(function() { self.init_server_events(event_function_map, callback); }, 3000);
            }
        };

        var retry = function(event_function_map) {
            setTimeout(function() { self.init_server_events(event_function_map, callback); }, 3000);
        };

        if (this.session_id) {
            this.set_server_events("session_id=" + this.session_id + "&printer_id=" + printer_id_tpl,
                    event_function_map,
                    null,
                    return_callback,
                    callback,
                    retry);
        } else {
            retry(event_function_map);
        }
    };

    //
    // Execute expiration event
    //
    this._onexpiration = function(event) {
        var self = this;
        self.session_id = null;
        if (self.onexpired) self.onexpired(event);
    };

    //
    // RPC wrapper
    //
    this.rpc = function(url, params, callback) {
        var self = this;
        var data = {
            jsonrpc: "2.0",
            method: "call",
            params: params,
            id: Math.floor(Math.random() * 1000 * 1000 * 1000)
        };
        xhr = $.ajax({
            url: this.server + url,
            dataType: 'json',
            type: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            timeout: 10000,
            xhrFields: {
                withCredentials: true
            }
        });

        var result = xhr.pipe(function(result) {
            if (result.error !== undefined) {
                //console.error("Server application error", result.error);
                self.dispatchEvent({type: 'error', 'event': $.Event()});
                callback("error", null);
                return $.Deferred().reject("server", result.error);
            } else {
                return result.result;
            }
        }, function() {
            //console.error("JsonRPC communication error", _.toArray(arguments));
            var def = $.Deferred();
            self.dispatchEvent({type: 'error', 'event': $.Event()});
            callback("error", null);
            return def.reject.apply(def, ["communication"].concat(Array.prototype.slice.call(arguments)));
        });
        // FIXME: jsonp?
        result.abort = function () { xhr.abort && xhr.abort(); };

        result.then(function (result) {
            callback("done", result);
            return result;
        }, function(type, error, textStatus, errorThrown) {
            if (type === "server") {
                if (error.code === 100) {
                    self.session_id = false;
                }
                return $.Deferred().reject(error, $.Event());
            } else {
                var nerror = {
                    code: -32098,
                    message: "XmlHttpRequestError " + errorThrown,
                    data: {type: "xhr"+textStatus, debug: error.responseText, objects: [error, errorThrown] }
                };
                return $.Deferred().reject(nerror, $.Event());
            }
            callback("error", null);
        });
        return result;


        /*var xhr = new XMLHttpRequest();
        var self=this;
        var args = "?jsonp=_&id="+this.id;
        //if (self.session_id) {
        //    params.session_id = self.session_id;
        //}
        var request = { 'params': params };
        args = args + "&r="+encodeURIComponent(JSON.stringify(request || {}));

        xhr.ontimeout = function(event) {
            self.dispatchEvent({type: 'error', 'event': event});
            callback("timeout", null);
        };
        xhr.onerror = function(event)   {
            self.dispatchEvent({type: 'error', 'event': event});
            callback("error", null);
        };
        xhr.onload = function(event) {
            r = event.currentTarget.response;
            try {
                response = JSON.parse(r.substring(2,r.length-2));
            } catch(err) {
                self.dispatchEvent({type: 'error', 'event': event});
                callback("error", null);
                return;
            }
            if (response.error) {
                console.error(response.error);
                callback("error", response.error);
                if (response.error.code == 300) self._onexpiration(event);
            } else {
                self.id = response.id || self.id;
                if (self.onmessage) {
                    self.onmessage("in", response.result);
                }
                callback("done", response.result);
            }
        };
        xhr.open("GET", this.server + url + args, false);
        xhr.timeout = 10000;
        xhr.withCredentials = true;
        xhr.send();
        if (self.onmessage) {
            self.onmessage("out", [url, args]);
        }*/
    };

    //
    // Read list of databases on the server.
    //
    this.get_database_list = function(callback) {
        var self=this;
        self.rpc('/web/database/get_list', {}, callback);
    };

    //
    // Get session information.
    //
    this.get_session_info = function(callback) {
        var self=this;
        var old_uid = self.uid;
        self.rpc('/web/session/get_session_info', {  }, function(mess, result){
            if (mess == "done") {
                self.db = result.db;
                self.username = result.username;
                self.user_context = result.user_context;
                self.uid = result.uid;
                self.session_id = result.session_id;
                if (self.uid) {
                    self.dispatchEvent('login');
                } else {
                    self.dispatchEvent('expired');
                }
            } else {
                if (!self.uid) {
                    self.dispatchEvent('login_error');
                }
            }
            if (callback) {
                callback(mess, self);
            }
        });
    };

    //
    // Authenticate user in a db with a password.
    // NADIE LO USA!
    //
    this.authenticate = function(db, login, password, callback) {
        var self = this;
        var old_uid = self.uid;
        var params = { db: db, login: login, password: password, base_location: self.server };
        var _callback = function(mess, result) {
            if (mess == "done") {
                self.db = result.db;
                self.uid = result.uid;
                self.session_id = result.session_id;
                self.username = login;
                if (old_uid != self.uid && self.uid !== null) {
                    self.dispatchEvent('login');
                }
                if (self.uid === null) {
                    self.dispatchEvent('login_error');
                }
            }
            if (callback) {
                callback(mess, result && result.uid && result.uid !== null);
            }
        };
        self.rpc("/web/session/authenticate", params, _callback);
    };

    //
    // Logout
    //
    this.logout = function(callback) {
        var self = this;
        var params = {};
        var _callback = function(mess, result) {
            self.username = null;
            self.uid = null;
            self.session = null;
            self.spools = {};
            self.dispatchEvent('logout');
            if (callback) { callback(mess); }
        };
        self.rpc("/web/session/destroy", params, _callback);
    };

    //
    // Return value to the server.
    //
    this.send = function(value, callback) {
        var self = this;
        var _callback = function(mess, result) {
            self.dispatchEvent({type: 'send', 'message': mess, 'result': result});
            if (callback) {
                callback(mess, result);
            }
        };
        self._call('fpoc.event', 'write', [ value.event_id, {'consumed': true, 'response': JSON.stringify(value.response)} ], {}, _callback);
    };

    //
    // Check if server is online
    //
    this.check = function(callback) {
        var self = this;
        var _callback = function(mess, result) {
            self.dispatchEvent({type: 'check', 'message': mess, 'result': result});
            if (callback) {
                callback(mess, result);
            }
        };
        self.rpc("/web/session/check", {}, _callback);
    };

    //
    // Init the session in the server if exists.
    //
    this.init = function(callback) {
        var self = this;
        var _callback = callback || function(mess, obj) {
            if (mess != "logged") {
                console.warn("Session is not open. Reason: ", mess);
            } else {
                console.warn("Session is open.");
            }
        };
        // Setup session information.
        if (self.session_id) {
            self.get_session_info(_callback);
        } else {
            self.dispatchEvent('error');
            _callback("notlogin", this);
        }
    };

    this._call = function(model, method, args, kwargs, callback) {
        var self = this;
        return self.rpc("/web/dataset/call_kw", {
            model: model,
            method: method,
            args: args,
            kwargs: kwargs
        }, callback);
    };
    
    this.clean_printers = function(callback) {
        var self = this;
        if (self.printers) {
            async.each(self.printers, function(e) { e.close(); }, callback);
        } else
            callback();
    };
    
    this.update = function(_callback) {
        var self = this;

        console.debug('[SES] Updating printers.');
        if (self.session_id && printer_id_tpl && self.uid) {
            self._call('fpoc.fiscal_printer', 'search',[ [['name','=',printer_id_tpl]] ], {}, function(e, fps) {
                if (e != 'error') {
                    if(fps.length > 0){
                        var d = new Date();
                        self._call('fpoc.fiscal_printer', 'write',
                            [ fps, {
                                'session_id':self.session_id,
                                'lastUpdate': d,
                            } ], {}, function(e1, r) { _callback(); });
                    } else{
                        self._call('fpoc.disconnected', 'search', [ [['name','=',printer_id_tpl]] ], {}, function(e1, fpd) {
                            if (e1 != 'error') {
                                if(fpd.length == 0){
                                    self._call('fpoc.disconnected', 'create',[{
                                        'name': printer_id_tpl,
                                        'user_id': self.uid,
                                        'session_id':self.session_id,
                                    }], {}, function(e2, r) { _callback(); });
                                }
                            }
                        });
                    }
                } else{
                    _callback();
                }
            });
        } else {
            _callback();
        };
    };
};

oerpSession.prototype = new EventTarget();
oerpSession.constructor = oerpSession;

// vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
