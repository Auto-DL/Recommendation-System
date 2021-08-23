from fastapi import FastAPI
import tensorflow as tf
import numpy as np
from typing import List, Dict

from tensorflow.python.ops.gen_array_ops import reverse

# initializes the FASTAPI app. Do not change var name.
app = FastAPI()

layer_map = {
    "Conv2D": 0,
    "Dense": 1,
    "LSTM": 2,
    "SimpleRNN": 3,
    "Dropout": 4,
    "Flatten": 5,
    "ZeroPadding2D": 6,
    "AveragePooling2D": 7,
    "MaxPooling2D": 8,
}

reverse_layer_map = {v: k for k, v in layer_map.items()}

# path to the model being used.
MODEL_PATH = "../models/linear_classification_model.h5"
# top number of classes to be returned.
TOP_K = 2

model = tf.keras.models.load_model(MODEL_PATH)


@app.post("/predict")
def predict(payload: Dict):
    """
    Take the payload which is json data and returns the 2 most likely classes.
    :example Json data:{ 'layers': List[str] }
    :return: Dict
    For JS purposes it is an object with object 'predictions' which consist of the classes.
    """
    layers = payload["layers"]
    layers = list(map(lambda x: layer_map[x], layers))
    layers = np.array(layers[-3:], dtype=np.float32).reshape(1, -1)
    preds = model.predict(layers)
    top_k = np.argsort(preds[0])[-TOP_K:][::-1]
    response = {
        f"suggestion_{idx+1}": reverse_layer_map[layer]
        for idx, layer in enumerate(top_k)
    }
    return {"predictions": response}
