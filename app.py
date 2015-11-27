from flask import Flask, request
from twilio import twiml
from werkzeug.contrib.cache import RedisCache, SimpleCache


app = Flask(__name__)

# Configure the cache
app.cache = SimpleCache()

@app.route('/retry', methods=['GET', 'POST'])
def retry_request():
    """ bar """
    resp = twiml.Response()

    # errored_recently = app.cache.get()

    if 'ErrorCode' in request.values and request.values['ErrorCode'] == '11200':
        # The original request timed out, but let's try it again
        resp.pause(length=10)
        resp.redirect(request.values['ErrorUrl'],
                      method=request.values.get('Method') or 'POST')
    else:
        # There's no hope for this request. Redirect to the provided fallback
        # URL, or intentionally redirect to an error URL to invoke the official
        # Twilio error message
        # resp.redirect('http://fallback.antivoicemail.com/voice-error.xml', method='GET')
        # resp.say('Sorry, an application error has occurred. Goodbye.', voice='alice')
        if 'FallbackUrl' in request.values:
            resp.redirect(request.values['FallbackUrl'],
                          method=request.values.get('FallbackMethod') or 'GET')
        else:
            resp.redirect('/error')
    
    return str(resp)


if __name__ == '__main__':
    app.run(debug=True)
