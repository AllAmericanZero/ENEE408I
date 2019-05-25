import mes
import playsound
import time

mes.open_service("alex")
messages = []
new_messages = []
while True:
	new_messages = mes.get_messages()
	print(new_messages)
	if any("dead" in x[2].lower() for x in new_messages) or any("fallen" in x[2].lower() for x in new_messages):
		print("Uh oh!")
	if not new_messages:
		with open("in_mes.txt","w") as in_mes:
			for entry in new_messages:
				in_mes.write(entry[1] + " said " + entry[2])
	time.sleep(1)
	new_messages = []