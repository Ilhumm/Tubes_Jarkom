import socket
import sys
import time
import statistics

PROXY_IP = "192.168.0.153"
PROXY_PORT = 8888

SERVER_IP = "192.168.0.149"
UDP_PORT = 9000


BUFFER_SIZE = 4096

def tcp_mode():

    path = input(
        "Path [/index.html]: "
    ).strip()

    if not path:
        path = "/index.html"

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {PROXY_IP}\r\n"
        f"Connection: close\r\n\r\n"
    )

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    sock.connect(
        (
            PROXY_IP,
            PROXY_PORT
        )
    )

    sock.sendall(
        request.encode()
    )

    response = b""

    while True:
        data = sock.recv(
            BUFFER_SIZE
        )

        if not data:
            break

        response += data

    sock.close()

    print(
        response.decode(
            errors="ignore"
        )
    )


def udp_mode():

    total_packets = 10

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.settimeout(1)

    rtts = []

    received = 0
    total_bytes = 0

    test_start = time.time()

    for seq in range(
        total_packets
    ):

        send_time = time.time()

        payload = (
            f"Ping {seq} "
            f"{send_time}"
        )

        try:

            sock.sendto(
                payload.encode(),
                (
                    SERVER_IP,
                    UDP_PORT
                )
            )

            data, addr = sock.recvfrom(
                1024
            )

            recv_time = time.time()

            rtt = (
                recv_time
                - send_time
            ) * 1000

            rtts.append(rtt)

            received += 1

            total_bytes += len(data)

            print(
                f"Reply "
                f"seq={seq} "
                f"RTT={rtt:.2f} ms"
            )

        except socket.timeout:

            print(
                f"Request timeout "
                f"seq={seq}"
            )

    duration = (
        time.time()
        - test_start
    )

    print("\n==========")

    loss = (
        (
            total_packets
            - received
        )
        / total_packets
    ) * 100

    if rtts:

        min_rtt = min(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        max_rtt = max(rtts)

        diffs = []

        for i in range(
            1,
            len(rtts)
        ):
            diffs.append(
                abs(
                    rtts[i]
                    - rtts[i - 1]
                )
            )

        jitter = (
            statistics.stdev(
                diffs
            )
            if len(diffs) > 1
            else 0
        )

        throughput = (
            total_bytes
            / duration
        ) / 1024

        print(
            f"Min RTT : "
            f"{min_rtt:.2f} ms"
        )

        print(
            f"Avg RTT : "
            f"{avg_rtt:.2f} ms"
        )

        print(
            f"Max RTT : "
            f"{max_rtt:.2f} ms"
        )

        print(
            f"Packet Loss : "
            f"{loss:.2f}%"
        )

        print(
            f"Jitter : "
            f"{jitter:.2f} ms"
        )

        print(
            f"Throughput : "
            f"{throughput:.2f} KB/s"
        )

    sock.close()


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python client.py tcp"
        )

        print(
            "python client.py udp"
        )

        sys.exit()

    mode = sys.argv[1]

    if mode == "tcp":
        tcp_mode()

    elif mode == "udp":
        udp_mode()

    else:
        print(
            "Unknown mode"
        )