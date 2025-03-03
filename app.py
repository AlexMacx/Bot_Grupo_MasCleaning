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
        return jsonify({'message':'EVENT_RECEIVED'+str(e)})

def enviar_mensajes_whatsapp(texto, numero):
    texto = texto.lower()

    if ("informacion" in texto or "informaci\u00f3n" in texto or "clkmm" in texto):
        agregar_mensajes_log("Entra menu inicial: "+texto)
        data=data_menu_inicial(numero)
    elif "clkother" in texto:
        agregar_mensajes_log("Entra menu otro: "+texto)
        data = data_otro(numero)
    elif ("clkmc" in texto):
        agregar_mensajes_log("Entra clkmc (menu soy gmc): "+texto)
        data = data_menu_soy_gmc(numero)
    elif("clknewmc" in texto):
        agregar_mensajes_log("Entra clkmc (menu quiero ser gmc): "+texto)
        data = data_menu_quiero_ser_gmc(numero)
    elif("clkdeliver" in texto):
        agregar_mensajes_log("Entra clkmc (menu envios): "+texto)
        data = data_envios(numero)
    elif ("clksuaviza" in texto):
        agregar_mensajes_log("Entra clksuaviza: "+texto)
        data=data_elab_suaviza(numero)
    elif("clksell" in texto):
        agregar_mensajes_log("Entra clksell: "+texto)
        data=data_punto_venta(numero)
    elif("clk_infosell" in texto):
        agregar_mensajes_log("Entra clk_infosell: "+texto)
        data=data_info_pv(numero)
    elif ("clkdoubts" in texto):
        agregar_mensajes_log("Entra clkdoubts: "+texto)
        data=data_dudas_elabora_mc(numero)
    elif ("clklpricess" in texto):
        agregar_mensajes_log("Entra clklpricess: "+texto)
        data=data_lista_precios(numero)
    elif ("clklocation" in texto):
        agregar_mensajes_log("Entra clklocation: "+texto)
        data=data_ubicacion_mc(numero)
    elif ("clkorder" in texto):
        agregar_mensajes_log("Entra clkorder: "+texto)
        data = data_proceso_compra_mc(numero)
    elif ("clk_lmulti" in texto):
        agregar_mensajes_log("Entra clk_lmulti: "+texto)
        data = data_elab_lmulti(numero)
    elif ("clk_ltrastes" in texto):
        agregar_mensajes_log("Entra clk_ltrastes: "+texto)
        data = data_elab_lavatrastes(numero)
    elif ("clk_deter" in texto):
        agregar_mensajes_log("Entra clk_deter: "+texto)
        data = data_elab_detergente(numero)
    elif "chkentrega" in texto: #Posiblemente se quite
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Compartenos tu direción para agendar entrega"
            }
        }
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

def data_menu_soy_gmc(numero):
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
                                "payload": "clklpricess"
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
                                "payload": "clknewmc"
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
def data_menu_quiero_ser_gmc(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "quiero_ser_gmc",
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
                                "payload": "clklocation"
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
                                "payload": "clkdeliver"
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
                                "payload": "clklpricess"
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
                                "payload": "clksell"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "5",
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
def data_otro(numero):
    data={
            "messaging_product": "whatsapp",
            "to": numero,
            "recipient_type": "individual",
            "type": "image",
            "image": {
                "link": "https://bot-grupo-mascleaning.onrender.com/static/img_otros.jpg",
                "caption": "Saludos, soy José Luis Hernandez, ¿cómo puedo apoyarte? \nEscribeme o llamame por este medio, será un placer atenderte."
            }
        }
    return data
# Inicia respuesta a botones dfuncionalidad Dudas
def data_elab_lmulti(numero):
    data={
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "video",
        "video": {
            "link": "https://bot-grupo-mascleaning.onrender.com/static/video-lmulti.mp4",
            "caption": "Video elaboración Limpiador Multiusos."
        }
    }
    return data
#Elabora suavizante
def data_elab_suaviza(numero):
    data={
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "image",
        "image": {
            "link": "https://bot-grupo-mascleaning.onrender.com/static/elabora_suavizante.jpg",
            "caption": "Información para elaborar suavizante."
        }
    }
    return data
def data_elab_lavatrastes(numero):
    data={
            "messaging_product": "whatsapp",
            "to": numero,
            "recipient_type": "individual",
            "type": "video",
            "video": {
                "link": "https://bot-grupo-mascleaning.onrender.com/static/video-init2.mp4",
                "caption": "Video elaboración Lavatrastes."
            }
        }
    return data
#Elabora detergente
def data_elab_detergente(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "image",
            "image": {
                "link": "https://bot-grupo-mascleaning.onrender.com/static/elabora_detergente.jpg",
                "caption": "Información para elaboración detergente."
            }
        }
    return data
# Fin respuesta a botones dfuncionalidad Dudas
#busca_proveedor no se usara más
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
def data_dudas_elabora_mc(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "template",
            "template": {
                "name": "dudas_elabora_mc",
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
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/Listado_de_Precios_2025.pdf"
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
                                "payload": "clk_deter"
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
                                "payload": "clk_ltrastes"
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
                                "payload": "clksuaviza"
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
                                "payload": "clk_smanos"
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
                                "payload": "clk_lmulti"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "5",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_scapi"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "6",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_auto"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "7",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_otros"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "8",
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": "clk_masc"
                            }
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "9",
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
                                    "link": "https://bot-grupo-mascleaning.onrender.com/static/Listado_de_Precios_2025.pdf"
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
                                "payload": "clkdeliver"
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
                                "payload": "clknewmc"
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
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "image",
                    "image": {
                        "link": "https://bot-grupo-mascleaning.onrender.com/static/img_compra_cotiza.jpg"
                    }
                },
                "body": {
                    "text": "Para hacer un pedido, sigue los pasos de la imagen."
                },
                "footer": {
                    "text": "¿Cómo hacer un pedido?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clklpricess",
                                "title": "Lista de Precios"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clkmc",
                                "title": "Atras"
                            }
                        }
                    ]
                }
            }
        }
    return data
def data_envios(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "image",
                    "image": {
                        "link": "https://bot-grupo-mascleaning.onrender.com/static/img_envios.jpg"
                    }
                },
                "body": {
                    "text": "Da click en la imagen para ver costos de envío."
                },
                "footer": {
                    "text": "Envíos nacionales o locales."
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clkorder",
                                "title": "¿Cómo hacer pedido?"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clklpricess",
                                "title": "Lista de precios"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clknewmc",
                                "title": "Atras"
                            }
                        }
                    ]
                }
            }
        }
    return data
def data_punto_venta(numero):
    data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "video",
                    "video": {
                        "link": "https://bot-grupo-mascleaning.onrender.com/static/video-lmulti.mp4"
                    }
                },
                "body": {
                    "text": "Da click en el boton Punto de Venta para comaprtir información. Si tienes alguna duda o comentario, puedes llamarme en cualquier momento."
                },
                "footer": {
                    "text": "Video de ejemplo, cambiarlo. Cambiar mensaje footer."
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clk_infosell",
                                "title": "Punto de Venta"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clknewmc",
                                "title": "Atras"
                            }
                        }
                    ]
                }
            }
        }
    return data
def data_info_pv(numero):
    data=data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "document",
                    "document": {
                        "link": "https://bot-grupo-mascleaning.onrender.com/static/punto-venta.pdf"
                    }
                },
                "body": {
                    "text": "Documentación básica y pasos a seguir para apertura de Punto de Venta"
                },
                "footer": {
                    "text": "Información punto de venta."
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clkorder",
                                "title": "¿Cómo hacer pedido?"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clknewmc",
                                "title": "Atras"
                            }
                        }
                    ]
                }
            }
        }
    return data
if __name__=='__main__':
    app.run(host='0.0.0.0',port=80,debug=True)