import asyncio
from bleak import BleakScanner, BleakClient
import struct
import time

# 하기전에 pip install bleak

# 우리가 가지고 있는 센서의 정보들
Sensor1 = {
  'sensorId' : 1,
  'sensorAdress' : "FB:89:EB:22:95:84",
  'sensorData': []
}

Sensor2 = {
  'sensorId' : 2,
  'sensorAdress' : "FB:89:EB:22:95:84",
  'sensorData': []
}

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

# 데이터 읽어오기
async def main(address):
    global temp
    global notFound
    devices = await BleakScanner.discover(timeout=20)
    for d in devices:
        if d.address == address:
            await asyncio.sleep(2)
            client = BleakClient(d, timeout=100)
            try:
              print('connect 시도중')
              await client.connect()
              print('connect!')
              while client.is_connected:
                services = client.services
                tempData = {
                  'time': time.strftime('%Y-%m-%d %H:%M'),
                  'data': {}
                }
                for service in services:
                    for characteristic in service.characteristics:
                        # 데이터 읽기 + 저장
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
                                NiclaSenseME[sense]['data'] = values
                for sense in senses:
                  print(sense, NiclaSenseME[sense]['data'])
                Sensor1['sensorData'].append(tempData)
                # 1분에 한번씩 업데이트해줌
                await asyncio.sleep(60)
            except Exception as e:
              print(e)
              print(f'연결이 {temp + 1}번째 끊겼습니다. 총 5번까지 시도합니다.')
              print(Sensor1)
              await client.disconnect()
              return 'disconnect'
    else:
        print(f'{notFound + 1}번째 시도, 장비를 찾을 수 없습니다.')
        return 'cannot Found'


## 여기서부터는 안됐을 때의 로직

# 연결이 끊기면 시도하는 횟수 = temp
temp = 0
# 못찾으면 다시 시도하는 횟수 = notFound
notFound = 0

while (temp < 5 and notFound < 3):
  ans = asyncio.run(main(Sensor1['sensorAdress']))
  print(ans)
  print(temp, notFound)
  # 만약 못 찾았다면
  if ans == 'cannot Found':
    notFound += 1
  elif ans == 'disconnect':
    temp += 1


print(Sensor1)
if temp == 5:
    print('연결이 5번이상 끊겨서 종료합니다.')
else:
    print('3번이상 장비를 찾을 수 없어서 종료합니다.')


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
