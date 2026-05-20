from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from bson import ObjectId

class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    google_id: str                    # "sub" Google — clé unique
    email: str
    name: str
    picture: Optional[str] = None     # avatar Google
    access_token: str
    refresh_token: str
    token_expiry: datetime
    scopes: list[str] = []            # scopes accordés par l'user
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True       # accepte _id et id
        arbitrary_types_allowed = True