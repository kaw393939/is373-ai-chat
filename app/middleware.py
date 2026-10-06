"""Bound request memory even when Content-Length is absent or dishonest."""

from starlette.responses import JSONResponse


class BodyLimit:
    def __init__(self, app, maximum=65536):
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.maximum:
                return await JSONResponse({"detail": "Request body too large"}, 413)(
                    scope, receive, send
                )
            if not message.get("more_body", False):
                break
        supplied = False

        async def bounded_receive():
            nonlocal supplied
            if not supplied:
                supplied = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)
