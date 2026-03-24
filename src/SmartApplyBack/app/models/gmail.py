from pydantic import BaseModel
from typing import Optional
 
 
class GmailMessage(BaseModel):
    """Représente un mail extrait depuis Gmail."""
 
    id:           str
    subject:      Optional[str] = None   
    sender:       Optional[str] = None  
    received_at:  Optional[str] = None   
    body:         Optional[str] = None   
    links:        list[str]     = []     
    label:        Optional[str] = None  