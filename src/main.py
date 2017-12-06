#!/usr/bin/env python
import homie
import logging
import string
import threading
import json
import hashlib
import uuid
import time
import urllib.request, urllib.error, urllib.parse

logging.basicConfig(level=logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

configFile = "config/config.json"
Homie = homie.Homie(configFile)
node = Homie.Node("narodmon", "sensors")
sensor_type_desc = {11: 'lux'}

def init():
	global configFile, api_key, users, sensor_types, timeout

	config = Homie._loadConfig(configFile)
	users = config.get('USERS', '')
	logger.info("users: ")
	logger.info(users)

	sensor_types = config.get('SENSOR_TYPES', '')
	logger.info("sensor_types: ")
	logger.info(sensor_types)

	api_key = config.get('API_KEY', '')
	if api_key == '':
		logger.error("Error reading api_key from config.")
		exit(-1)
	logger.info("Using api_key: " + api_key)

	timeout = config.get('SEND_TIMEOUT', 60)
	logger.info("Using timeout: " + str(timeout))

def send_sensors_state():
	global api_key, users, sensor_types, sensor_type_desc, timeout
	while True:
		try:
			for user in users:
				id = user #Номер желаемого пользователя, у которого нужно получить данные сенсоров
				app_id = str(uuid.getnode())
				md5_app_id = hashlib.md5(app_id.encode('utf-8')).hexdigest()
				data = {
					'cmd': 'sensorsOnDevice',
					'id': id,
					'uuid': md5_app_id,
					'api_key': api_key,
					'lang': 'en'
				}
				request = urllib.request.Request('http://narodmon.ru/api', json.dumps(data).encode('utf-8'))
				response = urllib.request.urlopen(request)
				buf = response.read()
				result = json.loads(buf.decode('utf-8'))
				for sensor in result.get("sensors", None):
					id = sensor.get('id', '')
					name = sensor.get('name', '')
					stype = sensor.get('type', 11)
					value = sensor.get('value', -1)
					unit = sensor.get('unit', '')

					if stype not in sensor_types:
						continue
					# logger.info(unit + ": " + str(value))

					node = Homie.Node(str(user), "sensors")
					Homie.setNodeProperty(node, sensor_type_desc[stype], value, False)
					logger.info("Sending user (" + str(user) + ") sensor (" + str(id) + ") value: " + str(value))
		except Exception as e:
			logger.error("Error updating sensors: " + str(e))
		time.sleep(timeout)

def main():
	init()
	Homie.setFirmware("narodmon", "1.0.0")
	Homie.setup()
	
	t1 = threading.Thread(target=send_sensors_state, args=[])
	t1.daemon = True
	t1.start()

	while True:
		time.sleep(1)

if __name__ == '__main__':
	try:
		main()
	except (KeyboardInterrupt, SystemExit):
		logger.info("Quitting.")
