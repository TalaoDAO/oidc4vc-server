from os import path, getcwd
import requests
import shutil
from sys import getsizeof
import time
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
    logo = 'Frame_QRCode.png'
    logo = Image.open(getcwd() + '/static/img/'  + logo)
    logo.convert("RGB")

    #merge both png to get the final result and saves it
    Blend = Image.blend(QRCode_generated,logo,0.5)
    enhancer = ImageEnhance.Contrast(Blend)
    Blend_Enhanced = enhancer.enhance(3)
    Blend_Enhanced.save(mode.uploads_path  + 'External_CV_QRCode.png')
