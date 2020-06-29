from aiohttp import web

# build code
routes = web.RouteTableDef()


@routes.post('/submit')
async def submission(request):
    message = await request.json()
    print('message received:{message}')
    return web.json_response(message)

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=8010)