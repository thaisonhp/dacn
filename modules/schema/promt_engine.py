from pydantic import BaseModel


class PromtEngine(BaseModel):
    System_prompt : str = None 
    similarity_threshold : float = None 
    
