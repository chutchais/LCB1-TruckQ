from flask import Flask,request ,make_response,g#, url_for
import time
import json
import datetime
import sys, os

from flask import request,jsonify
from flask import Response

import redis
import requests

# Added on Sep 8,2020
#To support CORS
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
# cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False

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

@app.route('/api/booking/<booking>/<container>', methods=['GET','POST'])
# @cross_origin()
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
	

@app.route('/api/booking/<booking>/<container>/reserve', methods=['GET','POST'])
# @cross_origin()
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

@app.route('/api/booking/<booking>/<container>/cancel', methods=['GET','POST'])
# @cross_origin()
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

				#7)Added Reserved on Oct 2,2020

				# Modify on Oct 7,2020 -- To update RESERVED in case exist. 
				key = f"{booking}:RESERVED"
				if db.get(key) == None :
					db.set(key,0) 
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
		return True,f"ยกเลิกการจองคิวของ {container}"
	except Exception as e:
		return False,f"ไม่สามารถยกเลิกการจองคิวของ {container}"

def reserve_Q_booking_container(booking,container):
	try:
		(result,message) = validate_container(booking,container)
		if result == False:
			return False,f"ไม่สามารถจองคิวของตู้ {container} ,เพราะ {message}"

		key =f"{booking}:CONTAINER:{container}:Q"
		setKey(key,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		return True,f"จองคิวของตู้ {container} สำเร็จ"
	except Exception as e:
		return False,f"ไม่สามารถจองคิวของตู้ {container}"	


def verify_booking_container(booking,container):
	try:
		result = False
		message=''
		# Check Booking in DB (redis)
		key = booking
		# Added to improve in case there is new container added --on Oct 7,2020
		key =f'{booking}:CONTAINER:{container}'
		booking_data = getKey(key)

		print (f'Check Booking {booking} -- {booking_data}')
		if booking_data == None :
			# If dose not exist then pull from Booking API
			# print (f'Pulling booking data')
			res = get_booking_and_save_to_db(booking)
			if res == 0 :
				message=f'Booking {booking} ไม่มีอยู่ในระบบ'
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
		message=f"ตู้:{container} ไม่อยู่ภายใต้ booking:{booking}   "
		return False,message
	
	#Check Container is already Booked?
	key =f"{booking}:CONTAINER:{container}:Q"
	q = getKey(key)
	if not q == None :
		message=f"ตู้:{container} ได้ถูกจองเรียบร้อยแล้ว (เมื่อวันที่ {q})"
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

# 1)BL without Container -- Check Avialable
@app.route('/api/bl/<bl>/check/<reserve_qty>', methods=['GET','POST'])
def query_bl_qty(bl,reserve_qty=0):
	# 1) Pull Booking data
	result = True
	message ="OK"
	result,message,qty,available = verify_bl(bl,reserve_qty)
	payload = {
		"bl":bl,
		"result":"ACCEPT" if result else 'NOTACCEPT',
		"message":message,
		"qty" : qty,
		"available":available
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200

# 2)BL without Container -- Reserve container
@app.route('/api/bl/<bl>/reserve/<reserve_qty>', methods=['GET','POST'])
def reserve_bl_qty(bl,reserve_qty=0):
	# 1) Pull Booking data
	result = False
	message =""
	qty =0
	available=0
	# --Verify Existing BL --
	bl_data = getKey(bl)
	if bl_data == None :
		message = f"ไม่พบ {bl} ในระบบ"
	else:
		# Verify Qty.Reserved and Reserved_Qty
		qty = getKey(f'{bl}:QTY')
		reserved = getKey(f'{bl}:RESERVED')
		if int(reserved)+int(reserve_qty) > int(qty) :
			result = False
			message = f"Unable to reserve for {reserve_qty} container(s) , Reserved number exceed BL total container number"
			message = f"ไม่สามารถจองจำนวน {reserve_qty} ตู้ได้ ,เพราะเกินจำนวน หรือ BL นี้ถูกจองเต็มหมดแล้ว"
			available = int(qty)-int(reserved)
		else :
			# Increase BL:RESERVED by reserved_qty
			key = f"{bl}:RESERVED"
			setKey(key,int(reserved)+int(reserve_qty))
			#-----------------------------------
			result=True
			message = f"Reserved {reserve_qty} container(s) successful"
			message = f"การจองจำนวน {reserve_qty} ตู้สำเร็จ"
			available = int(qty)- (int(reserved)+int(reserve_qty))
	#------------------------
	payload = {
		"bl":bl,
		"result":"ok" if result else 'failed',
		"message":message,
		"qty" : qty,
		"available":available
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response

# 2)BL without Container -- Cancel container
@app.route('/api/bl/<bl>/cancel/<cancel_qty>', methods=['GET','POST'])
def cancel_bl_qty(bl,cancel_qty=0):
	# 1) Pull Booking data
	result = False
	message =""
	qty =0
	available=0
	# --Verify Existing BL --
	bl_data = getKey(bl)
	if bl_data == None :
		message = f"ไม่พบ {bl} ในระบบ"
	else:
		# Verify Qty.Reserved and Reserved_Qty
		qty = getKey(f'{bl}:QTY')
		reserved = getKey(f'{bl}:RESERVED')

		new_qty = int(reserved)-int(cancel_qty)
		new_qty = 0 if new_qty < 0 else new_qty

		# Decrease BL:RESERVED by cancel_qty
		key = f"{bl}:RESERVED"
		setKey(key,new_qty)
		# --------------------------------

		result=True
		message = f"การยกเลิกจำนวน {cancel_qty} ตู้สำเร็จ"
		available = int(qty)- int(new_qty)
	#------------------------
	payload = {
		"bl":bl,
		"result":"ok" if result else 'failed',
		"message":message,
		"qty" : qty,
		"available":available
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
# -------------------------------------------

@app.route('/api/bl/<bl>/<container>', methods=['GET','POST'])
# @cross_origin()
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

@app.route('/api/bl/<bl>/<container>/reserve', methods=['GET','POST'])
# @cross_origin()
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


@app.route('/api/bl/<bl>/<container>/cancel', methods=['GET','POST'])
# @cross_origin()
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
		return True,f"ยกเลิกคิวของ {container} สำเร็จ"
	except Exception as e:
		return False,f"ไม่สามารถยกเลิกคิวของ {container}"

def reserve_Q_bl_container(bl,container):
	try:
		(result,message) = validate_container(bl,container)
		if result == False:
			return False,f"ไม่สามารถจองคิวสำหรับตู้ {container} ,เพราะ {message}"

		key =f"{bl}:CONTAINER:{container}:Q"
		setKey(key,datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		return True,f"จองคิวสำหรับตู้ {container} สำเร็จ"
	except Exception as e:
		return False,f"จองคิวสำหรับตู้ {container} ไม่สำเร็จ"	

def verify_bl(bl,reserve_qty=1):
	try:
		result = False
		message=''
		qty=0
		available=0
		# Check Booking in DB (redis)
		bl_data = getKey(bl)
		print(bl_data)
		print (f'Check BL {bl} -- {bl_data}')
		if bl_data == None :
			# If dose not exist then pull from Booking API
			print (f'Pulling booking data')
			qty = get_bl_and_save_to_db(bl)
			if qty == 0 : #BL QTY
				message=f'BL {bl} does''t exist in system'
				message=f'ไม่พบ {bl} ในระบบ'
			else :
				# Check Request number with 
				available = getKey(f'{bl}:RESERVED')
				result = True
			return result,message,qty,available
		else:
			# BL is exist
			qty = getKey(f'{bl}:QTY')
			reserved = getKey(f'{bl}:RESERVED')
			if int(reserved)+int(reserve_qty) > int(qty) :
				result = False
				message = f"Unable to reserve for {reserve_qty} container(s) , Reserved number exceed BL total container number"
				message = f"ไม่สามารถจองจำนวน {reserve_qty} ตู้ได้ ,เพราะเกินจำนวน หรือ BL นี้ถูกจองเต็มหมดแล้ว"
				available = int(qty)-int(reserved)
			else :
				result = True
				message = ""
				available = int(qty)-int(reserved) #int(qty)-(int(reserved)+int(reserve_qty))
			
			
			return result,message,qty,available


	except Exception as e:
		return False,f"ไม่สามารถดึงข้อมูล BL {bl} ได้ เพราะว่า {e}",qty,0

def verify_bl_container(bl,container):
	try:
		result = False
		message=''
		# Check Booking in DB (redis)
		bl_data = getKey(bl)
		print (f'Check BL {bl} -- {bl_data}')
		if bl_data == None :
			# If dose not exist then pull from Booking API
			print (f'Pulling booking data')
			res = get_bl_and_save_to_db(bl)
			if res == 0 : #BL QTY
				message=f'BL {bl} does''t exist in system'
				message=f'ไม่พบ BL {bl} ในระบบ'
				if container == '':
					return (False,message,0)
				else:
					return (False,message)
		
		print('Found BL')
		if container == '':
			return (True,'',6)
		else:
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

				# Added on Sep 18,2020 -- To intial RESERVE number
				key = f"{bl}:RESERVED"
				db.set(key,0) 
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
		print (f'Pulling bl data Error : {e}')
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		return 0
# --------------End-----------------

def verify_shore(bl,reserve_qty=1):
	try:
		result = False
		message=''
		qty=0
		available=0
		# Check Booking in DB (redis)
		bl_data = getKey(bl)
		print(bl_data)
		print (f'Check BL {bl} -- {bl_data}')
		if bl_data == None :
			# If dose not exist then pull from Booking API
			print (f'Pulling Booking data')
			qty = get_booking_and_save_to_db(bl)
			if qty == 0 : #BL QTY
				message=f'BL {bl} does''t exist in system'
				message=f'ไม่พบ {bl} ในระบบ'
			else :
				# Check Request number with 
				available = getKey(f'{bl}:RESERVED')
				result = True
			return result,message,qty,available
		else:
			# BL is exist
			qty = getKey(f'{bl}:QTY')
			reserved = getKey(f'{bl}:RESERVED')

			if int(reserved)+int(reserve_qty) > int(qty) :
				result = False
				message = f"Unable to reserve for {reserve_qty} container(s) , Reserved number exceed BL total container number"
				message = f"ไม่สามารถจองจำนวน {reserve_qty} ตู้ได้ ,เพราะเกินจำนวน หรือ ชอร์นี้ถูกจองเต็มหมดแล้ว"
				available = int(qty)-int(reserved)
			else :
				result = True
				message = ""
				available = int(qty)-int(reserved) #int(qty)-(int(reserved)+int(reserve_qty))
			
			
			return result,message,qty,available


	except Exception as e:
		return False,f"ไม่สามารถดึงข้อมูล Shore {bl} ได้ เพราะว่า {e}",qty,0

# Import -- MTY Container
@app.route('/api/shore/<shore>', methods=['GET','POST'])
# @cross_origin()
def query_shore(shore):
	# 1) Pull Booking data
	result = True
	message ="OK"
	result,message,qty,available = verify_shore(shore,1)
	# result,message = verify_booking_container(booking,container)
	# result,message = verify_bl_container(bl,container)
	payload = {
		"shore":shore,
		"result":"ACCEPT" if result else 'NOTACCEPT',
		"message":message,
		"qty":qty,
		"available":available
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200

# 1)shore without Container -- Check Avialable
@app.route('/api/shore/<shore>/check/<reserve_qty>', methods=['GET','POST'])
def query_shore_qty(shore,reserve_qty=0):
	# 1) Pull Booking data
	result = True
	message ="OK"
	result,message,qty,available = verify_shore(shore,reserve_qty)
	payload = {
		"shore":shore,
		"result":"ACCEPT" if result else 'NOTACCEPT',
		"message":message,
		"qty" : qty,
		"available":available
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
	# return json.dumps(payload, indent=4) ,200

# 2)shore without Container -- Reserve container
@app.route('/api/shore/<shore>/reserve/<reserve_qty>', methods=['GET','POST'])
def reserve_shore_qty(shore,reserve_qty=0):
	# 1) Pull Booking data
	result = False
	message =""
	qty =0
	available=0
	# --Verify Existing BL --
	bl_data = getKey(shore)
	if bl_data == None :
		message = f"ไม่พบ {shore} ในระบบ"
	else:
		# Verify Qty.Reserved and Reserved_Qty
		qty = getKey(f'{shore}:QTY')
		reserved = getKey(f'{shore}:RESERVED')
		if int(reserved)+int(reserve_qty) > int(qty) :
			result = False
			message = f"Unable to reserve for {reserve_qty} container(s) , Reserved number exceed BL total container number"
			message = f"ไม่สามารถจองจำนวน {reserve_qty} ตู้ได้ ,เพราะเกินจำนวน หรือ ชอร์นี้ถูกจองเต็มหมดแล้ว"
			available = int(qty)-int(reserved)
		else :
			# Increase BL:RESERVED by reserved_qty
			key = f"{shore}:RESERVED"
			setKey(key,int(reserved)+int(reserve_qty))
			#-----------------------------------
			result=True
			message = f"Reserved {reserve_qty} container(s) successful"
			message = f"การจองจำนวน {reserve_qty} ตู้สำเร็จ"
			available = int(qty)- (int(reserved)+int(reserve_qty))
	#------------------------
	payload = {
		"shore":shore,
		"result":"ok" if result else 'failed',
		"message":message,
		"qty" : qty,
		"available":available
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response

# 2)BL without Container -- Cancel container
@app.route('/api/shore/<shore>/cancel/<cancel_qty>', methods=['GET','POST'])
def cancel_shore_qty(shore,cancel_qty=0):
	# 1) Pull Booking data
	result = False
	message =""
	qty =0
	available=0
	# --Verify Existing BL --
	bl_data = getKey(shore)
	if bl_data == None :
		message = f"ไม่พบ {shore} ในระบบ"
	else:
		# Verify Qty.Reserved and Reserved_Qty
		qty = getKey(f'{shore}:QTY')
		reserved = getKey(f'{shore}:RESERVED')

		new_qty = int(reserved)-int(cancel_qty)
		new_qty = 0 if new_qty < 0 else new_qty

		# Decrease BL:RESERVED by cancel_qty
		key = f"{shore}:RESERVED"
		setKey(key,new_qty)
		# --------------------------------

		result=True
		message = f"การยกเลิกจำนวน {cancel_qty} ตู้สำเร็จ"
		available = int(qty)- int(new_qty)
	#------------------------
	payload = {
		"shore":shore,
		"result":"ok" if result else 'failed',
		"message":message,
		"qty" : qty,
		"available":available
	}
	response=jsonify(payload)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
# -------------------------------------------

# @app.route('/api/bl/<bl>/<container>', methods=['GET','POST'])
# # @cross_origin()
# def query_bl_container(bl,container):
# 	# 1) Pull Booking data
# 	result = True
# 	message ="OK"
# 	result,message = verify_bl_container(bl,container)
	
# 	payload = {
# 		"bl":bl,
# 		"container":container,
# 		"result":"ACCEPT" if result else 'NOTACCEPT',
# 		"message":message
# 	}
# 	response=jsonify(payload)
# 	response.headers.add('Access-Control-Allow-Origin', '*')
# 	return response
# 	# return json.dumps(payload, indent=4) ,200

# @app.route('/api/bl/<bl>/<container>/reserve', methods=['GET','POST'])
# # @cross_origin()
# def reserve_bl_container(bl,container):
# 	# 1) Pull Booking data
# 	result,message = reserve_Q_bl_container(bl,container)
# 	payload = {
# 		"bl":bl,
# 		"container":container,
# 		"result":"ok" if result else 'failed',
# 		"message":message
# 	}
# 	response=jsonify(payload)
# 	response.headers.add('Access-Control-Allow-Origin', '*')
# 	return response
# 	# return json.dumps(payload, indent=4) ,200



def setKey(key,value):
	return db.set(key,value)

def getKey(key):
	return db.get(key)

def deleteKey(key):
	return db.delete(key)

if __name__ == '__main__':
	app.run(host='0.0.0.0',debug=True)
	# serve(app, host='0.0.0.0', port=8013)
