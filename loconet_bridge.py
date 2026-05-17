import socket


class LocoNetBridge:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port
        self.sock = None

    def connect_bridge(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
    
    def connect_serial(self, com_port):
        return self.send(f"CONNECT_SERIAL com={com_port}")

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, command: str) -> str:
        if not self.sock:
            raise RuntimeError("No conectado al bridge C#")

        self.sock.sendall((command.strip() + "\n").encode("utf-8"))

        data = b""
        while not data.endswith(b"\n"):
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("Conexión cerrada por el bridge")
            data += chunk

        return data.decode("utf-8-sig").strip().replace("\ufeff", "")

    def ping(self):
        return self.send("PING")

    def connect_loconet(self, ip, port):
        return self.send(f"CONNECT ip={ip} port={port}")

    def disconnect_loconet(self):
        return self.send("DISCONNECT")

    def lncv_start(self, article, addr):
        return self.send(f"LNCV_START article={article} addr={addr}")

    def lncv_read(self, cv):
        return self.send(f"LNCV_READ cv={cv}")

    def lncv_write(self, cv, value):
        return self.send(f"LNCV_WRITE cv={cv} value={value}")

    def lncv_stop(self):
        return self.send("LNCV_STOP")