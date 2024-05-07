import asyncio

async def register_QR_food(containerId, food_name, dt):
	await asyncio.sleep(10)
	data = {}
	data['food_type'] = 'QR'
	data['datetime'] = dt
	data['container_id'] = containerId
	data['food_name'] = food_name
	# print(f'QR {containerId} registered!!.... {data}')
	return data
async def register_OCR_food(validate_time, food_name, dt):
	await asyncio.sleep(10)
	data = {}
	data['food_type'] = 'OCR'
	data['datetime'] = dt
	data['validate_time'] = validate_time
	data['food_name'] = food_name
	# print(f'OCR registered!!.... {data}')
	return data
async def register_GENERAL_food(food_name, dt):
	await asyncio.sleep(10)
	data = {}
	data['food_type'] = 'GENERAL'
	data['datetime'] = dt
	data['food_name'] = food_name
	# print(f'GENERAL registered!!.... {data}')
	return data
