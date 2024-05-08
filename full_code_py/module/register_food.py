import asyncio

async def register_QR_food(bt_address, food_name):
	await asyncio.sleep(10)
	data = {}
	data['name'] = food_name
	data['ftypeId'] = 1
	data['qrId'] = bt_address
	
	# print(f'QR {containerId} registered!!.... {data}')
	return data
async def register_OCR_food(validate_time, food_name):
	await asyncio.sleep(10)
	data = {}
	data['name'] = food_name
	data['ftypeId'] = 2
	data['expirationDate'] = validate_time
	# print(f'OCR registered!!.... {data}')
	return data
async def register_GENERAL_food(food_name):
	await asyncio.sleep(10)
	data = {}
	data['name'] = food_name
	data['ftypeId'] = 3
	# print(f'GENERAL registered!!.... {data}')
	return data
