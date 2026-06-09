import socket
import threading
import os
import mimetypes
from datetime import datetime

TCP_PORT = 8000
UDP_PORT = 9000
BUFFER_SIZE = 4096

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def log_request(client_ip, path, status):
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"{client_ip} {path} {status}"
    )


def build_response(status_code, reason, body, content_type):
    header = (
        f"HTTP/1.1 {status_code} {reason}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    )

    return header.encode() + body


def get_file_path(path):
    if path == "/":
        path = "/index.html"

    return os.path.join(BASE_DIR, path.lstrip("/"))


def handle_http_client(conn, addr):
    try:
        request = conn.recv(BUFFER_SIZE).decode(errors="ignore")

        if not request:
            conn.close()
            return

        first_line = request.split("\r\n")[0]
        parts = first_line.split()

        if len(parts) < 3:
            response = build_response(
                400,
                "Bad Request",
                b"Bad Request",
                "text/plain"
            )
            conn.sendall(response)
            conn.close()
            return

        method, path, version = parts

        if method != "GET":
            response = build_response(
                405,
                "Method Not Allowed",
                b"Method Not Allowed",
                "text/plain"
            )
            conn.sendall(response)
            conn.close()
            return

        filepath = get_file_path(path)

        if not os.path.exists(filepath):
            error_file = os.path.join(BASE_DIR, "status", "404.html")

            if os.path.exists(error_file):
                with open(error_file, "rb") as f:
                    body = f.read()
            else:
                body = b"<h1>404 Not Found</h1>"

            response = build_response(
                404,
                "Not Found",
                body,
                "text/html"
            )

            conn.sendall(response)
            log_request(addr[0], path, 404)
            conn.close()
            return

        with open(filepath, "rb") as f:
            body = f.read()

        content_type = (
            mimetypes.guess_type(filepath)[0]
            or "application/octet-stream"
        )

        response = build_response(
            200,
            "OK",
            body,
            content_type
        )

        conn.sendall(response)
        log_request(addr[0], path, 200)

    except Exception as e:
        print("SERVER ERROR:", e)

        try:
            response = build_response(
                500,
                "Internal Server Error",
                b"<h1>500 Internal Server Error</h1>",
                "text/html"
            )
            conn.sendall(response)
        except:
            pass

    finally:
        conn.close()


def tcp_server():
    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind(("0.0.0.0", TCP_PORT))
    server.listen(10)

    print(f"[HTTP] Running on port {TCP_PORT}")

    while True:
        conn, addr = server.accept()

        threading.Thread(
            target=handle_http_client,
            args=(conn, addr),
            daemon=True
        ).start()


def udp_echo_server():
    udp = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    udp.bind(("0.0.0.0", UDP_PORT))

    print(f"[UDP] Echo running on port {UDP_PORT}")

    while True:
        data, addr = udp.recvfrom(1024)
        udp.sendto(data, addr)


if __name__ == "__main__":
    threading.Thread(
        target=tcp_server,
        daemon=True
    ).start()

    threading.Thread(
        target=udp_echo_server,
        daemon=True
    ).start()

    while True:
        pass