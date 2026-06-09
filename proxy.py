import socket
import threading
import os
import hashlib
import time
from datetime import datetime

PROXY_PORT = 8888

SERVER_IP = "172.20.10.3"
SERVER_PORT = 8000

BUFFER_SIZE = 4096

CACHE_DIR = "cache"

os.makedirs(CACHE_DIR, exist_ok=True)


def log(client_ip, url, cache_status, response_time):
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"{client_ip} {url} "
        f"{cache_status} "
        f"{response_time:.2f} ms"
    )


def get_cache_filename(path):
    return os.path.join(
        CACHE_DIR,
        hashlib.md5(path.encode()).hexdigest()
    )


def send_error(conn, code, reason):
    body = f"<h1>{code} {reason}</h1>".encode()

    response = (
        f"HTTP/1.1 {code} {reason}\r\n"
        f"Content-Type: text/html\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() + body

    conn.sendall(response)


def handle_client(client_conn, client_addr):
    start = time.time()

    try:
        request = client_conn.recv(BUFFER_SIZE)

        if not request:
            client_conn.close()
            return

        request_line = request.decode(
            errors="ignore"
        ).split("\r\n")[0]

        parts = request_line.split()

        if len(parts) < 3:
            send_error(
                client_conn,
                400,
                "Bad Request"
            )
            client_conn.close()
            return

        method, path, version = parts

        cache_file = get_cache_filename(path)

        # ======================
        # CACHE HIT
        # ======================

        if os.path.exists(cache_file):

            with open(cache_file, "rb") as f:
                response = f.read()

            client_conn.sendall(response)

            elapsed = (
                time.time() - start
            ) * 1000

            log(
                client_addr[0],
                path,
                "HIT",
                elapsed
            )

            client_conn.close()
            return

        # ======================
        # CACHE MISS
        # ======================

        try:
            server_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            server_socket.settimeout(5)

            server_socket.connect(
                (
                    SERVER_IP,
                    SERVER_PORT
                )
            )

            server_socket.sendall(request)

            response = b""

            while True:
                data = server_socket.recv(
                    BUFFER_SIZE
                )

                if not data:
                    break

                response += data

            server_socket.close()

        except socket.timeout:
            send_error(
                client_conn,
                504,
                "Gateway Timeout"
            )
            client_conn.close()
            return

        except:
            send_error(
                client_conn,
                502,
                "Bad Gateway"
            )
            client_conn.close()
            return

        with open(cache_file, "wb") as f:
            f.write(response)

        client_conn.sendall(response)

        elapsed = (
            time.time() - start
        ) * 1000

        log(
            client_addr[0],
            path,
            "MISS",
            elapsed
        )

    except Exception as e:
        print("Proxy Error:", e)

    finally:
        client_conn.close()


def start_proxy():
    proxy_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    proxy_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    proxy_socket.bind(
        ("0.0.0.0", PROXY_PORT)
    )

    proxy_socket.listen(20)

    print(
        f"[PROXY] Listening on {PROXY_PORT}"
    )

    while True:
        conn, addr = proxy_socket.accept()

        threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        ).start()


if __name__ == "__main__":
    start_proxy()