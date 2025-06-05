from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"status": "alive", "message": "Auto Rename Bot is running!"})

@routes.get("/health", allow_head=True)
async def health_check(request):
    return web.json_response({"status": "healthy", "service": "auto-rename-bot"})

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
