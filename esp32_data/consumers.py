import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from station_meteo.models import StationMeteo
from django.utils import timezone
import asyncio

class ESP32DataConsumer(AsyncWebsocketConsumer):
    # Dictionnaire pour tracker les stations connectées
    connected_stations = {}
    
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Serveur prêt - En attente d\'identification'
        }))

    async def disconnect(self, close_code):
        # Nettoyer la station déconnectée
        for station_id, client_data in self.connected_stations.items():
            if client_data.get('client') == self:
                del self.connected_stations[station_id]
                await self.broadcast_connected_stations()
                break

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'identification':
                await self.handle_identification(data)
            elif all(key in data for key in ['temperature', 'humidite', 'humidite_sol', 'luminosite']):
                await self.handle_sensor_data(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))

    async def handle_identification(self, data):
        """Enregistre la station connectée"""
        station_id = data.get('station_id')
        device_mac = data.get('device_mac')
        
        if station_id:
            # Enregistrer la station comme connectée
            self.connected_stations[station_id] = {
                'client': self,
                'device_mac': device_mac,
                'last_seen': timezone.now(),
                'status': 'connected'
            }
            
            # Vérifier si la station existe en base
            station_exists = await self.check_station_exists(station_id)
            
            if station_exists:
                await self.send(text_data=json.dumps({
                    'type': 'identification_accepted',
                    'station_id': station_id,
                    'message': f'Station {station_id} reconnue et enregistrée'
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'station_not_found',
                    'station_id': station_id,
                    'message': f'Station {station_id} connectée mais non enregistrée dans le CRUD'
                }))
            
            # Diffuser la liste mise à jour à tous les clients
            await self.broadcast_connected_stations()

    async def handle_sensor_data(self, data):
        station_id = data.get('station_id')
        
        # Mettre à jour le last_seen
        if station_id in self.connected_stations:
            self.connected_stations[station_id]['last_seen'] = timezone.now()
        
        # Sauvegarder les données
        await self.save_sensor_data(data)
        
        # Diffuser les données à tous les clients
        await self.broadcast_sensor_data(data)

    async def broadcast_connected_stations(self):
        """Diffuse la liste des stations connectées à tous les clients"""
        connected_list = list(self.connected_stations.keys())
        
        message = {
            'type': 'connected_stations_update',
            'connected_stations': connected_list,
            'count': len(connected_list)
        }
        
        # Envoyer à tous les clients connectés
        for station_data in self.connected_stations.values():
            try:
                await station_data['client'].send(text_data=json.dumps(message))
            except:
                pass

    async def broadcast_sensor_data(self, data):
        """Diffuse les données de capteurs à tous les clients"""
        message = {
            'type': 'sensor_data',
            'data': data,
            'station_id': data.get('station_id'),
            'timestamp': timezone.now().isoformat()
        }
        
        for station_data in self.connected_stations.values():
            try:
                await station_data['client'].send(text_data=json.dumps(message))
            except:
                pass

    @sync_to_async
    def check_station_exists(self, station_id):
        return StationMeteo.objects.filter(id_station=station_id).exists()

    @sync_to_async
    def save_sensor_data(self, data):
        """Sauvegarde les données en base"""
        try:
            station_id = data.get('station_id')
            print(f"💾 Données sauvegardées - {station_id}: "
                  f"Temp:{data.get('temperature')}°C "
                  f"Hum:{data.get('humidite')}% "
                  f"Sol:{data.get('humidite_sol')}% "
                  f"Lux:{data.get('luminosite')}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")