import re
import os
import json
import time
import requests
from tabulate import tabulate
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as BS


CITY = {}
STATE = {}
COUNTRY = {}
WORK_DIR = ""
DATA = {}
EXCLUSIONS_LIST = ['datehourly','moon','recHi','recHiYr','recLo','recLoYr','recRain','recRainYr','histRain','skyCodes','skyImages']


def init():
	"""
	API to initialize some processes before data collection,
	like collecting the data from json files.

	INPUT: None
	OUTPUT: None
	"""
	global WORK_DIR
	WORK_DIR = os.getcwd()
	global CITY,STATE,COUNTRY
	with open("%s/content/cities.json"%WORK_DIR,"r") as f:
		CITY = json.load(f)
	CITY = CITY['cities']
	with open("%s/content/states.json"%WORK_DIR,"r") as f:
		STATE = json.load(f)
	STATE = STATE['states']
	with open("%s/content/countries.json"%WORK_DIR,"r") as f:
		COUNTRY = json.load(f)
	COUNTRY = COUNTRY['countries']


def verify_city(name):
	"""
	API to verify if the city entered by user 
	is present in the list of cities.
	
	INPUT: City Name
	OUTPUT: None/Dictionary
	"""	
	for elem in CITY:
		if elem["name"].lower() == name:
			return elem["state_id"]
	return None


def get_state(state_id):
	"""
	API to collect state info for a valid city.
	
	INPUT: State ID
	OUTPUT: Dictionary/None 
	"""
	for elem in STATE:
		if elem["id"] == state_id:
			return elem
	return None


def get_country(country_id):
	"""
	API to collect country details after fetching 
	state related data.

	INPUT: Country ID
	OUTPUT: Dictionary/None
	"""
	for elem in COUNTRY:
		if elem["id"] == country_id:
			return elem
	return None


def get_inputs():
	"""
	Prompt user to enter city name.
	
	INPUT: None
	OUTPUT: Tuple/None
	"""
	city = input("Enter the city name: ")
	state_id = verify_city(city.lower())

	if state_id is None:
		err_msg = "'%s' is not present in the list of cities"%city
		print()
		print("#"*(len(err_msg)+4))
		print("# %s #"%err_msg)
		print("#"*(len(err_msg)+4))
		return None

	state = get_state(state_id)
	country = get_country(state["country_id"])

	city_name = re.sub(" ","-",city.strip())
	state_name = re.sub(" ","-",state["name"].strip())
	country_name = re.sub(" ","-",country["name"].strip())

	return city_name,state_name,country_name


def create_http_req(city,state,country):
	"""
	Create the http address that will retrieve the response

	INPUT: City, State and Country
	OUTPUT: request object
	"""
	head = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}
	address = "https://www.msn.com/en-us/weather/today/%s%s%s/we-city"%(city.lower(),state.lower(),country.lower())
	parameters = {'q':'%s-%s'%(city.lower(),state.lower())}
	req = requests.get(address,params=parameters,headers=head)
	return req


def get_title(et):
	"""
	Fetches the title field from the http response.

	INPUT: etree object created from http response
	OUTPUT: Title Content
	"""
	root = et.getroot()
	title = root.find('./head/title')
	return title


def filter_xml(content):
	"""
	Remove unnecessary tags from the http response, like
	1) Head
	2) Scripts
	3) Input fields
	Then create an html file and save the filtered content.

	INPUT: Http response
	OUTPUT: filename	
	"""
	soup = BS(content,"lxml")

	for elem in ["limit","script","meta","link","style","noscript"]:
		[x.extract() for x in soup.findAll(elem)]

	content = soup.prettify()

	filename = "dummy.html"
	with open(filename,"w") as myFile:
		myFile.write(content)
	return filename


def collect_dates(et):
	"""
	Collect the dates that will be printed on screen.
	User can then select which date he wants to see the data for.

	INPUT: element tree
	OUTPUT: None
	"""
	global DATA
	root = et.getroot()
	body = root.find('body')
	xpath = ".//*[@class='forecast-list']/li/a"
	forecast_list = body.findall(xpath)
	count = 1

	for entries in forecast_list:
		day = entries.findall("./*[@class='dt']/span")[0].text.strip()
		date = entries.findall("./*[@class='dt']/span")[1].text.strip()
		DATA['day%d'%count]['day'] = "%s %s"%(day,date)
		


def collect_all_data(et):
	"""
	Parses through the response and collects the entire data
	that includes hourly status throughout the week.
	
	INPUT: Element tree
	OUTPUT: None
	"""
	global DATA
	root = et.getroot()
	xpath = ".//ul[@class='forecast-list']/li/a"
	data = root.findall(xpath)
	count = 1
	if data is not None:
		for elem in data:
			content = {}
			descr = elem.attrib['aria-label'].strip()
			content['descr'] = descr
			for attributes in ["data-detail","data-hourly"]:
				attr_val = json.loads(elem.attrib[attributes].strip())
				for key,val in attr_val.items():
					if key in EXCLUSIONS_LIST:
						continue
					content[key] = val
			DATA['day%d'%count] = content
			count += 1
	collect_dates(et)


def print_data_on_console(day,detail=False):
	pass

def print_on_console(day=None, detailed=False):
	"""
	Prints the today's weather condition on console

	INPUT: None
	OUTPUT: None
	"""
	if day==None:
		data = DATA['day1']
		day = data['day']
		t_high = data['high']
		t_low = data['low']
		sky_txt = data['skytext']
		mornNat = data['mornNat']
		evenNat = data['evenNat']
		sunrise = data['sunrise']
		sunset = data['sunset']
		precip = sum([int(x) for x in data['precipitations']])/len(data['precipitations'])
		print("\nToday's Weather Forecast:\nMax Temp: %d(F)\nMin Temp: %d(F)\nChances of Rain: %.1f\nSky: %s\nSunrise: %s\nSunset: %s\nDaytime: %s\nNighttime: %s\n"%(t_high,t_low,precip,sky_txt,sunrise,sunset,mornNat,evenNat))
	else:
		day = 'day%d'%day
		data = DATA[day]
		day = data['day']
		t_high = data['high']
		t_low = data['low']
		sky_txt = data['skytext']
		mornNat = data['mornNat']
		evenNat = data['evenNat']
		sunrise = data['sunrise']
		sunset = data['sunset']
		precip = sum([int(x) for x in data['precipitations']])/len(data['precipitations'])
		if detailed == False:
			print("\nWeather Forecast of %s:\nMax Temp: %d(F)\nMin Temp: %d(F)\nChances of Rain: %.1f\nSky: %s\nSunrise: %s\nSunset: %s\nDaytime: %s\nNighttime: %s\n"%(day,t_high,t_low,precip,sky_txt,sunrise,sunset,mornNat,evenNat))
		else:
			moonrise = data['moonrise']
			moonset = data['moonset']
			table_1_heading = ["Temp High(F)","Temp Low(F)","Rainfall Probability","Sky","Sunrise","Sunset","Moonrise","Moonset"] 
			table_2_heading = ["Time","Temperature","Precipitation","Sky","Wind Direction","Wind Speed"]
			table_1 = [[t_high,t_low,precip,sky_txt,sunrise,sunset,moonrise,moonset]]
			table_2 = []
			for i in range(len(data['times'])):
				temp = []
				temp.append(data['times'][i]+'m')
				temp.append(data['temperatures'][i])
				temp.append(data['precipitations'][i])
				temp.append(data['skyTexts'][i])
				temp.append(data['windDir'][i])
				temp.append(data['wind'][i])
				table_2.append(temp)
			print("\n\n")
			print("===Throughout the day===")
			print(tabulate(table_1,table_1_heading,tablefmt='grid'))
			print("\n")
			time.sleep(.5)
			print("===Hourly details===")
			print(tabulate(table_2,table_2_heading,tablefmt='grid'))
			print("\n")
			

def prompt_for_more_options():
	"""
	Prompts user if he wants some additional details.
	
	INPUT: None
	OUTPUT: String
	"""
	print("\nYou can even try the below options:\n1)Detailed description of today's weather\n2)Description from the next 7 days\n3)Detailed description of the next 7 days\nPress any other key to exit")
	x = input("::")
	if x not in ['1','2','3']:
		print("Thankyou for using this tool!!")
		x = None
	return x

def main():
	"""
	Main function starts from here
	
	INPUT: None
	OUTPUT: None
	"""
	data = get_inputs()
	if data == None:
		return
	city,state,country = data	
	req = create_http_req(city,state,country)
	content = req.text
	
	filename = filter_xml(content)
	et = ET.parse(filename)
	title = get_title(et).text
	collect_all_data(et)
	print_on_console()
	time.sleep(2)
	x = prompt_for_more_options()
	if x is None:
		return
	else:
		if x == '1':
			print_on_console(day=1,detailed=1)
	


if __name__ == "__main__":
	#try:
	init()
	main()
	#except Exception as e:
	#	print(e)
	#finally:
	#	try:
	#		#pass
	#		os.remove("%s/dummy.html"%WORK_DIR)
	#	except:
	#		pass

