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
#https://bot-grupo-mascleaning.onrender.com/static/video-home.mp4
    if "hola" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "video",
            "video": {
                "link": "https://bot-grupo-mascleaning.onrender.com/static/video-bienvenida.mp4",
                "caption": " Hola, Bienvenido a Mas Cleaning."
            }
        }
    elif "1" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."
            }
        }
    elif "2" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "location",
            "location": {
                "latitude": "-12.067158831865067",
                "longitude": "-77.03377940839486",
                "name": "Estadio Nacional del Perú",
                "address": "Cercado de Lima"
            }
        }
    elif "3" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "document",
            "document": {
                    "link": "https://www.turnerlibros.com/wp-content/uploads/2021/02/ejemplo.pdf",
                    "caption": "Temario del Curso #001"
                }
            }
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
    elif "0" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, visita mi web anderson-bastidas.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del Curso. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
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
    elif "media" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "bienvenida_mc",
                "languaje": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "video",
                                "image": {
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
                                "payload": "PAYLOAD"
                            }
                        ]
                    }
                ]
            }
        }
    else:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, visita mi web anderson-bastidas.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del Curso. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
            }
        }
    #Convertir el diccionario a formato JSON
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
        connection.request("POST","/v21.0/500359583168203/messages", data, headers) 
        response = connection.getresponse()
        
        agregar_mensajes_log(json.dumps(numero))
        
        agregar_mensajes_log(json.dumps(response.read().decode()))
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()

if __name__=='__main__':
    app.run(host='0.0.0.0',port=80,debug=True)