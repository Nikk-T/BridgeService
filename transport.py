import serial, asyncio, glob, logging

log = logging.getLogger("transport")

class SerialTransport:

    def __init__(self, baud):
        self.baud = baud
        self.ser = None

    def detect_port(self):
        for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*"):
            ports = glob.glob(pattern)
            if ports:
                return ports[0]
        return None

    async def connect(self):

        while True:

            try:

                port = self.detect_port()

                if not port:
                    log.warning("No serial device found")
                    await asyncio.sleep(3)
                    continue

                self.ser = serial.Serial(port, self.baud, timeout=1)

                log.info(f"Serial connected: {port}")

                return

            except Exception as e:

                log.error(f"Serial connection failed: {e}")

                await asyncio.sleep(3)

    def write(self, data):

        if not self.ser:
            raise RuntimeError("Serial not connected")

        self.ser.write(data)
        self.ser.flush()