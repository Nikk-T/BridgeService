import asyncio, json, logging, websockets, yaml
from pathlib import Path

from transport import SerialTransport
from protocol import SLSProtocol
from controller import LightingController

logging.basicConfig(level=logging.INFO)

log = logging.getLogger("bridge")

CONFIG_PATH = Path("config/maps.yaml")

def load_maps():

    with open(CONFIG_PATH) as f:

        config = yaml.safe_load(f)

    return (
        config.get("unit_channel_map",{}),
        config.get("floor_channel_map",{}),
        config.get("status_colour",{})
    )

async def main():

    unit_map,floor_map,colour_map = load_maps()

    transport = SerialTransport(115200)

    await transport.connect()

    protocol = SLSProtocol(transport)

    controller = LightingController(protocol,unit_map,floor_map,colour_map)

    async def handle(ws):

        async for msg in ws:

            data = json.loads(msg)

            cmd = data.get("command")

            payload = data.get("payload",{})

            if cmd == "unit_status":

                await controller.unit_status(
                    payload["unit_id"],
                    payload.get("status","off")
                )

            elif cmd == "sync_all":

                await controller.sync_all(payload["units"])

            elif cmd == "blackout":

                await controller.blackout()

            await ws.send(json.dumps({"status":"ok"}))

    async with websockets.serve(handle,"0.0.0.0",8765):

        log.info("Bridge running")

        await asyncio.Future()

asyncio.run(main())