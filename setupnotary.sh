#!/bin/bash
rm -rf botocore govern8r  govern8rClient govern8rLib govern8rService python-bitcoinlib
# one time command to update python in  MAC env.
#ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
#brew install python
#sudo eas_install virtualenv
#sudo easy_install pip

# start to download all the repos
git clone https://github.com/cypherhat/govern8r.git
git clone https://github.com/cypherhat/govern8rClient.git
git clone https://github.com/cypherhat/govern8rService.git
git clone https://github.com/cypherhat/govern8rLib.git
git clone https://github.com/cypherhat/python-bitcoinlib.git

#create virtual envs.
pwd
virtualenv -p /usr/bin/python vClient
virtualenv -p /usr/bin/python vService
source vService/bin/activate

pwd
#install server required packages
pip install -r govern8rService/requirements.txt
pwd
deactivate
pwd
source vClient/bin/activate

#install client required packages.
pip install -r govern8rClient/requirements.txt
pwd
deactivate
~                                                                                                                                                                                    
~                                                                                                                                                                                    
~                                                                                                                                                                                    
~                                                                                                                                                                                    
~                                                                                                                                                                                    
~                                                                                                                                                                                    
~                               
