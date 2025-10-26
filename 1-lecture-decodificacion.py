import asyncio
from bleak import BleakClient
import struct
import json

# Dirección MAC del dispositivo Bluetooth
address = "00:4D:32:16:33:27"  # Reemplaza con la dirección MAC de tu dispositivo
BLOOD_PRESSURE_MEASUREMENT_UUID = "00002a35-0000-1000-8000-00805f9b34fb"  # UUID de la característica de presión arterial

# Diccionario global para almacenar los datos de presión arterial y el arreglo de bits
blood_pressure_data = {
    'raw_data': None,  # Para almacenar el array de bits crudos
    'decoded_data': None  # Para almacenar los datos decodificados
}

# Función para decodificar los datos de presión arterial
def decode_blood_pressure(data):
    flags = data[0]
    unit_is_kPa = (flags & 0x01) != 0

    systolic, diastolic, mean_arterial = struct.unpack('<HHH', data[1:7])
    pulse_position = 7
    pulse_rate = None
    if len(data) > pulse_position:
        pulse_rate = struct.unpack('<H', data[pulse_position:pulse_position+2])[0]

    if unit_is_kPa:
        systolic /= 7.50062
        diastolic /= 7.50062
        mean_arterial /= 7.50062

    output = {
        'Sistólica': round(systolic, 2),
        'Diastólica': round(diastolic, 2),
        'Presión media': round(mean_arterial, 2),
        'Pulso': pulse_rate if pulse_rate else 'No disponible',
        'Unidades': 'kPa' if unit_is_kPa else 'mmHg'
    }
    return output

# Callback para manejar los datos recibidos
def notification_handler(sender, data):
    print(f"Notificación desde {sender}: {data}")
    blood_pressure_data['raw_data'] = data
    blood_pressure_data['decoded_data'] = decode_blood_pressure(data)
    save_data_to_json()
    print("Datos decodificados y guardados:", blood_pressure_data['decoded_data'])

# Función para guardar los datos en un archivo JSON / AHORA SERA EN FIREBASE
def save_data_to_json():
    if blood_pressure_data['decoded_data']:
        try:
            with open("decoded_data.json", "w") as json_file:
                json.dump(blood_pressure_data['decoded_data'], json_file, indent=4)
            print("Datos guardados en 'decoded_data.json'.")
        except Exception as e:
            print(f"Error al guardar los datos en JSON: {e}")
    else:
        print("No hay datos decodificados para guardar.")

# Función principal para leer la presión arterial desde el dispositivo Bluetooth
async def read_blood_pressure(address):
    try:
        async with BleakClient(address) as client:
            if client.is_connected:
                print(f"Conectado al dispositivo {address}")
                await client.start_notify(BLOOD_PRESSURE_MEASUREMENT_UUID, notification_handler)
                print("Esperando notificaciones de presión arterial...")
                await asyncio.sleep(30)
                await client.stop_notify(BLOOD_PRESSURE_MEASUREMENT_UUID)
            else:
                print(f"No se pudo conectar al dispositivo {address}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    asyncio.run(read_blood_pressure(address))