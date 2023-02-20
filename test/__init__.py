import os

from dotenv import load_dotenv
import src.pyaemet as pae

load_dotenv()  # take environment variables from .env.

clima = pae.AemetClima(apikey=os.getenv("SECRET_KEY"))
