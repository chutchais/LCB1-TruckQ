from flask import Flask,request ,make_response,g#, url_for
import time
import json
import datetime

from flask import request,jsonify
from flask import Response

import redis
import requests

# Added on Sep 8,2020
#To support CORS
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Booking API
URL_BOOKING = "http://192.168.10.16:5001/booking/"
URL_ETB = "http://192.168.10.20:8003/berth/etb/"
URL_BL = "http://192.168.10.16:5000/bl/"

# db = redis.StrictRedis('localhost', 6379,db=2,charset="utf-8", decode_responses=True)
db = redis.StrictRedis('tq-redis', 6379,db=2, charset="utf-8", decode_responses=True)

# --------------Start---------------
#1) Booking/Container Query
	# Check in DB (key = BOOKING)
	# IF exist :
	#   check Available Quota , count KEY (key = BOOKING:CONTAINER) must less than BOOKING:QTY:number
	# If not exist :
	#   Check Booking from Booking API (within 30 days),
	#   If found --> save to booking name and Booking Qty ,(ttl=15 days)
	#   Name    (key = BOOKING) 
	#   QTY     (key = BOOKING:QTY:number)   
	#   Vessel  (key = BOOKING:VESSEL:vessel)
	#   Voy     (key = BOOKING:VOY:voy)
	#   ETB     (key = BOOKING:VESSEL:etb)

@app.route('/booking/<booking>/<container>', methods=['GET','POST'])
@cross_origin()
def query_booking_container(booking,container):
	# 1) Pull Booking data
	result,message = verify_booking_container(booking,container)
	payload = {
		"booking":booking,
		"container":container,
		"result":"ACCEPT" if result else 'NOTACCEPT',
		"message":message
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200
	

@app.route('/booking/<booking>/<container>/reserve', methods=['GET','POST'])
@cross_origin()
def reserve_booking_container(booking,container):
	# 1) Pull Booking data
	result,message = reserve_Q_booking_container(booking,container)
	payload = {
		"booking":booking,
		"container":container,
		"result":"ok" if result else 'failed',
		"message":message
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200

@app.route('/booking/<booking>/<container>/cancel', methods=['GET','POST'])
@cross_origin()
def cancel_booking_container(booking,container):
	# 1) Pull Booking data
	result,message = cancel_Q_booking_container(booking,container)
	payload = {
		"booking":booking,
		"container":container,
		"result":"ok" if result else 'failed',
		"message":message
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200


# Internal function
def get_booking_and_save_to_db(booking):
	try:
		res = requests.get(f"{URL_BOOKING}{booking}")
		# Save to Database
		ttl = 60*60*6 #6 hours , 60*60*3
		first_container = True
		for container in res.json():
			if first_container :
				# 1) Create Booking
				key = f"{booking}"
				db.set(key,key) 
				db.expire(key, ttl)
				# 2_ QTY     (key = BOOKING:QTY:number) 
				key = f"{booking}:QTY"
				db.set(key,len(res.json())) 
				db.expire(key, ttl)
				# 3) Vessel  (key = BOOKING:VESSEL:vessel)
				key = f"{booking}:VESSEL"
				db.set(key,container['vessel_code']) 
				db.expire(key, ttl)
				# 4) Voy     (key = BOOKING:VOY:voy)
				key = f"{booking}:VOY"
				db.set(key,container['voy']) 
				db.expire(key, ttl)
				# 5) ETB     (key = BOOKING:VESSEL:etb)
				key = f"{booking}:VESSEL:ETB"
				etb = getETB(container['vessel_code'],container['voy'])
				db.set(key,etb) 
				db.expire(key, ttl)

				# 6) Save Json     (key = BOOKING:JSON)
				key = f"{booking}:JSON"
				db.set(key,json.dumps(res.json())) 
				db.expire(key, ttl)


				first_container = False

			# 6) Container (key = BOOKING:CONTAINER:container)
			key = f"{booking}:CONTAINER:{container['container']}"
			db.set(key,container['container']) #store dict in a hashjson.dumps(json_data)
			db.expire(key, ttl) #expire it after 6 hours
		print (f'Booking container count {len(res.json())}')
		return len(res.json())
	except Exception as e:
		print ('Pulling booking data Error')
		return 0

def cancel_Q_booking_container(booking,container):
	try:
		key =f"{booking}:CONTAINER:{container}:Q"
		deleteKey(key)
		return True,f"Success cancel Q of {container}"
	except Exception as e:
		return False,f"Unable to cancel Q of {container}"

def reserve_Q_booking_container(booking,container):
	try:
		(result,message) = validate_container(booking,container)
		if result == False:
			return False,f"Unable to reserved Q of {container} ,because {message}"

		key =f"{booking}:CONTAINER:{container}:Q"
		setKey(key,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		return True,f"Success reserved Q of {container}"
	except Exception as e:
		return False,f"Unable to reserved Q of {container}"	


def verify_booking_container(booking,container):
	try:
		result = False
		message=''
		# Check Booking in DB (redis)
		booking_data = getKey(booking)
		print (f'Check Booking {booking} -- {booking_data}')
		if booking_data == None :
			# If dose not exist then pull from Booking API
			# print (f'Pulling booking data')
			res = get_booking_and_save_to_db(booking)
			if res == 0 :
				message=f'Booking {booking} does''t exist in system'
				return False,message
		
		return validate_container(booking,container)
		# 
	except Exception as e:
		return 0

def validate_container(booking,container):
	message=''
	# Check reservation time must before ETB
	# key =f"{booking}:VESSEL:ETB"
	# etb_str = getKey(key)
	# if not (etb_str == None or etb_str == ''):
	# 	etb = datetime.datetime.strptime(etb_str, "%Y-%m-%d %H:%M:%S")
	# 	if datetime.datetime.now() > etb :
	# 		message=f'Not allow to reserve Q after ETB ({etb_str})'
	# 		return False,message
	# print(etb)

	# Booking exist , then check Container
	key =f"{booking}:CONTAINER:{container}"
	if getKey(key) == None :
		message=f"Container:{container} is not belong to Booking:{booking}   "
		return False,message
	
	#Check Container is already Booked?
	key =f"{booking}:CONTAINER:{container}:Q"
	q = getKey(key)
	if not q == None :
		message=f"Container:{container} is already reserved Q (on {q})"
		return False,message
	
	return True,message

def getETB(vessel,voy):
	res = requests.get(f"{URL_ETB}{vessel}/{voy}")
	print(res.text) #2020-08-19 12:00:00
	return res.text



#2) Bill of Landing Verify
	# Check in DB (key = BL)
	# IF exist :
	#   check Available Quota , count KEY (key = BOOKING:CONTAINER) must less than BOOKING:QTY:number
	# If not exist :
	#   Check Booking from Booking API (within 30 days),
	#   If found --> save to booking name and Booking Qty ,(ttl=15 days)
	#   Name    (key = BOOKING) 
	#   QTY     (key = BOOKING:QTY:number)   
	#   Vessel  (key = BOOKING:VESSEL:vessel)
	#   Voy     (key = BOOKING:VOY:voy)
	#   ETB     (key = BOOKING:VESSEL:etb)

# Import -- Full Container
@app.route('/bl/<bl>/<container>', methods=['GET','POST'])
@cross_origin()
def query_bl_container(bl,container):
	# 1) Pull Booking data
	result = True
	message ="OK"
	result,message = verify_bl_container(bl,container)
	
	payload = {
		"bl":bl,
		"container":container,
		"result":"ACCEPT" if result else 'NOTACCEPT',
		"message":message
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200

@app.route('/bl/<bl>/<container>/reserve', methods=['GET','POST'])
@cross_origin()
def reserve_bl_container(bl,container):
	# 1) Pull Booking data
	result,message = reserve_Q_bl_container(bl,container)
	payload = {
		"bl":bl,
		"container":container,
		"result":"ok" if result else 'failed',
		"message":message
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200


@app.route('/bl/<bl>/<container>/cancel', methods=['GET','POST'])
@cross_origin()
def cancel_bl_container(bl,container):
	# 1) Pull Booking data
	result,message = cancel_Q_bl_container(bl,container)
	payload = {
		"bl":bl,
		"container":container,
		"result":"ok" if result else 'failed',
		"message":message
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200

def cancel_Q_bl_container(bl,container):
	try:
		key =f"{bl}:CONTAINER:{container}:Q"
		deleteKey(key)
		return True,f"Success cancel Q of {container}"
	except Exception as e:
		return False,f"Unable to cancel Q of {container}"

def reserve_Q_bl_container(bl,container):
	try:
		(result,message) = validate_container(bl,container)
		if result == False:
			return False,f"Unable to reserved Q of {container} ,because {message}"

		key =f"{bl}:CONTAINER:{container}:Q"
		setKey(key,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		return True,f"Success reserved Q of {container}"
	except Exception as e:
		return False,f"Unable to reserved Q of {container}"	


def verify_bl_container(bl,container):
	try:
		result = False
		message=''
		# Check Booking in DB (redis)
		bl_data = getKey(bl)
		print (f'Check BL {bl} -- {bl_data}')
		if bl_data == None :
			# If dose not exist then pull from Booking API
			# print (f'Pulling booking data')
			res = get_bl_and_save_to_db(bl)
			if res == 0 :
				message=f'BL {bl} does''t exist in system'
				return False,message
		
		return validate_container(bl,container)
		# 
	except Exception as e:
		return 0

def get_bl_and_save_to_db(bl):
	try:
		res = requests.get(f"{URL_BL}{bl}")
		# Save to Database
		ttl = 60*60*6 #6 hours , 60*60*3
		first_container = True
		for container in res.json():
			if first_container :
				# 1) Create Booking
				key = f"{bl}"
				db.set(key,key) 
				db.expire(key, ttl)
				# 2_ QTY     (key = BOOKING:QTY:number) 
				key = f"{bl}:QTY"
				db.set(key,len(res.json())) 
				db.expire(key, ttl)
				# 3) Vessel  (key = BOOKING:VESSEL:vessel)
				# key = f"{bl}:VESSEL"
				# db.set(key,container['vessel_code']) 
				# db.expire(key, ttl)
				# 4) Voy     (key = BOOKING:VOY:voy)
				# key = f"{bl}:VOY"
				# db.set(key,container['voy']) 
				# db.expire(key, ttl)
				# 5) ETB     (key = BOOKING:VESSEL:etb)
				# key = f"{bl}:VESSEL:ETB"
				# etb = getETB(container['vessel_code'],container['voy'])
				# db.set(key,etb) 
				# db.expire(key, ttl)

				# 6) Save Json     (key = BOOKING:JSON)
				key = f"{bl}:JSON"
				db.set(key,json.dumps(res.json())) 
				db.expire(key, ttl)


				first_container = False

			# 6) Container (key = BOOKING:CONTAINER:container)
			key = f"{bl}:CONTAINER:{container['container']}"
			db.set(key,container['container']) #store dict in a hashjson.dumps(json_data)
			db.expire(key, ttl) #expire it after 6 hours
		print (f'BL container count {len(res.json())}')
		return len(res.json())
	except Exception as e:
		print ('Pulling bl data Error')
		return 0
# --------------End-----------------
# Import -- MTY Container
@app.route('/shore/<shore>', methods=['GET','POST'])
@cross_origin()
def query_shore(shore):
	# 1) Pull Booking data
	result = True
	message ="OK"
	# result,message = verify_bl_container(bl,container)
	payload = {
		"shore":shore,
		"result":"ACCEPT" if result else 'NOTACCEPT',
		"message":message
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200




def setKey(key,value):
	return db.set(key,value)

def getKey(key):
	return db.get(key)

def deleteKey(key):
	return db.delete(key)

if __name__ == '__main__':
	app.run(host='0.0.0.0',debug=True)
	# serve(app, host='0.0.0.0', port=8013)
