from aiohttp import web
from twilio import twiml
from urllib.parse import urlparse

import asyncio
import os
import redis


async def retry_request(request):
    """
    Attempts to recover the call if it was because of a timeout,
    otherwise returns an error message
    """
    # Get a combined dictionary of our POST and GET data
    post_data = await request.post()
    data = {**post_data, **request.GET}

    # If there's no ErrorCode in the data, then this request didn't originate
    # from an error - someone likely misconfigured their webhooks
    if 'ErrorCode' not in data:
        return web.Response(status=400)

    error_url = data['ErrorUrl']
    error_hostname = urlparse(error_url).hostname

    resp = twiml.Response()
    if data['ErrorCode'] == '11200' and not request.app.cache.exists(error_hostname):
        # Twilio couldn't reach the original URL. Let's wait 8 seconds and then
        # tell Twilio to try again
        await asyncio.sleep(8.0)

        # Redirect Twilio back to the original URL with the original method
        resp.redirect(error_url,
                      method=data.get('Method') or 'POST')

        # Also add the ErrorUrl's hostname to our cache for 15 minutes
        # so we know to give up on this request if Twilio comes back again
        request.app.cache.setex(error_hostname, True, 60 * 15)
    else:
        # There's no hope for this request. Redirect to the provided fallback
        # URL, or return a 500 error to invoke the offical Twilio error message
        if 'FallbackUrl' in data:
            resp.redirect(data['FallbackUrl'],
                          method=data.get('FallbackMethod') or 'GET')
        else:
            return web.Response(status=500)

    return web.Response(text=str(resp),
                        content_type='application/xml')

# Initialize the app
app = web.Application()

# Initialize the Redis cache
app.cache = redis.from_url(os.environ.get('REDIS_URL', ''))

# Add the route
app.router.add_route('POST', '/retry', retry_request)

if __name__ == '__main__':
    # Start the development server
    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, '0.0.0.0', 8080)
    srv = loop.run_until_complete(f)
    print('Serving on', srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(handler.finish_connections(1.0))
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.finish())
    loop.close()
