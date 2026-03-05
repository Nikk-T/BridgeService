# -------------------------------------------------
# Hardware command worker
# -------------------------------------------------
async def hardware_worker(queue: asyncio.Queue):
    """
    Async worker that executes hardware commands from a queue.
    Commands are tuples: (command_name:str, args:tuple)
    """
    while True:
        command_name, args = await queue.get()

        try:
            if command_name == "rgb":
                sls.rgb(*args)
            elif command_name == "blackout":
                sls.blackout()
            elif command_name == "suspend":
                sls.suspend()
            elif command_name == "resume":
                sls.resume()
            elif command_name == "keepalive":
                sls.keepalive()
            else:
                log.warning(f"Unknown hardware command: {command_name}")

        except Exception as e:
            log.error(f"Hardware command failed ({command_name}): {e}")
            raise


# -------------------------------------------------
# Serial watchdog
# -------------------------------------------------
async def serial_watchdog(queue: asyncio.Queue, interval: int = 600):
    """
    Periodically sends a keepalive command to prevent SLS960 idle timeout.
    """
    while True:
        await asyncio.sleep(interval)
        await queue.put(("keepalive", ()))
        log.debug("Keepalive sent")


# -------------------------------------------------
# Helper: suspend -> execute -> resume pattern
# -------------------------------------------------
async def execute_with_suspend(queue: asyncio.Queue, commands: list[tuple]):
    """
    Suspend hardware, execute multiple commands, then resume.
    """
    await queue.put(("suspend", ()))
    for cmd_name, args in commands:
        await queue.put((cmd_name, args))
    await queue.put(("resume", ()))


# -------------------------------------------------
# Command processor
# -------------------------------------------------
async def process_command(data: dict, queue: asyncio.Queue):
    """
    Convert websocket JSON commands into hardware queue commands.
    """
    command = data.get("command", "")
    payload = data.get("payload", {})

    if command == "unit_status":
        unit_id = payload["unit_id"]
        status = payload.get("status", "off")
        r, g, b = STATUS_COLOUR.get(status, (255, 255, 255))

        commands = [("rgb", (ch, r, g, b)) for ch in UNIT_CHANNEL_MAP.get(unit_id, [])]
        await execute_with_suspend(queue, commands)

    elif command == "sync_all":
        commands = []
        for uid, status in payload.get("units", {}).items():
            r, g, b = STATUS_COLOUR.get(status, (255, 255, 255))
            for ch in UNIT_CHANNEL_MAP.get(uid, []):
                commands.append(("rgb", (ch, r, g, b)))
        await execute_with_suspend(queue, commands)

    elif command == "floor_highlight":
        floor = payload.get("floor", 0)
        col = payload.get("colour", [100, 150, 255])
        commands = [("rgb", (ch, *col)) for ch in FLOOR_CHANNEL_MAP.get(floor, [])]
        await execute_with_suspend(queue, commands)

    elif command == "blackout":
        await queue.put(("blackout", ()))

    else:
        log.warning(f"Received unknown command: {command}")


# -------------------------------------------------
# WebSocket handler
# -------------------------------------------------
async def handle(ws, queue: asyncio.Queue):
    """
    Handles a single websocket client connection.
    """
    log.info(f"Client connected: {ws.remote_address}")

    async for msg in ws:
        try:
            data = json.loads(msg)

            # Handle ping separately
            if data.get("command") == "ping":
                uptime = int(time.time() - START_TIME)
                await ws.send(json.dumps({"status": "ok", "command": "ping", "uptime": uptime}))
                continue

            # Process hardware command
            await process_command(data, queue)
            await ws.send(json.dumps({"status": "ok"}))

        except Exception as e:
            log.error(f"Command processing error: {e}")
            await ws.send(json.dumps({"status": "error", "message": str(e)}))

