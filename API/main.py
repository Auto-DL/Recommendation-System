from fastapi import FastAPI
import tensorflow as tf

app = FastAPI()


@app.get("/")
def hello():
    return {"Greeting": "bam"}
