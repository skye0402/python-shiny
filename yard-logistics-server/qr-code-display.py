from ast import Bytes
import time
from tokenize import String
from typing import Any
from flask import Flask, request, jsonify
from threading import Thread
import qrcode
from shiny import *
from shiny.types import ImgData
import base64

restListener = Flask(__name__)

qrcodeTextStr = ""
originalImg = None
checkInTime = time.time()

def timeHasPassed(oldepoch):
    return time.time() - oldepoch >= 8

# === Create a random value ==============
@restListener.route('/qrcode', methods=['POST'])
def receiveYardOrder():
    global qrcodeTextStr
    global originalImg
    global checkInTime
    reqBody = request.json
    print(f"{reqBody.keys()=}")
    retValue = {}
    try:
        qrcodeTextStr = reqBody["licensePlate"]
        if "img" in reqBody.keys():
            # read img as base64 and save it as a file
            originalImg = reqBody["img"]
            with open("./original-image.png", "wb") as fh:
                originalImg += "=" * ((4 - len(originalImg) % 4) % 4)
                fh.write(base64.b64decode(originalImg))
            retValue["img"] = originalImg

    except Exception as e:
        import traceback
        traceback.print_exc()
        qrcodeTextStr = "Invalid Yard Order #"
        originalImg = None
    retValue["received"] = qrcodeTextStr
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
    global originalImg
    if timeHasPassed(checkInTime) and qrcodeTextStr != "":
        print("Time passed")
        qrcodeTextStr = ""
        originalImg = None
    return qrcodeTextStr

@reactive.poll(check_for_change, 2)
def read_qr_code() -> str:
    return qrcodeTextStr

# === Define the Shiny UI and server ===============================

app_ui = ui.page_fluid(
    ui.output_image("showOriginalImage"),
    ui.output_image("qrCodeImage"),
    ui.output_text_verbatim("qrcodeText"),
)

def server(input: Inputs, output: Outputs, session: Session) -> None:
    @output
    @render.image()
    async def showOriginalImage() -> ImgData | None:
        read_qr_code()
        global originalImg
        if originalImg is not None:
            import os
            print(f"{os.listdir('./')}")
            imageName = './original-image.png'
            showImg: ImgData = {"src": str(imageName), "width": "200px"}
            return showImg
        else:
            imageName = "waiting-for-checkin.png"
            originalImg = None
            showImg: ImgData = {"src": str(imageName), "width": "200px"}
            return None

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
            # img = qrcode.make('https://www.google.com/search?q=' + qrcodeTextStr)
            img = qrcode.make(qrcodeTextStr)
            imageName = 'checkin-qrcode.png'
            img.save(imageName)
        qrImg: ImgData = {"src": str(imageName), "width": "300px"}
        return qrImg
        
app = App(app_ui, server)