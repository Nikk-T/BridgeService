import asyncio
import logging

log = logging.getLogger("controller")

class LightingController:

    def __init__(self, protocol, unit_map, floor_map, colour_map):

        self.protocol = protocol
        self.unit_map = unit_map
        self.floor_map = floor_map
        self.colour_map = colour_map

    async def unit_status(self, unit_id, status):

        r,g,b = self.colour_map.get(status,(255,255,255))

        for ch in self.unit_map.get(unit_id,[]):

            self.protocol.rgb(ch,r,g,b)

    async def sync_all(self, units):

        self.protocol.suspend()

        for uid,status in units.items():

            await self.unit_status(uid,status)

        self.protocol.resume()

    async def floor_highlight(self, floor, colour):

        self.protocol.suspend()

        for ch in self.floor_map.get(floor,[]):

            self.protocol.rgb(ch,*colour)

        self.protocol.resume()

    async def blackout(self):

        self.protocol.blackout()