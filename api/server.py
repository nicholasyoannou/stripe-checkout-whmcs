"""
server.py, remade in FastAPI
Made by ©️ Nicholas Yoannou, 2023 Jan 28
Python 3.6 or newer required.
"""

from dotenv import load_dotenv


def trueFalse(booleanStr: str):
    if booleanStr.lower() == 'true':
        return True
    else:
        return False


load_dotenv()  # take environment variables from .env. # not sure if this does this automatically but my darn laptop never does it properly, here you go lmao

import os
import calendar
import requests
import time
import decimal
import stripe

# This is your secret API key.
stripe.api_key = os.environ['STRIPE_SECRET_APIKEY']

import redis

r = redis.Redis(
    host=os.environ['REDIS_HOST'],
    port=int(os.environ['REDIS_PORT']),
    password=os.environ['REDIS_PASSWORD'],
    ssl=trueFalse(os.environ['REDIS_SSL'])
)

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(docs_url=None)

WHMCS_API_URL = os.environ['WHMCS_API_URL']
WHMCS_IDENTIFIER = os.environ['WHMCS_IDENTIFIER']
WHMCS_SECRET = os.environ['WHMCS_SECRET']
WHMCS_ACCESS_KEY = os.environ['WHMCS_ACCESS_KEY']

YOUR_DOMAIN = os.environ['WHMCS_DOMAIN']
# BILLING_STR_DOMAIN = 'http://127.0.0.1:4242' # intended for localhost testing
BILLING_STR_DOMAIN = os.environ['API_DOMAIN']
BUSINESSNAME_SHORT = os.environ['BUSINESS_NAME_SHORT']

origins = [
    YOUR_DOMAIN,
    "https://stripe.com",
    "https://checkout.stripe.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/makePaymentInvoice')
def create_checkout_session(invoice_number: str = Form(), amount: str = Form(), customeremail: str = Form()):
    reqRed = r.hgetall(invoice_number)
    if reqRed != None and not (str(reqRed) == '{}') and not (str(reqRed) == ''):
        return RedirectResponse(str(reqRed[b'session_link'])[2:-1], status_code=303)
    # try:
    invNumber = invoice_number

    # Check if invoice number belongs to email specified
    check = requests.post(WHMCS_API_URL,
                          data={'action': 'GetInvoice', 'identifier': WHMCS_IDENTIFIER, 'secret': WHMCS_SECRET,
                                'accesskey': WHMCS_ACCESS_KEY,
                                'invoiceid': invNumber,
                                'responsetype': 'json'}).json()  # action GetInvoice, to get UserID of invoice
    check2 = requests.post(WHMCS_API_URL,
                           data={'action': 'GetClientsDetails', 'identifier': WHMCS_IDENTIFIER, 'secret': WHMCS_SECRET,
                                 'accesskey': WHMCS_ACCESS_KEY,
                                 'clientid': check['userid'], 'responsetype': 'json'}).json()[
        'email']  # action GetClientsDetails, using UserID
    if not (check2 == customeremail):
        return 'Validation unsuccessful. The billing panel client email is different from the one paid on checkout. Please contact support.'

    if decimal.Decimal(check['subtotal']) * 100 != decimal.Decimal(amount) * 100:
        return 'Validation unsuccessful. The amount requested to checkout was not the amount said on the invoice. Please contact support.'

    # Add a check whether the invoice has been paid before

    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                "name": f"Invoice #{invoice_number}",
                "quantity": 1,
                "currency": "usd",
                "amount": str(decimal.Decimal(amount) * 100)[0:-3],
            }
        ],
        mode='payment',
        expires_at=calendar.timegm(time.gmtime()) + (60 * 30),
        customer_email=customeremail,
        payment_intent_data={
            'statement_descriptor': f'{BUSINESSNAME_SHORT}* #{invoice_number}'
        },
        success_url=BILLING_STR_DOMAIN + f'/checkInvoicePaid/{invNumber}',
        cancel_url=YOUR_DOMAIN + f'/viewinvoice.php?id={invNumber}&paymentfailed=true'
    )
    r.hmset(invNumber,
            {'session_id': checkout_session.stripe_id, 'session_link': checkout_session.url, 'email': customeremail})
    r.expire(invNumber, time=60 * 32)
    return RedirectResponse(checkout_session.url, status_code=303)


@app.get('/checkInvoicePaid/{invNumber}')
def checkInvoicePaid(invNumber):
    reqRed = r.hgetall(invNumber)
    if reqRed == None or str(reqRed) == '{}' or str(reqRed) == '':
        return RedirectResponse(os.environ['WHMCS_DOMAIN'])
    session_id = str(reqRed[b'session_id'])[2:-1]
    invoice_id = invNumber

    # Checks that invoice is paid on Stripe
    getPaymentStatus = stripe.checkout.Session.retrieve(
        session_id, )
    if not (getPaymentStatus['payment_status'] == 'paid'):
        return 'Validation unsuccessful. The system cannot verify that the invoice was paid successfully. Please contact support.'

    # Marks as paid on WHMCS
    addPayment = requests.post(WHMCS_API_URL, data={'action': 'AddInvoicePayment', 'identifier': WHMCS_IDENTIFIER,
                                                    'accesskey': WHMCS_ACCESS_KEY,
                                                    'secret': WHMCS_SECRET, 'invoiceid': invoice_id,
                                                    'transid': getPaymentStatus['payment_intent'],
                                                    'gateway': 'stripe'})  # action GetClientsDetails, using UserID

    # Redirects back to WHMCS
    return RedirectResponse(YOUR_DOMAIN + f'/viewinvoice.php?id={invNumber}&paymentsuccess=true', status_code=303)


if __name__ == '__main__':
    if trueFalse(os.environ['DEBUG_MODE']):
        uvicorn.run("server:app", host=os.environ['API_HOST'], port=int(os.environ['API_PORT']), log_level="debug")
    else:
        uvicorn.run("server:app", host=os.environ['API_HOST'], port=int(os.environ['API_PORT']))
