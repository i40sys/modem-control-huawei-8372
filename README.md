Detailed information at:
https://industry40.system/iot-gw/32
in spanish

# DESCRIPTION
Connect, or disconnect, Internet connection through a Huawei 8372h-320 4G modem. Commands can be processed using CLI or sending SMS to the SIM card installed in the 4G modem.


quick summary of the operations:

# HOW DOES IT WORK

* only last SMS is maintained, the rest of SMS are deleted
* SMS content is stored in /var/run/modem, content always lowcase
* there are two scripts on /opt/modem: modem_on/modem_off
* both of them are linked on /usr/local/bin for making them available on PATH
* the only thing they do is change the content of /var/run/modem for on/off
* content of file /var/run/modem is overiden by last SMS content
* for disconnecting just run the command 'modem_off' or send SMS message with the content "off"
* in less than two minutes modem will be disconnected
* modem.py also works as a watchdog checking internet connection every 60"
* Ping IP address in Internet for checking connectivity

