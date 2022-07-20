import os
import sys
import telnetlib
from flask import Flask
from flask_restful import Resource, Api
from flask_cors import CORS
import xml.etree.ElementTree as ET
import requests
import json
import time

######## Declaracion de VARIABLES GLOBALES #######
tn = ''
x = ''
BCF = ''

####### Para realizar prueba de Front-End #######
intAux = 0
#################################################

def conexion_telnet(ip, user, password):

	try:
		tn = telnetlib.Telnet(ip,23,5)
		x = tn.read_until(b'ENTER USERNAME <')
		i = 0
		while(b'ENTER' in x):
			tn.write(user[i].encode('ascii') + b'\n\r')
			x = tn.read_until(b'ENTER PASSWORD <')
			tn.write(password[i].encode('ascii') + b'\n\r')
			x = tn.read_until(b'<')
			print(x)
			i = i + 1
		response = 'successful telnet connection'

	except:
		tn = '-1'
		x = b''
		response = 'failed telnet connection'

	finally:
		print(response)

	return tn,x.decode('ascii')

# Split array with n elements for arrays
def split_array(array, n):
	for i in range(0, len(array), n):
		yield array[i:i + n] 

def getRegional(data_Regional, cellid):

	cellid = list(cellid)

	listAux = []
	for x in cellid:
		if(not x.isnumeric()):
			listAux.append(x)
	aux = ''.join(listAux)
	#print(aux)

	if(aux in data_Regional):
		regionales = data_Regional[aux]
	else:
		# Default
		regionales = [7,5,8]
		
	#print(regionales)

	return regionales

def getDN(regional, cellid):

	URL = f'http://rc{regional}login.rc{regional}.netact.claro.amx/netact/cm/open-api/persistency/OpenCmPersistencyServiceSOAP'

	data = f'''
	<soapenv:Envelope xmlns:soapenv ="http://schemas.xmlsoap.org/soap/envelope/"
	xmlns:oper ="http://www.nsn.com/schemas/public/cm/open-api/persistency/operations"
	xmlns:mod ="http://www.nsn.com/schemas/public/cm/open-api/persistency/model"
	xmlns:quer ="http://www.nsn.com/schemas/public/cm/open-api/persistency/query">
		<soapenv:Header/>
		<soapenv:Body>
			<oper:QueryMOLitesRequest>
			    <mod:configuration mod:confId ="1"/>
			    <quer:query>//NOKBSC:BCF[ name() like "%{cellid}%" ]</quer:query>
			</oper:QueryMOLitesRequest>
		</soapenv:Body>
	</soapenv:Envelope>'''

	auth = ('xxx','xxx')

	response = requests.post(url = URL, data = data, verify = False, auth=auth)

	statusCode = response.status_code
	print(statusCode)

	# Cuando response.status_code == 200, response devuelve True (this is possible because __bool__() is an overloaded method on Response)
	# Otros códigos de estado dentro del rango de 200 a 400, también se consideran exitosos en el sentido de que proporcionan una respuesta viable.
	if(response):

		dataXML = response.text

	else:

		dataXML = None

	return dataXML

def parseDN(dataXML):

	root = ET.fromstring(dataXML)
	#print(root)

	result = root[0][0][1]
	#print(result)

	BCFs = []

	BSC_ID_anterior = ''

	for data in range(0, len(result)):

		DN = result[data].attrib['{http://www.nsn.com/schemas/public/cm/open-api/persistency/model}moId']
		print(DN)
		x = DN.replace('PLMN-PLMN/BSC-','')
		for i in range(0,len(x)):
			if(x[i] == '/'):
				indexSeparator = i
		
		BSC_ID = x[0:indexSeparator]

		BCF = x[indexSeparator:].replace('/BCF-','')

		#print(BCF)
		if(BSC_ID == BSC_ID_anterior):
			BCFs.append(BCF)
			BCFs.append('&')
		else:
			BCFs = [BCF]
			BCFs.append('&')

		BSC_ID_anterior = BSC_ID

	# Elimino el último elemento de la lista que es un "&" para que quede con el formato necesario
	BCFs.pop()
	# convertimos la lista a String
	BCF = ''.join(BCFs)

	#print('BSC-ID: ', BSC_ID)
	#print('BCF: ', BCF)

	return BSC_ID, BCF

def busqueda_datos(data_Regional, data_BSCs, cellid):

	# Se normaliza a mayusculas
	cellid = cellid.upper()

	regionales = getRegional(data_Regional, cellid)

	print('Regionales: ', regionales)

	flag_cellid = True
	flag_BSC = False
	BCF = ''
	BSC = ''
	ip = ''
	dataXML = ''

	for regional in regionales:

		print('Regional: ', regional)

		dataXML = getDN(regional, cellid)

		if(dataXML != None):

			root = ET.fromstring(dataXML)
			#print(root)

			result = root[0][0][1]
			#print(result)

			#print(len(result))
			if(len(result) != 0):
				break
			else:
				dataXML = None

			#print(dataXML)

		else:

			print('Error de autenticación')
			flag_cellid = False

	if(dataXML != None):

		BSC_ID, BCF = parseDN(dataXML)

		for x in data_BSCs['R'+str(regional)]:
			if(x['instance'] == BSC_ID):
				flag_BSC = True
				#print(x['instance'])
				BSC = x['name']
				ip = x['ip']

	else:
			
		flag_cellid = False

	return BSC,ip,BCF,flag_cellid,flag_BSC

def consultas_BSC(tn,x,BCF):

	matriz_BCF = []
	matriz_ET = []
	alarmas_ET = []
	datos_BCF = []
	tramas = []
	error_BCF = []

	tn.write(f'ZEEI:BCF={BCF};'.encode('ascii') + b"\n\r")
	x = tn.read_until(b'RADIO NETWORK CONFIGURATION').decode('ascii')
	i = 0
	lista = [b'BCF',b'TRX-',b'<']
	while(i != 2):
		# Devuelve i (índice del elemento en la lista que encuentra primero), obj (objeto) y el resto (texto que lee)
		(i, obj, res) = tn.expect(lista)
		x = res.decode('ascii')
		print(x)
		if(i == 0):
			(i, obj, res) = tn.expect(lista)
			x = res.decode('ascii')
			print(x)
			if(i == 1):
				# Agrego un símbolo para poder tener referencia dónde arranca una nueva BCF
				datos_BCF.append('#')
				nro_BCF = x[1:5].strip(' ')
				datos_BCF.append(nro_BCF)
				estado_BCF = x[67:70].strip(' ')
				datos_BCF.append(estado_BCF)
			elif(i == 0):
				# Agrego un símbolo para poder tener referencia dónde arranca una nueva BCF
				datos_BCF.append('#')
				nro_BCF = x[1:5].strip(' ')
				datos_BCF.append(nro_BCF)
				estado_BCF = 'NOT FOUND'
				datos_BCF.append(estado_BCF)
		elif(i == 1):
			ET = x[22:26].strip(' ')
			# Evita agregar valores repetidos de ETs
			if(ET not in tramas):
				# Agrega sólo los valores que no se repiten
				tramas.append(ET)
				datos_BCF.append(ET)
	# Soluciona el inconveniente de no mostrar la ET al tener un solo TRX
	# Además tiene en cuenta la ultima ET, que en caso de ser distinta no se mostraba
	if('<' in x):
		if('NOT FOUND' not in x):
			ET = x[22:26].strip(' ')
			# Evita agregar valores repetidos de ETs
			if(ET not in tramas):
				# Agrega sólo los valores que no se repiten
				tramas.append(ET)
				datos_BCF.append(ET)
		else:
			# Agrego un símbolo para poder tener referencia dónde arranca una nueva BCF
			datos_BCF.append('#')
			nro_BCF = x[1:5].strip(' ')
			datos_BCF.append(nro_BCF)
			estado_BCF = 'NOT FOUND'
			datos_BCF.append(estado_BCF)

	# Elimino el primer símbolo y agrego uno al final para poder tener una referencia
	datos_BCF.pop(0)
	datos_BCF.extend('#')

	print(datos_BCF)

	aux = []
	for v in range(0,len(datos_BCF)):
		if(datos_BCF[v] != '#'):
			aux.append(datos_BCF[v])
		else:
			matriz_BCF.append(aux)
			aux = []

	# Normaliza para que sea una Matriz
	aux = []
	if(isinstance(matriz_BCF[0], str)):
		aux.append(matriz_BCF)
		matriz_BCF = aux
		aux = []

	print(matriz_BCF)

	###  Recorre Y saca las ETs de cada Matriz BCF
	###  for w in range(0,len(matriz_BCF)):
	###	   for z in range(2,len(matriz_BCF[w])):
	###		  print(matriz_BCF[w][z])
						
	print(tramas)

	print(x)

	if('-' not in tramas):
		flag_SRAN = False
		# Para verificar estado de las ET
		datos_ET = []
		for w in range(0,len(tramas)):
			tn.write(f'ZUSI:ET,{tramas[w]};'.encode('ascii') + b"\n\r")
			x = tn.read_until(b'EXECUTION STARTED').decode('ascii')
			x = tn.read_until(b'ET').decode('ascii')
			x = tn.read_until(b'<').decode('ascii')
			print(x)
			datos_ET.append(tramas[w])
			datos_ET.append(x[14:19].strip(' '))

			tn.write(f'ZAHO:ET,{tramas[w]};'.encode('ascii') + b"\n\r")
			x = tn.read_until(b'ALARMS CURRENTLY ON').decode('ascii')
			print(x)
			x = tn.read_until(b'END OF ALARMS CURRENTLY ON')
			print(x)
			if(x == b'\r\n\n\r\nEND OF ALARMS CURRENTLY ON'):
				datos_ET.append('NO')
			else:
				alarmas_ET.append(tramas[w])
				alarm_anterior = ''
				s = x.split(b' \r\n ') 
				for c in range(0,len(s)):
					if(c %2 != 0):
						alarm = s[c].decode('ascii')
						alarm = alarm[15:].strip(' ')
						if(alarm_anterior != ''):
							alarm = alarm_anterior + " - " + alarm
						alarm_anterior = alarm
				alarmas_ET.append(alarm)
				datos_ET.append('SI')

		# Normaliza para que sea una Matriz
		# Split array with n elements for arrays
		alarmas_ET = list(split_array(alarmas_ET, 2))

		print(alarmas_ET)

		print(datos_ET)

		# Normaliza para que sea una Matriz
		# Split array with n elements for arrays
		matriz_ET = list(split_array(datos_ET, 3))

		print(matriz_ET)

	else:
		print('2G SRAN')
		flag_SRAN = True

	return matriz_BCF,matriz_ET,alarmas_ET,flag_SRAN

app = Flask(__name__)
# Soluciona los errores de intercambio de recursos de origen cruzado - Control de acceso HTTP (CORS)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
###############
api = Api(app)
###############
app.config.from_object(__name__)
# The secret key is needed to keep the client-side sessions secure
app.config['SECRET_KEY'] = '\xaf\r\xedP\xa0\x15\x106\xa8w\x05\xc3\x85gY\xe4\x0b\x8f#\xbcu\x1f\xf4\xb5'

####### Carga de datos CellID-Regional JSON #######
# El archivo no se encuentra por tener información sensible de la empresa
with open('data_Regional.json') as file:
	data_Regional = json.load(file)
###################################################

######### Carga de datos BSC-IPs JSON #########
# El archivo no se encuentra por tener información sensible de la empresa
with open('data_BSCs.json') as file:
	data_BSCs = json.load(file)
###############################################

class ApiRestFul(Resource):
	def get(self, cellid, checkbox):

		####################
		flag_SRAN = False
		flag_Telnet = True
		####################

		# Se usa la palabra global para que se pueda modificar dentro de la funcion una variable global
		global BCF
		global tn
		global x

		BSC,ip,BCF,flag_cellid,flag_BSC = busqueda_datos(data_Regional, data_BSCs, cellid)
		
		###########################################################################
		########################## Codigo de produccion ###########################
		if(flag_cellid == True and flag_BSC == True):

			# Datos para la conexión
			user = ['xxx','xxx', 'xxx']
			password = ['xxx','xxx', 'xxx']

			### Se conecta por telnet a una BSC ###
			tn,x = conexion_telnet(ip,user,password)

			if(tn != '-1'):

				if(BSC in x):

					print(f'IP: {ip}, corresponde a la BSC: {BSC}')

					matriz_BCF,matriz_ET,alarmas_ET,flag_SRAN = consultas_BSC(tn,x,BCF)

					### Formateo de datos a JSON ###
					data_json = {
						cellid: {
							'flag_cellid': flag_cellid,
							'flag_BSC': flag_BSC,
							'matriz_BCF': matriz_BCF,
							'matriz_ET': matriz_ET,
							'flag_SRAN': flag_SRAN,
							'flag_Telnet': flag_Telnet,
							'alarmas_ET': alarmas_ET,
							'BSC': BSC,
							'ip': ip,
							'BCF': BCF
						}
					}

					if(checkbox == 'off'):

						print('Conexion telnet cerrada')
						tn.close()

						# Se inicializan las variables globales
						tn = ''
						x = ''
						BCF = ''

				else:
					print('Error: IP incorrecta de BSC')

			else:
				print('Error: No se puede establecer conexión con la BSC')
				flag_Telnet = False
				data_json = {
					cellid: {
						'flag_Telnet': flag_Telnet
					}
				}
		##########################################################################

		#########################################################
		### Para realizar prueba de Front-End ###
		#if(flag_cellid and flag_BSC == True):
		#	if(cellid == 'SF903'):
		#		aux = []
		#		matriz_BCF = [['234','WO','23','25'],['567','WO','27']]
		#		if(isinstance(matriz_BCF[0], str)):
		#			aux.append(matriz_BCF)
		#			matriz_BCF = aux
		#			aux = []
		#		matriz_ET = [['23','WO-EX','NO'],['25','WO-EX','SI'],['27','WO-EX','SI']]
		#		if(isinstance(matriz_ET[0], str)):
		#			aux.append(matriz_ET)
		#			matriz_ET = aux
		#			aux = []
		#		alarmas_ET = [['25','AIS RECEIVED'],['27','MONITOR FAIL - PCM LINE REMOTE AND ALARM']]
		#		if(isinstance(alarmas_ET[0], str)):
		#			aux.append(alarmas_ET)
		#			alarmas_ET = aux
		#			aux = []
		#		flag_SRAN = False
		#		flag_Telnet = True
		#
		#	data_json = {
		#		cellid: {
		#			'flag_cellid': flag_cellid,
		#			'flag_BSC': flag_BSC,
		#			'matriz_BCF': matriz_BCF,
		#			'matriz_ET': matriz_ET,
		#			'flag_SRAN': flag_SRAN,
		#			'flag_Telnet': flag_Telnet,
		#			'alarmas_ET': alarmas_ET,
		#			'BSC': BSC,
		#			'ip': ip,
		#			'BCF': BCF
		#		}
		#	}
		#########################################################

		elif(flag_cellid == False):
			print('Error: Valor de Cell-ID no encontrado')

			data_json = {
				cellid: {
					'flag_Telnet': flag_Telnet,
					'flag_cellid': flag_cellid,
					'flag_BSC': flag_BSC
				}
			}

		elif(flag_BSC == False):
			print('Error: Valor de BSC no encontrado')

			data_json = {
				cellid: {
					'flag_Telnet': flag_Telnet,
					'flag_cellid': flag_cellid,
					'BSC': BSC,
					'flag_BSC': flag_BSC
				}
			}

		return data_json

api.add_resource(ApiRestFul, '/api/<string:cellid>&<string:checkbox>') # http://127.0.0.1:5000/cellid&checkbox
######################################################################

class ApiRestFul_RT(Resource):
	def get(self, cellid):

		# Se usa la palabra global para que se pueda modificar dentro de la funcion una variable global
		global BCF
		global tn
		global x

		######################### Codigo de produccion ########################
		matriz_BCF,matriz_ET,alarmas_ET,flag_SRAN = consultas_BSC(tn,x,BCF)
		#######################################################################

		print('update render')

		###################  Para realizar prueba de Front-End  #####################
		#global intAux
		#intAux = intAux+1
		#cellid = 'SF903'
		#matriz_BCF = [[intAux,'WO','22','33','44']]
		#matriz_ET = [['22','WO-EX','SI'],['33','WO-EX','NO'],['44','WO-EX','NO']]
		#alarmas_ET = [['22','MONITOR FAIL - PCM LINE REMOTE AND ALARM']]
		#flag_SRAN = False
		#############################################################################

		data_json = {
			cellid: {
				'matriz_BCF': matriz_BCF,
				'matriz_ET': matriz_ET,
				'flag_SRAN': flag_SRAN,
				'alarmas_ET': alarmas_ET
			}
		}
		
		return data_json

api.add_resource(ApiRestFul_RT, '/api/<string:cellid>/_update')

class ApiRestFul_CloseTn(Resource):
	def get(self):

		# Se usa la palabra global para poder modificar una variable global
		global tn
		global x
		global BCF

		######## Codigo de produccion ########
		tn.close()
		######################################

		# Se inicializan las variables globales
		tn = ''
		x = ''
		BCF = ''

		#### Para realizar prueba de Front-End ####
		global intAux
		intAux = 0
		###########################################

		print('Conexion telnet cerrada')

		return 'Conexion telnet cerrada'

api.add_resource(ApiRestFul_CloseTn, '/_CloseTn')


if __name__ == "__main__":

###########################################################
	#app.config['TEMPLATES_AUTO_RELOAD'] = True      
	#app.jinja_env.auto_reload = True
###########################################################
	# Al colocar la red 0.0.0.0 permite que la web se vea en la red local
	app.run(debug=True, host='0.0.0.0', port='5000')


