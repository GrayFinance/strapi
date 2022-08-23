from requests import request
from typing import List
from uuid import uuid4

import aiohttp
import asyncio

class Strapi:

    def __init__(self, url: str = "http://127.0.0.1:1337") -> None:
        self.token = None
        self.url = url

    def auth(self, token: str):
        self.token = token

    def call(self, method: str, path: str, data=None, files=None, batch=True) -> dict or List[dict]:
        if ("/api" in path):
            data = {"data": data}
        headers = {"Authorization": f"Bearer {self.token}"}
        return request(method=method, url=f"{self.url}{path}", files=files, headers=headers, json=data).json().get("data")
    
    async def async_call(self, session: object, **params: dict):         
        result = await session.request(method=params["method"], url=params["url"], headers=params["headers"], json=params["json"])
        return await result.json()
    
    async def batch(self, method: str, path: str = None, data: list = [], headers=None) -> object:
        headers = {"content-type": "application/json", "Authorization": f"Bearer {self.token}"}
        tasks = []
        async with aiohttp.ClientSession() as session:
            for d in data:
                if (type(path) == str):
                    d["path"] = path  
                
                url = self.url + d["path"]
                tasks.append(self.async_call(session, method=method, url=url, headers=headers, json={"data": d}))        
            return await asyncio.gather(*tasks, return_exceptions=True)

    def query(self, query: dict, first=True) -> dict:
        query = self.call("POST", "/graphql", data={"query": query})
        if (first == True):
            query = query[list(query.keys())[0]]["data"]
            if (len(query) == 0):
                return dict()
            elif (len(query) == 1):
                return query[0]
            else:
                return query
        else:
            return query
    
    def create_entity(self, colletion: str, data: dict) -> dict:
        return self.call("POST", f"/api/{colletion}", data=data)

    def get_entity(self, colletion: str, id: str = None) -> dict:
        path = f"/api/{colletion}"
        if (id != None):
            path += f"/{id}"
        return self.call("GET", path)

    def list_entities(self, colletion: str) -> List[dict]:
        return self.call("GET", f"/api/{colletion}")
    
    def update_entity(self, colletion: str, id: str = None, data: dict = {}) -> dict:
        path = f"/api/{colletion}"
        if (id != None):
            path += f"/{id}"
        return self.call("PUT", path, data=data)
    
    def upload_image(self, file: object, filename: str = None) -> dict:
        if (filename == None):
            filename = f'{str(uuid4())}.png'
        return self.call("POST", "/upload", files={'files': (filename, file, 'image', {'uri': ''})})

    def bulk_create_entities(self, colletion: str, data: List[dict]) -> List[dict]:
        return asyncio.run(self.batch("POST", f"/api/{colletion}", data))

    def bulk_update_entities(self, colletion: str, data: List[dict]) -> List[dict]:
        bulk = []
        for d in data:
            if (d.get("id") == None):
                continue
            else:
                id = d["id"]
                del d["id"]
                d["path"] = f"/api/{colletion}/{id}"
                bulk.append(d)
        return asyncio.run(self.batch("PUT", None, bulk))