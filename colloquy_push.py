import weechat
import json
import socket
import ssl

weechat.register("colloquy_push", "Benjie", "0.1", "MIT", "Implements Colloquy's iOS push notifications", "", "")

clients_in_progress = {}
known_clients = None
known_clients_string = weechat.config_get_plugin('known_clients')
if known_clients_string is not None:
    try:
        known_clients = json.loads(known_clients_string)
    except: pass
if type(known_clients) is not dict:
    known_clients = {}

def push_cb(data, signal, signal_data):
    # signal:
    #   freenode,irc_out_PUSH
    # signal_data:
    #   relay_client_7;PUSH add-device c0000000000000000000000000000000000000000000000000000000000000b6 :Device Name Here
    #   relay_client_7;PUSH service colloquy.mobi 7906
    #   relay_client_7;PUSH connection W0000000004 :Weechat
    #   relay_client_7;PUSH highlight-sound :Beep 1.aiff
    #   relay_client_7;PUSH message-sound :Stoof.aiff
    #   relay_client_7;PUSH end-device
    client, rest = signal_data.split(";", 1)
    
    components = rest.split(" ", 2)
    components.append('')
    cmd = components[1].strip()
    rest = components[2].strip()

    if cmd == "add-device":
        clients_in_progress[client] = {}
        token, name = rest.split(" ", 1)
        name = name.lstrip(':')
        clients_in_progress[client]['token'] = token
        clients_in_progress[client]['name'] = name
    elif client in clients_in_progress:
        if cmd == "end-device":
            weechat.prnt("", "colloquy_push: received all details from device: %s" % json.dumps(clients_in_progress[client]))
            known_clients[clients_in_progress[client]['token']] = clients_in_progress[client]
            weechat.config_set_plugin('known_clients', json.dumps(known_clients))
            del clients_in_progress[client]
        elif cmd == "service":
            server, port = rest.split(" ")
            port = int(port)
            clients_in_progress[client]['server'] = server
            clients_in_progress[client]['port'] = port
        elif cmd == "connection":
            connection, connection_name = rest.split(" ", 1)
            clients_in_progress[client]['connection'] = connection
            clients_in_progress[client]['connection_name'] = connection_name
        elif cmd == "highlight-sound":
            rest = rest.lstrip(":")
            clients_in_progress[client]['highlight-sound'] = rest
        elif cmd == "message-sound":
            rest = rest.lstrip(":")
            clients_in_progress[client]['message-sound'] = rest
        else:
            weechat.prnt("", "colloquy_push: warning: didn't understand command: %s" % cmd)
    return weechat.WEECHAT_RC_OK

weechat.hook_signal("*,irc_outtags_push", "push_cb", "")

# Hook privmsg/hilights
weechat.hook_print("", "irc_privmsg", "", 1, "notify_show", "")

# Functions
def notify_show(data, bufferp, uber_empty, tagsn, isdisplayed, ishilight, prefix, message):

    #get local nick for buffer
    mynick = weechat.buffer_get_string(bufferp,"localvar_nick")

    # only notify if the message was not sent by myself
    if (weechat.buffer_get_string(bufferp, "localvar_type") == "private") and (prefix!=mynick):
        show_notification(prefix, prefix, message)

    elif ishilight == "1":
        buffer = (weechat.buffer_get_string(bufferp, "short_name") or weechat.buffer_get_string(bufferp, "name"))
        show_notification(buffer, prefix, message)

    return weechat.WEECHAT_RC_OK

def show_notification(chan, nick, message):
    for token, details in known_clients.items():
        payload = {'device-token':token, 'message': message, 'sender': nick, 'room': chan, 'server': details['connection'], 'badge': 1, 'sound': details['highlight-sound']}
        server = details['server']
        port = details['port']
        port = int(port)
        weechat.prnt("", "colloquy_push: sending %s to (%s:%d)" % (json.dumps(payload), server, port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)

        # require a certificate from the server
        ssl_sock = ssl.wrap_socket(s)
        #, ca_certs="/etc/ca_certs_file", cert_reqs=ssl.CERT_REQUIRED)
        ssl_sock.connect((server, port))
        ssl_sock.write("%s\n" % json.dumps(payload))
        ssl_sock.close()
