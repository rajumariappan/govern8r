from flask import request, Response, json, g, redirect, url_for
from functools import wraps

from flask_api import FlaskAPI
from wallet import NotaryWallet
from services.account_service import AccountService
from services.notarization_service import NotarizationService
from message import SecureMessage
import base58
import hashlib
import configuration

config = configuration.NotaryConfiguration()
app = FlaskAPI(__name__)
wallet = NotaryWallet("foobar")
account_service = AccountService(wallet)
notarization_service = NotarizationService(wallet)
secure_message = SecureMessage(wallet)

bad_response = Response(json.dumps({}), status=500, mimetype='application/json')
bad_response.set_cookie('govern8r_token', 'UNAUTHENTICATED')

unauthenticated_response = Response(json.dumps({}), status=401, mimetype='application/json')
unauthenticated_response.set_cookie('govern8r_token', 'UNAUTHENTICATED')


def build_fingerprint():
    fingerprint = str(request.user_agent)+str(request.remote_addr)
    return fingerprint


def build_token(nonce):
    nonce_hash = hashlib.sha256(nonce).digest()
    fingerprint_hash = hashlib.sha256(build_fingerprint()).digest()
    token = hashlib.sha256(nonce_hash + fingerprint_hash).digest()
    encoded = base58.base58_check_encode(0x80, token.encode("hex"))
    return encoded


def validate_token(nonce, token):
    check_token = build_token(nonce)
    return check_token == token


def authenticated():
    govern8r_token = request.cookies.get('govern8r_token')
    return validate_token(g.account_data['nonce'], govern8r_token)


def rotate_authentication_token():
    govern8r_token = build_token(g.account_data['nonce'])
    authenticated_response = Response(json.dumps({}), status=200, mimetype='application/json')
    authenticated_response.set_cookie('govern8r_token', govern8r_token)
    return authenticated_response


def previously_notarized(document_hash):
    notarization_data = notarization_service.get_notarization_by_document_hash(document_hash)
    if notarization_data is not None:
        return True
    else:
        return False


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        address = kwargs['address']
        if address is None:
            return bad_response
        if not authenticated():
            return unauthenticated_response
        return f(*args, **kwargs)
    return decorated_function


def address_based(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        address = kwargs['address']
        if address is None:
            return bad_response
        else:
            account_data = account_service.get_account_by_address(address)
            if account_data is None:
                return bad_response
            g.account_data = account_data
        return f(*args, **kwargs)
    return decorated_function


def security_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        address = kwargs['address']
        payload = request.data
        if secure_message.verify_secure_payload(address, payload):
            raw_message = secure_message.get_message_from_secure_payload(payload)
            g.message = json.loads(raw_message)
        else:
            return bad_response
        return f(*args, **kwargs)
    return decorated_function


@app.route("/govern8r/api/v1/pubkey", methods=['GET'])
def pubkey():
    """
    Return server public key. The key is encoded in hex and needs to be decoded
    from hex to be used by the encryption utility.
    """
    # request.method == 'GET'
    public_key = wallet.get_public_key()
    data = {
        'public_key': public_key.encode("hex")
    }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')
    return resp


@app.route("/govern8r/api/v1/challenge/<address>", methods=['PUT'])
@address_based
@security_required
def put_challenge(address):
    """
    Authentication
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    """

    if g.message['nonce'] != g.account_data['nonce']:
        return unauthenticated_response
    govern8r_token = build_token(g.account_data['nonce'])
    good_response = Response(json.dumps({}), status=200, mimetype='application/json')
    good_response.set_cookie('govern8r_token', value=govern8r_token)
    return good_response


@app.route("/govern8r/api/v1/challenge/<address>", methods=['GET'])
@address_based
def get_challenge(address):
    """
    Authentication
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    """

    str_nonce = json.dumps({'nonce': g.account_data['nonce']})
    payload = secure_message.create_secure_payload(g.account_data['public_key'], str_nonce)
    good_response = Response(json.dumps(payload), status=200, mimetype='application/json')
    return good_response


@app.route("/govern8r/api/v1/account/<address>", methods=['GET'])
@address_based
@login_required
def get_account(address):
    """
    Account registration
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    """

    outbound_payload = secure_message.create_secure_payload(g.account_data['public_key'], json.dumps(g.account_data))
    authenticated_response = rotate_authentication_token()
    authenticated_response.data = outbound_payload
    return authenticated_response


@app.route("/govern8r/api/v1/account/<address>", methods=['PUT'])
@security_required
def put_account(address):
    """
    Account registration
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    """

    good_response = Response(json.dumps({}), status=200, mimetype='application/json')

    result = account_service.create_account(address, g.message)
    if result is None:
        return bad_response
    else:
        print(result)
        return good_response


@app.route("/govern8r/api/v1/account/<address>/<nonce>", methods=['GET'])
@address_based
def confirm_account(address, nonce):
    """
    Account registration confirmation
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    nonce : string
       The nonce sent to the email address
    """
    good_response = Response("Confirmed: "+address, status=200, mimetype='application/json')
    account_service.confirm_account(address, nonce)
    return good_response


@app.route("/govern8r/api/v1/account/<address>/notarization/<document_hash>", methods=['PUT'])
@address_based
@security_required
@login_required
def notarization(address, document_hash):
    """
    Notarize document
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    document_hash : string
       The hash of the document.
    """

    authenticated_response = rotate_authentication_token()

    if previously_notarized(document_hash):
        authenticated_response.status_code = 500
        return authenticated_response

    if g.message['document_hash'] == document_hash:
        g.message['address'] = address
        outbound_message = notarization_service.notarize(g.message)
        if outbound_message is not None:
            outbound_payload = secure_message.create_secure_payload(g.account_data['public_key'], json.dumps(outbound_message))
            authenticated_response.data = json.dumps(outbound_payload)
        else:
            authenticated_response.status_code = 500
        return authenticated_response
    else:
        return unauthenticated_response


@app.route("/govern8r/api/v1/account/<address>/notarization/<document_hash>/status", methods=['GET'])
@address_based
@login_required
def notarization_status(address, document_hash):
    """
    Notarization status
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    document_hash : string
       The hash of the document.
    """
    authenticated_response = rotate_authentication_token()
    status_data = notarization_service.get_notarization_status(document_hash)
    if status_data is not None:
        outbound_payload = secure_message.create_secure_payload(g.account_data['public_key'], json.dumps(status_data))
        authenticated_response.data = json.dumps(outbound_payload)
    else:
        authenticated_response.data = status_data
    return authenticated_response


@app.route("/govern8r/api/v1/account/<address>/test", methods=['GET'])
@address_based
@login_required
def test_authentication(address):
    """
    Test authentication
    Parameters
    ----------
    address : string
       The Bitcoin address of the client.
    """

    authenticated_response = rotate_authentication_token()
    return authenticated_response


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)