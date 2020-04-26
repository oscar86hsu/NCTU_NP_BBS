#!/bin/bash

myip=`curl -s "https://api.ipify.org"`
echo "My IP:" $myip

if [ "$myip" != "35.185.139.53" ]; then

    mydomain="oscarhsu.me"
    myhostname="bbs"
    gdapikey=$(aws ssm get-parameter --name "godaddy-api-key" --with-decryption | python -c "import sys, json; print(json.load(sys.stdin)['Parameter']['Value'])")

    dnsdata=`curl -s -X GET -H "Authorization: sso-key ${gdapikey}" "https://api.godaddy.com/v1/domains/${mydomain}/records/A/${myhostname}"`
    gdip=`echo $dnsdata | cut -d ',' -f 1 | tr -d '"' | cut -d ":" -f 2`
    echo "`date '+%Y-%m-%d %H:%M:%S'` - Current External IP is $myip, GoDaddy DNS IP is $gdip"


    if [ "$gdip" != "$myip" -a "$myip" != "" ]; then
        echo "IP has changed!! Updating on GoDaddy"
        curl -s -X PUT "https://api.godaddy.com/v1/domains/${mydomain}/records/A/${myhostname}" -H "Authorization: sso-key ${gdapikey}" -H "Content-Type: application/json" -d "[{\"data\": \"${myip}\"}]"
        echo "Changed IP on ${myhostname}.${mydomain} from ${gdip} to ${myip}"
    fi
fi

python server.py