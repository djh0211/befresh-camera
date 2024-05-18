import asyncio


async def register_QR_food(bt_address, food_name):
	data = {}
	data['name'] = food_name
	data['ftypeId'] = 1
	data['qrId'] = bt_address
	return data
async def register_OCR_food(validate_time, food_name):
	data = {}
	data['name'] = food_name
	data['ftypeId'] = 2
	data['expirationDate'] = validate_time
	return data
async def register_GENERAL_food(food_name):
	data = {}
	data['name'] = food_name
	data['ftypeId'] = 3
	return data
