import schedule
import time
from datetime import datetime, timedelta
import redis
import requests
import json

# db = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)
db = redis.StrictRedis('tq-redis', 6379, charset="utf-8", decode_responses=True)
URL_MAINGATE = 'http://www.truckq_api.laemchabangport.com:8043/TQ_API_TLC/api/TLC_Gatein/getDetail'


# @app.route('/container/<container>/<truck_licence>/<action>', methods = ['GET'])
# If Key(terminal) does not exist , will return Now-24hr.
def get_last_exe_time(terminal):
	key = '%s:last_execute' % (terminal)
	ttl = 60*60*6 #6 hours , 60*60*3

	now = datetime.now() # current date and time
	date_time = now.strftime("%Y-%m-%d %H:%M:%S")

	if not db.exists(key): #does the hash exist?
		last_24hr 		= datetime.today() - timedelta(days=1) # last 24 hours
		last_24hr_str 	= last_24hr.strftime("%Y-%m-%d %H:%M:%S")
		value 			= last_24hr_str
	else :
 		value = db.get(key) #get all the keys in the hash

	db.set(key,date_time) #store dict in a hashjson.dumps(json_data)
	db.expire(key, ttl) #expire it after a year
	return value

def pulling_PAT(terminal,payload):
	# try:
	res = requests.post(URL_MAINGATE,payload)
	# Save to Database
	ttl = 60*60*4 #3 hours , 60*60*3
	for truck in res.json():
		# Key By Truck license
		key = f"{terminal}:truck:{truck['Truck_License_NO']}"
		db.set(key,json.dumps(truck)) #store dict in a hashjson.dumps(json_data)
		db.expire(key, ttl) #expire it after a year

		#Key by Container
		if truck['CONTAINER_NO'] :
			key = f"container:{truck['CONTAINER_NO']}"
			db.set(key,json.dumps(truck)) #store dict in a hashjson.dumps(json_data)
			db.expire(key, ttl) #expire it after a year

	return len(res.json())
	# 	# End Save
	# except Exception as e:
	# 	return 0
	
	
	

def pulling_b1():
	now = datetime.now() # current date and time
	start_time 	= get_last_exe_time('B1')
	stop_time 	= now.strftime("%Y-%m-%d %H:%M:%S")

	b1_json ={
		"User":"lcbb1adm",
		"Password":"P@55w0rd",
		"Start_Date":"%s" % start_time,
		"End_Date": "%s" % stop_time
	}
	print(b1_json)
	print(pulling_PAT('B1',b1_json))
	# print(f"Pulling data of B1. from {get_last_exe_time('B1')} to {datetime.now()}")
	# print(f"New TruckQ : {pulling_PAT(b1_json)} records")

def pulling_a0():
	now = datetime.now() # current date and time
	start_time 	= get_last_exe_time('A0')
	stop_time 	= now.strftime("%Y-%m-%d %H:%M:%S")

	a0_json ={
		"User":"lcba0adm",
		"Password":"P@55w0rd",
		"Start_Date":"%s" % start_time,
		"End_Date": "%s" % stop_time
	}
	print(a0_json)
	print(pulling_PAT('A0',a0_json))
	# print(f"Pulling data of A0. from {get_last_exe_time('A0')} to{datetime.now()}")
	# print(f"New TruckQ : {pulling_PAT(a0_json)} records")

schedule.every(5).minutes.do(pulling_b1)
schedule.every(5).minutes.do(pulling_a0)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)
# schedule.every(5).to(10).minutes.do(job)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)
# schedule.every().minute.at(":17").do(job)

# Initial run
pulling_b1()
pulling_a0()
#------------
while True:
	schedule.run_pending()
	time.sleep(1)



# @app.route('/')
# @app.route('/<terminal>')
# def hello_world(terminal='B1'):
# 	from datetime import datetime
# 	now = datetime.now() # current date and time
# 	date_time = now.strftime("%Y-%m-%d")

# 	a0_json ={
# 	"User":"lcba0adm",
# 	"Password":"P@55w0rd",
# 	"Start_Date":"%s 00:00:00" % date_time,
# 	"End_Date": "%s 23:59:59" % date_time
# 	}

# 	b1_json ={
# 		"User":"lcbb1adm",
# 		"Password":"P@55w0rd",
# 		"Start_Date":"%s 00:00:00" % date_time,
# 		"End_Date":	"%s 23:59:59" % date_time
# 	}
# 	url = a0_json if terminal == 'A0' else b1_json
# 	res = requests.post(URL_MAINGATE,url)
# 	# return 'Ok' if res.ok else 'Failed'
# 	# return jsonify(res.json())
# 	# '.decode('utf8')'
# 	return render_template('maingate.html', trucks=res.json() ,terminal=terminal,report_date=date_time)



