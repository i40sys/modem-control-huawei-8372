#!/usr/bin/env python3
from ping3 import ping
import copy
from time import sleep

import os
import sys
import logging
import daiquiri

import huaweisms.api.device
import huaweisms.api.user
import huaweisms.api.wlan
import huaweisms.api.dialup
import huaweisms.api.sms

DEBUG_LEVEL = logging.DEBUG
DESIRED_DEFAULT = "on"
PING_IP = "8.8.8.8, 8.8.4.4, 1.1.1.1, 1.0.0.1"
MODEM_FILE = "/var/run/modem"
MODEM_IP = "192.168.8.1"
LOG_FILE = "/var/log/modem.log"
# change for your credentials:
MODEM_USER = "admin"
MODEM_PASSWORD = "DQBETBG90JR"

daiquiri.setup(
    level=DEBUG_LEVEL, 
    outputs=(
      daiquiri.output.Stream(sys.stdout),
      daiquiri.output.RotatingFile(LOG_FILE, max_size_bytes=100000000),
    ))
logger = daiquiri.getLogger(__name__)

def is_online():
    ips = [ip.strip() for ip in PING_IP.split(',')]
    for ip in ips:
      logger.debug(f'Pinging IP: {ip}')
      try:
        out = ping(ip, timeout = 10)
        logger.info('Internet, status: ONLINE')
        return True
      except OSError:
        pass

    logger.info('Internet, status: OFFLINE')
    return False

def reboot(ctx):
  boot = huaweisms.api.device.reboot(ctx)
  logger.debug(boot)

  return boot['response'] == 'OK'

def is_connected(ctx):
  dialup = huaweisms.api.dialup.get_mobile_status(ctx)
  logger.debug(dialup)

  return dialup == "CONNECTED"

def dialup_disconnect(ctx):
  dialup = huaweisms.api.dialup.disconnect_mobile(ctx)
  logger.debug(dialup)

  return dialup['response'] == 'OK'

def dialup_connect(ctx):
  dialup = huaweisms.api.dialup.connect_mobile(ctx)
  logger.debug(dialup)

  return dialup['response'] == 'OK'

def _get_n_clean_sms(ctx):
  last = {}
  current = {}

  all_sms = huaweisms.api.sms.get_sms(
    ctx,
    box_type = 1,
    page = 1,
    qty = 10,
    unread_preferred = True
  )
  logger.debug(all_sms)
  if all_sms['type'] != 'response':
    logger.error(f'Cannot get SMS. Error: {all_sms}')
    sys.exit(-1)
  
  if not ('Message' in all_sms['response']['Messages']):
    logger.info('SMS Inbox empty')
    return get_desired_state()

  for sms in all_sms['response']['Messages']['Message']:
    current['index'] = sms['Index']
    current['ts'] = sms['Date']
    current['phone'] = sms['Phone']
    current['content'] = sms['Content'].lower().rstrip()
    logger.debug(f"SMS, processing: {current['ts']} - phone: {current['phone']} - content: {current['content']}")
    if 'ts' in last:
      logger.debug(f"last: {last['ts']} > current: {current['ts']}")
      if last['ts'] > current['ts']:
        logger.debug(f"SMS, removing: {current['ts']} - phone: {current['phone']} - content: {current['content']}")
        huaweisms.api.sms.delete_sms(ctx, current['index'])
    else:
      last = copy.deepcopy(current)

  logger.info(f"SMS, removing latest message: {last['ts']} - phone: {last['phone']} - content: {last['content']}")
  huaweisms.api.sms.delete_sms(ctx, last['index'])
    
  return last['content']

def get_last_sms(ctx):
    logger.debug('getting last SMS received...')
    logger.debug('removing old SMS, keep the lastest one')
    last_sms_data = _get_n_clean_sms(ctx)
    # possible values: on/off -> online/offline
    if last_sms_data.lower() == "on":
        # echo on > /var/run/modem
        modem_desired_state = 'on'
    else:
        # echo off > /var/run/modem
        modem_desired_state = 'off'
    open(MODEM_FILE,'w').write(modem_desired_state)
    logger.debug(f"stored desired state {modem_desired_state} at {MODEM_FILE}")

def get_desired_state():
    try:
        out = open(MODEM_FILE,'r').read()
    except FileNotFoundError:
        out = DESIRED_DEFAULT
    return out.lower().strip()

if __name__ == "__main__":
  # crontab calls periodically this business logic
  ctx = huaweisms.api.user.quick_login(MODEM_USER, MODEM_PASSWORD)

  get_last_sms(ctx)
  if get_desired_state() == "on":
    logger.info('Desired Internet connection: ONLINE')
    if not is_connected(ctx):
      dialup_connect(ctx)
      logger.info('Connecting... (waiting for 10s)')
      sleep(10)
    else:
      if not is_online():
        logger.warn("Everything ready, but Internet offline. Try resetting the modem with script: reset.sh")
        reboot(ctx)
        logger.info('Rebooting... (waiting for 30s)')
        sleep(30)
  else:
    logger.debug('Desired Internet connection: OFFLINE')
    if is_connected(ctx):
      dialup_disconnect(ctx)
      logger.info('Disconnecting... (waiting for 10s)')
      sleep(10)

  logger.debug('logout')
  huaweisms.api.user.logout(ctx)
  

