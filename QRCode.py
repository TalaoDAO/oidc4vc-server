import copy
import os.path
from os import path
from flask import Flask, session, send_from_directory, flash
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
import requests
import shutil
from flask_fontawesome import FontAwesome
import json
from sys import getsizeof
import time

# dependances
from protocol import Document, read_profil, Identity, Claim
#import environment
import constante
import ns
import analysis

import qrcode
from PIL import Image, ImageEnhance

def get_QRCode(mode, link):
    #Generate the QRCode linking to teh outside view of the CV and saves it
    outside_CV_view=link
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=8,
    )
    qr.add_data(outside_CV_view)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black",back_color="white")

    #Converts the generated png file to put the logo
    QRCode_generated = img.convert("RGB")

    #Opens the png file with the logo on it to merge them
    logo = 'QmVb4yRynoeSd8YQHCfHYgvfi1td2fquAaSFPnxRMx1ATU'
    if not path.exists(mode.uploads_path  + logo) :
        url = 'https://gateway.pinata.cloud/ipfs/'+ logo
        response = requests.get(url, stream=True)
        with open(mode.uploads_path  + logo, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
            del response
    logo = Image.open(mode.uploads_path  + logo + '.png')
    logo.convert("RGB")

    #merge both png to get the final result and saves it
    Blend = Image.blend(QRCode_generated,logo,0.5)
    enhancer = ImageEnhance.Contrast(Blend)
    Blend_Enhanced = enhancer.enhance(3)
    Blend_Enhanced.save(mode.uploads_path  + 'QRCode_with_Logo.png')
