import asyncio
from bleak import BleakScanner, BleakClient
import struct
import time
import logging
import os

from multiprocessing import Process, Manager, log_to_stderr, get_logger

def setup_logger():
    # 로그 레벨 설정
    logger = log_to_stderr()
    logger.setLevel(logging.INFO)
    # 로그 포맷 설정
    formatter = logging.Formatter('[%(levelname)s/%(processName)s] %(message)s')
    # 로그를 파일에 출력하기 위한 핸들러 설정
    file_handler = logging.FileHandler('multiprocessing_logs.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# 하기전에 pip install bleak

# 우리가 가지고 있는 센서의 정보들
Sensor1 = {
  'sensorId' : 1,
  'sensorAdress' : "FB:89:EB:22:95:84",
  'sensorData': []
}

Sensor2 = {
  'sensorId' : 2,
  'sensorAdress' : "45:B0:12:20:C1:71",
  'sensorData': []
}

sensor_list = [Sensor1['sensorAdress'], Sensor2['sensorAdress']]

# NiclaSenseME 정보
NiclaSenseME = {
    'temperature':
    {
      'uuid': '19b10000-2001-537e-4f6c-d104768a1214',
      'structure': ['Float32'],
      'data': []
    },
    'humidity':
    {
      'uuid': '19b10000-3001-537e-4f6c-d104768a1214',
      'structure': ['Uint8'],
      'data': []
    },
    'pressure':
    {
      'uuid': '19b10000-4001-537e-4f6c-d104768a1214',
      'structure': ['Float32'],
      'data': []
    },
    'co2':
    {
      'uuid': '19b10000-9002-537e-4f6c-d104768a1214',
      'structure': ['Uint32'],
      'data': []
    },
    'gas':
    {
      'uuid': '19b10000-9003-537e-4f6c-d104768a1214',
      'structure': ['Uint32'],
      'data': []
    },
    'nh3':
    {
      'uuid': '19b10000-9004-537e-4f6c-d104768a1214',
      'structure': ['Uint32'],
      'data': []
    },
  }

# 데이터 유형 매핑
typeMap = {
    "Uint8": {'type' : 'B', 'size': 1},
    "Uint16": {'type' : 'H', 'size': 2},
    "Uint32": {'type' : 'I', 'size': 4},
    "Int16": {'type' : 'h', 'size': 2},
    "Float32": {'type' : 'f', 'size': 4}
}

senses = NiclaSenseME.keys()

###########################################################################################
async def bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address, time):
	await asyncio.sleep(time)
	bluetooth_connect_task_queue.put(bt_address)


# 데이터 읽어오기


async def bluetooth_connect(bt_address):
    logger = get_logger()
    logger.info(f"{bt_address} function in")

    failed = 0
    while True:
        if failed>3:
            return False
        try:
            async with BleakClient(bt_address) as client:
                if await client.is_connected():
                    print(f"Connected to {bt_address}")
                    services = client.services
                    tempData = {
                        'time': time.strftime('%Y-%m-%d %H:%M'),
                        'data': {}
                    }
                    for service in services:
                        for characteristic in service.characteristics:
                            for sense in senses:
                                if characteristic.uuid == NiclaSenseME[sense]['uuid']:
                                    if 'read' in characteristic.properties:
                                        read_data = await client.read_gatt_char(characteristic)
                                        data_types = NiclaSenseME[sense]['structure']
                                        values = []
                                        offset = 0
                                        for data_type in data_types:
                                            value, = struct.unpack_from(typeMap[data_type]['type'], read_data)
                                            values.append(value)
                                            offset += typeMap[data_type]['size']
                                        tempData['data'][sense] = values[0]
                    logger.info(f'{bt_address}: {tempData}')

                    # await sensor_data_buffer.append_data(bt_address, tempData)
                    # await sensor_data_buffer.update_file()
                    return True
        except Exception as e:
            print(e)
            failed += 1





async def bluetooth_process_worker(bluetooth_connect_task_queue):
    logger = get_logger()
    logger.info("worker in")
    while True:
        if bluetooth_connect_task_queue.empty():
            await asyncio.sleep(10)
        # not empty
        bt_address = bluetooth_connect_task_queue.get()
        result = await bluetooth_connect(bt_address)
        if result:
            asyncio.create_task(bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address, 10))
        else:
            asyncio.create_task(bluetooth_job_re_queue_in(bluetooth_connect_task_queue, bt_address, 5))
    


def bluetooth_process(bluetooth_connect_task_queue):
    logger = get_logger()
    logger.info("process in")
    asyncio.run(bluetooth_process_worker(bluetooth_connect_task_queue))
       

def bluetooth_process_wrapper(bluetooth_connect_task_queue):
    logger = get_logger()
    logger.info("wrapper in")
    p = Process(target=bluetooth_process, args=(bluetooth_connect_task_queue,))
    p.start()
    p.join()

async def main():
    setup_logger()

    with Manager() as manager:
        bluetooth_connect_task_queue = manager.Queue()
        bluetooth_connect_task_queue.put(sensor_list[0])
        bluetooth_connect_task_queue.put(sensor_list[1])
        bluetooth_process_wrapper(bluetooth_connect_task_queue)

if __name__ == '__main__':
    asyncio.run(main())


'''
현재 로직
중간에 연결이 끊기면 -> 다섯번까지 시도합니다.
아예 기기를 찾을 수 없다면 -> 3번까지 시도합니다.
센서 1번과 2번의 주소만 바꿔서 돌리면 됩니다.

결과값
{
    "sensorId":1,
    "sensorAdress":"FB:89:EB:22:95:84",
    "sensorData":[
      {
          "time":"2024-05-03 14:05",
          "data":{
            "temperature":27.209999084472656,
            "humidity":37,
            "pressure":1004.7959594726562,
            "co2":500,
            "gas":34499,
            "nh3":0
          }
      },
      {
          "time":"2024-05-03 14:07",
          "data":{
            "temperature":30.369998931884766,
            "humidity":32,
            "pressure":1004.7959594726562,
            "co2":500,
            "gas":38633,
            "nh3":0
          }
      },
      {
          "time":"2024-05-03 14:08",
          "data":{
            "temperature":30.17999839782715,
            "humidity":31,
            "pressure":1004.7725830078125,
            "co2":500,
            "gas":39065,
            "nh3":0
          }
      },
      {
          "time":"2024-05-03 14:09",
          "data":{
            "temperature":29.75,
            "humidity":33,
            "pressure":1004.678955078125,
            "co2":500,
            "gas":37226,
            "nh3":0
          }
      },
      {
          "time":"2024-05-03 14:10",
          "data":{
            "temperature":29.75,
            "humidity":33,
            "pressure":1004.694580078125,
            "co2":500,
            "gas":37226,
            "nh3":0
          }
      }
    ]
}
'''
