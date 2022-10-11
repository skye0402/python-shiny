import time
from tokenize import String
from typing import Any
from flask import Flask, request, jsonify
from threading import Thread
import qrcode
from shiny import *
from shiny.types import ImgData

restListener = Flask(__name__)

qrcodeTextStr = ""
checkInTime = time.time()

def timeHasPassed(oldepoch):
    return time.time() - oldepoch >= 8

# === Create a random value ==============
@restListener.route('/qrcode', methods=['POST'])
def receiveYardOrder():
    global qrcodeTextStr
    global checkInTime
    reqBody = request.json
    try:
        qrcodeTextStr = reqBody["licensePlate"]
    except:
        qrcodeTextStr = "Invalid Yard Order #"
    retValue = {
        "received": qrcodeTextStr
    }
    checkInTime = time.time()
    return jsonify(retValue)

def start_flask():
    restListener.run(host="0.0.0.0", port=5000)

thread = Thread(target=start_flask)
# run the rest listener
thread.start()

# === Create the reactive.poll object ===============================

def check_for_change() -> Any:
    global checkInTime
    global qrcodeTextStr
    if timeHasPassed(checkInTime) and qrcodeTextStr != "":
        print("Time passed")
        qrcodeTextStr = ""
    return qrcodeTextStr

@reactive.poll(check_for_change, 2)
def read_qr_code() -> str:
    return qrcodeTextStr

# === Define the Shiny UI and server ===============================

app_ui = ui.page_fluid(
    ui.output_image("qrCodeImage"),
    ui.output_text_verbatim("qrcodeText"),
)

def server(input: Inputs, output: Outputs, session: Session) -> None:
    @output
    @render.text
    def qrcodeText():
        read_qr_code()
        if qrcodeTextStr == "":
            return 'Waiting for check-in.'
        else: 
            return f'"License Plate: {qrcodeTextStr}"'

    @output  
    @render.image()
    async def qrCodeImage() -> ImgData:
        read_qr_code()
        imageName = 'waiting-for-checkin.png'
        if qrcodeTextStr != "":
            img = qrcode.make('https://www.google.com/search?q=' + qrcodeTextStr)
            imageName = 'checkin-qrcode.png'
            img.save(imageName)
        qrImg: ImgData = {"src": str(imageName), "width": "300px"}
        return qrImg
        
app = App(app_ui, server)