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

    if ("hola" in texto or "tardes" in texto or "disponible" in texto or "clkmm" in texto):
        agregar_mensajes_log("Entra menu inicial: "+texto)
        data=data_menu_inicial(numero)
    elif "clkshare" in texto:
        agregar_mensajes_log("Entra loop inicial: "+texto)
        data = data_loop_inicial(numero)
    elif ("clkmc" in texto):
        agregar_mensajes_log("entra clkmc o 0: "+texto)
        data = data_menu_principal(numero)
    elif ("1" in texto and len(texto)==1):
        agregar_mensajes_log("Entra busca proveedor o 1: "+texto)
        data=data_busca_proveedor(numero)
    elif ("2" in texto and len(texto)==1):
        agregar_mensajes_log("Entra punto venta o 2: "+texto)
        data=data_abrir_punto_venta(numero)
    elif ("clk_precios_cat" in texto or ("3" in texto and len(texto) == 1)):
        agregar_mensajes_log("Entra clk_precios_cat o 3: "+texto)
        data=data_lista_precios(numero)
    elif ("4" in texto and len(texto) == 1):
        agregar_mensajes_log("Entra ubicacion o 4: "+texto)
        data=data_ubicacion_mc(numero)
    elif ("clk_cotiza" in texto or ("5" in texto and len(texto)==1)):
        agregar_mensajes_log("Entra clk_cotiza o 5: "+texto)
        data = data_proceso_compra_mc(numero)
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
        agregar_mensajes_log("Entra else menu inical: "+texto)
        data=data_menu_inicial(numero)
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

def data_menu_principal(numero):
    data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "menu_inical_mc",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": []
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
                                "payload": "clkorder"
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
                                "payload": "clkdoubts"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "2",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clklprices"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "3",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkother"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "4",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clkmm"
                            }
                        ]
                    }
                ]
            }
        }
    return data
def data_menu_inicial(numero):
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
                                "type": "image",
                                "image": {
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/img_init_2.jpg"
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
                "caption": "Video ilustrativo 1."
            }
        }
    data2={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "document",
            "document": {
                    "link": "https://bot-grupo-mascleaning.onrender.com/static/listado-precio-25.pdf",
                    "caption": "Listado de Precios 2025."
                }
        }
    data3={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "video",
            "video": {
                "link": "https://bot-grupo-mascleaning.onrender.com/static/video-init2.mp4",
                "caption": "Video ilustrativo 2."
            }
        }
    data4={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "document",
            "document": {
                    "link": "https://bot-grupo-mascleaning.onrender.com/static/o-punto-venta.pdf",
                    "caption": "Información de Apertura Punto de Venta."
                }
        }
    data5={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "Da click para regresar al Menú Principal."
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clkmc",
                                "title": "Menú Principal"
                            }
                        }
                    ]
                }
            }
        }
    data_loop_list.append(json.dumps(data1))
    data_loop_list.append(json.dumps(data2))
    data_loop_list.append(json.dumps(data3))
    data_loop_list.append(json.dumps(data4))
    data_loop_list.append(json.dumps(data5))
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
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "2",
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
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/video-init1.mp4"
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
                                "payload": "clk_tienda"
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
                                "payload": "clk_local"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "2",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_neighbor"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "3",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_other"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "4",
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
                                "payload": "clkmc"
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
                                "type": "location",
                                "location": {
                                    "latitude": "18.96996615136263",
                                    "longitude": "-98.30085274771714",
                                    "name": "Grupo Más Cleaning.",
                                    "address": "Grupo Más Cleaning, 72850 Santa Clara Ocoyucan, Pue."
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
                                "payload": "clkmc"
                            }
                        ]
                    }
                ]
            }
        }
    return data
if __name__=='__main__':
    app.run(host='0.0.0.0',port=80,debug=True)