!/bin/bash
rm -rf botocore  govern8r  govern8rClient  govern8rLib govern8rService  python-bitcoinlib
# one time command to update python in  MAC env.
#ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
#brew install python
#sudo eas_install virtualenv
#sudo easy_install pip

# start to download all the repos
git clone https://github.com/boto/botocore.git
git clone https://github.com/cypherhat/govern8r.git
git clone https://github.com/cypherhat/govern8rClient.git
git clone https://github.com/cypherhat/govern8rService.git
git clone https://github.com/cypherhat/govern8rLib.git
git clone https://github.com/cypherhat/python-bitcoinlib.git

pwd
virtualenv -p /usr/bin/python vClient
virtualenv -p /usr/bin/python vService
pwd
source vService/bin/activate
pip install flask
pip install flask-api
pip install pybitid
pip install blockcypher
pip install certifi
pip install configparser
pip install ecdsa
pip install pycrypto
pip install simple-crypt
pip install pyOpenSSL
pwd
cd botocore
python setup.py install
cd ..

pip install boto3
pip install awscli

pwd
cd python-bitcoinlib
python setup.py install
cd ..
pwd
cd govern8rLib
python setup.py install
cd ..

deactivate

pwd
source vClient/bin/activate
pip install requests
pip install ecdsa
pip install pycrypto
pip install configparser
pip install simple-crypt

cd govern8rLib
python setup.py install
cd ..
pwd
cd python-bitcoinlib
sudo python setup.py install
cd ..
pwd
deactivate

