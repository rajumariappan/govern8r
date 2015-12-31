from flask import request, Response, json
from flask_api import FlaskAPI
from wallet import NotaryWallet
from message import SecureMessage
from services.account_db_service import AccountDbService
from message import SecureMessage

app = FlaskAPI(__name__)
wallet = NotaryWallet()
account_service = AccountDbService()


def build_fingerprint():
    fingerprint = request.user_agent+request.remote_addr
    return fingerprint


def build_token(nonce):
    token = ''
    # token = hash(hash(build_fingerprint()) + hash(nonce))
    return token


@app.route("/govern8r/api/v1/pubkey", methods=['GET'])
def pubkey():
    """
    Return server public key. The key is encoded in hex and needs to be decoded from hex to be used by the encryption utility.
    """
    # request.method == 'GET'
    public_key = wallet.get_public_key()
    data = {
        'public_key': public_key.encode("hex")
    }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')
    return resp


@app.route("/govern8r/api/v1/challenge/<address>", methods=['GET', 'PUT'])
def challenge(address):
    """
    Authentication
    """
    js = json.dumps({})
    bad_response = Response(js, status=500, mimetype='application/json')

    secure_message = SecureMessage()
    if request.method == 'GET':
        account = account_service.get_challenge(address)
        if account is None:
            return bad_response
        str_nonce = json.dumps({'nonce': account['nonce']})
        payload = secure_message.create_secure_payload(account['public_key'], str_nonce)
        return payload
    elif request.method == 'PUT':
        account = account_service.get_account_by_address(address)
        if account is None:
            return bad_response
        payload = request.data
        if secure_message.verify_secure_payload(address, payload):
            raw_message = secure_message.get_message_from_secure_payload(payload)
            message = json.loads(raw_message)
            print("Incoming nonce: %s" % message['nonce'])
            print("Nonce on record: %s" % account['nonce'])
            return bad_response
    return bad_response

@app.route("/govern8r/api/v1/account/<address>", methods=['GET', 'PUT'])
def account(address):
    """
    Account registration
    """

    good_response = Response(json.dumps({}), status=200, mimetype='application/json')
    bad_response = Response(json.dumps({}), status=500, mimetype='application/json')
    secure_message = SecureMessage()
    payload = request.data
    if secure_message.verify_secure_payload(address, payload):
        str_registration_data = secure_message.get_message_from_secure_payload(payload)
        registration_data = json.loads(str_registration_data)

        if request.method == 'PUT':
            if not account_service.create_account(address, registration_data):
                return bad_response
            else:
                return good_response
        else:
            return bad_response

    return good_response


@app.route("/govern8r/api/v1/account/<address>/<nonce>", methods=['GET'])
def confirm_account(address, nonce):
    """
    Account registration confirmation
    """
    if request.method == 'GET':
        account_service.confirm_account(address, nonce)
    return {}


@app.route("/govern8r/api/v1/account/<address>/notarization/<document_hash>", methods=['PUT'])
def notarization(address, document_hash):
    """
    Notarize document
    """

    # request.method == 'PUT'
    return {}


@app.route("/govern8r/api/v1/account/<address>/notarization/<document_hash>/status", methods=['GET'])
def notarization_status(address, document_hash):
    """
    Notarization status
    """

    # request.method == 'GET'
    return {}


if __name__ == "__main__":
    app.run(debug=True)