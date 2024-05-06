import asyncio
import json

async def handle_echo(reader, writer):
	while True:
		data = await reader.read(100)
		message = json.loads(data.decode('utf-8'))
		addr = writer.get_extra_info('peername')

		print(f"Received {message} from {addr}")

		"""
			print("Send: %s" % message)
			writer.write(data)
			await writer.drain()

			print("Close the connection")
			writer.close()
		"""

async def main():
	server = await asyncio.start_server(
		handle_echo, '127.0.0.1', 56000)

	async with server:
		await server.serve_forever()

if __name__ == "__main__":
	# load .env

	asyncio.run(main())
	
