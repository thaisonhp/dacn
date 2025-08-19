from pydantic import BaseModel


class ModelSetting(BaseModel):
    model_name : str 
    api_key : str 
    temperature : float 
