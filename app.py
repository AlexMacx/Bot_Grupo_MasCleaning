from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import http.client
import json

app = Flask(__name__)

#Configuracion de la base de datos SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gmcpython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Modelo de la tabla log
class Log(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.utcnow)
    texto = db.Column(db.TEXT)

#Crear la tabla si no existe
with app.app_context():
    db.create_all()
#Función para ordenar los registros por fecha y  hora
def ordenar_fecha_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    #Obtener todos los registros de la bd
    registros = Log.query.all()
    registros_ordenados = ordenar_fecha_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

@app.route('/video')
def video_home():
    #Endpoint para obtener video
    return render_template('video.html')

mensajes_log = []

#Funcion para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)

    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()

#Token de verificación para la configuración
TOKEN_MCCODE = "MASCLEANINGCODE"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        response = recibir_mensajes(request)
        return response

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_MCCODE:
        return challenge
    else:
        return jsonify({'error':'Token invalido'}), 401
    
def extrae_numero(numFrom):
    if(len(numFrom)==13):
        return numFrom[0:2]+numFrom[3:]
    else:
        return numFrom

def recibir_mensajes(req):
    try:
        req = request.get_json()
        agregar_mensajes_log(json.dumps(req))
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        objeto_mensaje = value['messages']
        
        if objeto_mensaje:
            messages = objeto_mensaje[0]
            init_log_str = "Entro: recibir mensajes - if "
            if 'type' in messages:
                tipo = messages['type']
                #Guardando logs en DB
                agregar_mensajes_log(init_log_str+"type: "+json.dumps(messages))
                if tipo == 'interactive':
                    tipo_interactivo = messages["interactive"]["type"]

                    if tipo_interactivo == "button_reply":
                        texto = messages["interactive"]["button_reply"]["id"]
                        numero = messages['from']
                        numero = extrae_numero(numero)

                        enviar_mensajes_whatsapp(texto, numero)

                    if tipo_interactivo == "list_reply":
                        texto = messages["interactive"]["list_reply"]["id"]
                        numero = messages['from']
                        numero = extrae_numero(numero)

                        enviar_mensajes_whatsapp(texto, numero)
                if tipo == 'button':
                    texto = messages["button"]["payload"]
                    numero = messages['from']
                    numero = extrae_numero(numero)
                    agregar_mensajes_log("type button: "+texto)
                    enviar_mensajes_whatsapp(texto, numero)
                
                if 'text' in messages:
                    texto = messages['text']['body']
                    numero = messages['from']
                    numero = extrae_numero(numero)
                    
                    enviar_mensajes_whatsapp(texto, numero)
                    #Guardando logs en BD
                    #agregar_mensajes_log(init_log_str+"type: "+json.dumps(messages))

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})

def enviar_mensajes_whatsapp(texto, numero):
    texto = texto.lower()

    if (texto.__contains__("hola") or texto.__contains__("tardes") or texto.__contains__("disponible")):
        data=data_inicial(numero)
    elif (texto.__contains__("clkmc") or texto.__contains("0")):
        agregar_mensajes_log("entra clkmc o 0: "+texto)
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀📌Hola, ¿Cómo podemos apoyarte? Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. SER SU PROVEDOR DE PRODUCTOS DE LIMPIEZA. 🔗\n2️⃣. ABRIR UN PUNTO DE VENTA DE PRODUCTOS DE LIMPIEZA. 🏬\n3️⃣. CONOCER LISTA DE PRECIOS. 💲📄\n4️⃣. DONDE ESTÁN UBICADOS. 📍\n5️⃣. PROCESO DE COMPRA. 📝"
            }
        }
    elif "1" in texto:
        data=data_busca_proveedor(numero)
    elif "clk_cotiza" in texto:
        data = data_proceso_compra_mc(numero)
    elif "clk_precios_cat" in texto:
        data=data_lista_precios(numero)
    elif "4" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "audio",
            "audio": {
                "link": "https://filesamples.com/samples/audio/mp3/sample1.mp3"
            }
        }
    elif "5" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "text": {
                "preview_url": True,
                "body": "Introduccion al curso! https://youtu.be/6ULOE2tGlBM"
            }
        }
    elif "6" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🤝 En breve me pondre en contacto contigo. 🤓"
            }
        }
    elif "7" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "📅 Horario de Atención : Lunes a Viernes. \n🕜 Horario : 9:00 am a 5:00 pm 🤓"
            }
        }
    elif "boton" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "recipient_type": "individual",
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "¿Confirmas tu registro?"
                },
                "footer": { # optional
                    "text": "Selecciona una de las opciones"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btnsi",
                                "title": "Si" 
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btnno",
                                "title": "No" 
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "btnmaybe",
                                "title": "Tal Vez" 
                            }
                        }
                    ]
                }
            }
        }
    elif "btnsi" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Muchas gracias por aceptar."
            }
        }
    elif "btnno" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Es una lastima."
            }
        }
    elif "btnmaybe" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Estaré a la espera."
            }
        }
    elif "lista" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "recipient_type": "individual",
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": "Opciones MC"
                },
                "body": {
                    "text": "Selecciona algúna opción."
                },
                "footer": {
                    "text": "Selecciona una de las opciones para poder ayudarte."
                },
                "action": {
                    "button": "Ver Opciones",
                    "sections":[
                        {
                            "title":"Compra y Venta",
                            "rows": [
                                {
                                    "id":"chkcompra",
                                    "title": "Comprar",
                                    "description": "Compra los mejores artículos de tecnología."
                                },
                                {
                                    "id":"chkventa",
                                    "title": "Vender",
                                    "description": "Vende lo que ya no estes usando."
                                }
                            ]
                        },
                        {
                            "title":"Distribución y Entrega",
                            "rows": [
                                {
                                    "id":"chklocal",
                                    "title": "Local",
                                    "description": "Compra los mejores artículos de tecnología."
                                },
                                {
                                    "id":"chkentrega",
                                    "title": "Entrega",
                                    "description": "La entrega se realiza todos los días."
                                }
                            ]
                        }
                    ]
                }
            }
        }
    elif "chkcompra" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Muchas gracias por tu compra, este es el resumen."
            }
        }
    elif "chkventa" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Tu producto está a punto de tener mucha suerte."
            }
        }
    elif "chklocal" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "location",
            "location": {
                "latitude": "-12.067158831865067",
                "longitude": "-77.03377940839486",
                "name": "Matriz de distribución",
                "address": "Calle 1 equina calle 2"
            }
        }
    elif "chkentrega" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Compartenos tu dirreción para agendar entrega"
            }
        }
    else:
        data=data_inicial(numero)
    #Convertir el diccionario a formato JSON
    if type(data) is not list:
        data = json.dumps(data)

    tkn = "EAApgHYrrpPkBO7vP46IL4ih3CT7M1QXQTZCWDO29lUArch4IelhZABgwFhMhWN9fpexrNKv5NMnhkilXXgD3sFOzYf2Xi3sTwMggClvcx852kWmZAF47vfZBYbnjKqw7FtGhLEBEPKQGoo73pzKMa3zzEvZCSm9mXnvb2uoJHICm7zUd5c42wtmq0c93tkolHPYu5vc44OtVvJYgN"
    bearer = "Bearer "+tkn

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : bearer
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        url_req = "/v21.0/500359583168203/messages"
        if type(data) is not list:
            connection.request("POST",url_req, data, headers)
            response = connection.getresponse()
            agregar_mensajes_log(json.dumps(numero))
            agregar_mensajes_log(json.dumps(response.read().decode()))
        else:
            indice = 0
            for data_item in data:
                connection.request("POST",url_req, data_item, headers)
                response = connection.getresponse()
                agregar_mensajes_log("número "+str(indice)+": "+json.dumps(numero))
                agregar_mensajes_log("número "+str(indice)+": "+json.dumps(response.read().decode()))
                indice+=1
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()

def data_inicial(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "bienvenida_mc",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "video",
                                "video": {
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/video-bienvenida.mp4"
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": []
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkshare"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "1",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkmc"
                            }
                        ]
                    }
                ]
            }
        }
    return data
def data_loop_inicial(numero):
    data_loop_list = []
    data1={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "video",
            "video": {
                "link": "https://bot-grupo-mascleaning.onrender.com/static/video-init1.mp4",
                "caption": "Video ilustrativo 1, ingresa 0 para continuar"
            }
        }
    data2={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "document",
            "document": {
                    "link": "https://bot-grupo-mascleaning.onrender.com/static/listado-precio-25.pdf",
                    "caption": "Listado de Precios 2025, ingresa 0 para continuar"
                }
        }
    data3={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "video",
            "video": {
                "link": "https://bot-grupo-mascleaning.onrender.com/static/video-init2.mp4",
                "caption": "Video ilustrativo 2, ingresa 0 para continuar"
            }
        }
    data4={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "document",
            "document": {
                    "link": "https://bot-grupo-mascleaning.onrender.com/static/o-punto-venta.pdf",
                    "caption": "Apertura Punto de Venta, ingresa 0 para continuar"
                }
        }
    data_loop_list.append(json.dumps(data1))
    data_loop_list.append(json.dumps(data2))
    data_loop_list.append(json.dumps(data3))
    data_loop_list.append(json.dumps(data4))
    return data_loop_list
def data_busca_proveedor(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "busca_proveedor_mc",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/img_init.jpg"
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": []
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_cotiza"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "1",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_precios_cat"
                            }
                        ]
                    }
                ]
            }
        }
    return data
def data_abrir_punto_venta(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "abrir_punto_venta_mc",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "video",
                                "video": {
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/video-bienvenida.mp4"
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": []
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkshare"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "1",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkmc"
                            }
                        ]
                    }
                ]
            }
        }
    return data
def data_lista_precios(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "lista_precios_mc",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/listado-precio-25.pdf"
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": []
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "0"
                            }
                        ]
                    }
                ]
            }
        }
    return data
def data_ubicacion_mc(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "ubicacion_mc",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "video",
                                "video": {
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/video-bienvenida.mp4"
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": []
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkshare"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "1",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkmc"
                            }
                        ]
                    }
                ]
            }
        }
    return data
def data_proceso_compra_mc(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "proceso_compra_mc",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "image",
                                "image": {
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/img_compra_cotiza.jpg"
                                }
                            }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": []
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "0"
                            }
                        ]
                    }
                ]
            }
        }
    return data
if __name__=='__main__':
    app.run(host='0.0.0.0',port=80,debug=True)