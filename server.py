"""
HTTP Proxy Server
1. Modify browser settings to use this server as the proxy server
2. Testing -
curl http://www.example.com/
"""

import atexit
import logging
import socket
import sys
import threading

BACKLOG = 5
MAX_DATA_RECV = 999999
PORT = 9999  # port for proxy server
HOST = ''  # blank for localhost
BLOCKED = ["facebook"]
s = None


def main():
    global s
    logging.debug("Proxy server running on " + str(HOST) + ":" + str(PORT))

    try:
        # create the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # associate the socket to host and port
        s.bind((HOST, PORT))

        # listen
        s.listen(BACKLOG)

    except socket.error as e:
        if s:
            s.close()
        print("Could not open socket:", e.message)
        sys.exit(1)

    while True:
        # get the connection from client
        conn, client_addr = s.accept()

        # start a thread to handel the request from the client
        # _thread.start_new_thread(proxy_thread, (conn, client_addr))
        threading.Thread(target=proxy_thread, args=(conn, client_addr)).start()


def proxy_thread(conn, client_addr):
    global s
    # get the request
    request = conn.recv(MAX_DATA_RECV)

    try:
        logging.debug("Request - " + str(request))
        first_line = str(request).split('\n')[0]
        # print(first_line)

        url = first_line.split(' ')[1]
        # printout("Request", first_line, client_addr)
        logging.debug("URL - " + url)

        for i in range(len(BLOCKED)):
            if BLOCKED[i] in url:
                logging.debug("Blacklisted: " + str(first_line) + "  " + str(client_addr))
                conn.close()

                logging.debug("Request: " + str(first_line) + "  " + str(client_addr))

        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]
        logging.debug("Temp - " + str(temp))

        port_pos = temp.find(":")
        webserver_poc = temp.find("/")
        if webserver_poc == -1:
            webserver_poc = len(temp)

        webserver = ""
        port = -1
        if port_pos == -1 or webserver_poc < port_pos:
            port = 80
            webserver = temp[:webserver_poc]
        else:
            port = int(temp[(port_pos + 1):][:webserver_poc - port_pos - 1])
            webserver = temp[:port_pos]

        logging.debug("Webserver: " + webserver + " Port: " + str(port))
        logging.debug("---------------------------------------------------")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((webserver, port))
            s.send(request)

            while True:
                data = s.recv(MAX_DATA_RECV)

                if len(data) > 0:
                    conn.send(data)
                else:
                    break
            s.close()
            conn.close()
        except socket.error as e:
            if s:
                s.close()
            if conn:
                conn.close()
            logging.debug("Peer Reset: " + str(first_line) + "  " + str(client_addr))
            sys.exit(1)
    except Exception as e:
        logging.error("Exception - " + str(e))


def exit_function():
    if s:
        try:
            s.close()
            logging.debug("Socket closed successfully. Bye!")
        except Exception as e:
            logging.debug("Error while closing the socket - ", e)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    atexit.register(exit_function)
    main()
