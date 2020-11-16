import json
import os

def returnJson(jsonFile:str) -> dict:
	if os.path.exists(jsonFile):
		with open(jsonFile, "r") as jsonReader:
			return json.load(jsonReader) ## dict