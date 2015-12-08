# twiml-boomerang

A microservice for your Twilio fallback URLs that gives your original request
another chance.

You don't need to deploy this app yourself to use it. Just set your Twilio
Fallback URLs to:

```
https://retry-then-fallback.herokuapp.com/retry
```

## Why and/or how?

Sometimes you deploy your app on Heroku. Sometimes you use the free tier.

But sometimes Heroku doesn't wake up your dyno within 15 seconds. And Twilio
**never** waits more than 15 seconds for your app to respond to an incoming
phone call or text message.

You can avoid this problem by using twiml-boomerang as your
[Twilio Fallback URL](https://www.twilio.com/docs/api/security/availability-reliability).
Here's how it works:

1. Your Twilio phone number receives a phone call or text message
1. Twilio sends a request to your Voice/Messaging URL looking for instructions
on what to do next
1. After waiting 15 seconds for your Heroku app to wake up, but it doesn't
respond in time
1. Twilio sends a request to your
[Fallback URL](https://www.twilio.com/docs/api/security/availability-reliability),
`https://retry-then-fallback.herokuapp.com/retry`, which is running this repo
1. twiml-boomerang waits **8 seconds**, then redirects Twilio back to your
original URL so your now-awakened Heroku app can handle the request

If Twilio's request to your app fails again within 15 minutes, twiml-boomerang
won't tell Twilio to try again. Instead, it will redirect Twilio to some custom
error TwiML you provide - or just return a 500 error, prompting Twilio to tell
your caller the standard error message.

## Configuration

To use twiml-boomerang with your Twilio app, just set your Voice and/or Messaging
Fallback URLs to:

```
https://retry-then-fallback.herokuapp.com/retry
```

If a Twilio request to your server fails twice within 15 minutes, twiml-boomerang
will return a 500 error. Twilio will then tell your caller the standard error
message.

If you would still like to provide nice, custom error messages to your users,
simply add a `FallbackUrl` query parameter to your fallback URL value.

For example, this fallback URL value will tell Twilio to use the TwiML defined
at http://fallback.antivoicemail.com/voice-error.xml if a request errors twice
within 15 minutes:

```
https://retry-then-fallback.herokuapp.com/retry?FallbackUrl=http://fallback.antivoicemail.com/voice-error.xml
```

By default, twiml-boomerang will instruct Twilio to use a GET request to access
the `FallbackUrl` value. You can change that to a POST request by adding a
`FallbackMethod` value:

```
https://retry-then-fallback.herokuapp.com/retry?FallbackUrl=http://fallback.antivoicemail.com/voice-error.xml?FallbackMethod=POST
```
