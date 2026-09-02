#!/usr/bin/env python3
"""
Gênesis Córtex - Geolocation
Geolocalização de IPs (usando API offline quando possível)
"""

import logging
import socket
import struct
import ipaddress
from typing import Dict, Any, Optional
from pathlib import Path


class GeoLocation:
    """Geolocalizador de IPs"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.offline_mode = True  # Prioriza modo offline
        
        # Database GeoIP offline (GeoLite2)
        self.geoip_db = Path("data/GeoLite2-City.mmdb")
        
    def lookup_ip(self, ip_address: str) -> Dict[str, Any]:
        """Faz lookup de geolocalização de IP"""
        
        # Valida IP
        if not self._is_valid_ip(ip_address):
            return {"error": "Endereço IP inválido"}
            
        # Tenta lookup offline primeiro
        if self.offline_mode and self.geoip_db.exists():
            return self._offline_lookup(ip_address)
        else:
            return self._online_lookup(ip_address)
            
    def _is_valid_ip(self, ip_address: str) -> bool:
        """Valida formato de endereço IP"""
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            return False
            
    def _offline_lookup(self, ip_address: str) -> Dict[str, Any]:
        """Lookup usando database GeoIP offline"""
        try:
            import geoip2.database
            
            reader = geoip2.database.Reader(str(self.geoip_db))
            
            response = reader.city(ip_address)
            
            return {
                "ip": ip_address,
                "country": response.country.name,
                "country_code": response.country.iso_code,
                "city": response.city.name,
                "latitude": response.location.latitude,
                "longitude": response.location.longitude,
                "timezone": response.location.time_zone,
                "postal_code": response.postal.code,
                "source": "offline"
            }
            
        except ImportError:
            self.logger.warning("geoip2 não instalado, usando fallback online")
            return self._online_lookup(ip_address)
        except Exception as e:
            self.logger.error(f"Erro no lookup offline: {e}")
            return self._online_lookup(ip_address)
            
    def _online_lookup(self, ip_address: str) -> Dict[str, Any]:
        """Lookup usando API online (fallback)"""
        try:
            import requests
            
            # Usa API gratuita (ip-api.com)
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    return {
                        "ip": ip_address,
                        "country": data.get("country"),
                        "country_code": data.get("countryCode"),
                        "city": data.get("city"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "timezone": data.get("timezone"),
                        "isp": data.get("isp"),
                        "source": "online"
                    }
                else:
                    return {"error": data.get("message", "Erro na API")}
            else:
                return {"error": f"API retornou status {response.status_code}"}
                
        except ImportError:
            self.logger.warning("requests não instalado")
            return {"error": "Serviço de geolocalização não disponível"}
        except Exception as e:
            self.logger.error(f"Erro no lookup online: {e}")
            return {"error": f"Erro na consulta: {str(e)}"}
            
    def resolve_hostname(self, hostname: str) -> Optional[str]:
        """Resolve hostname para IP"""
        try:
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except socket.gaierror:
            return None
            
    def reverse_dns(self, ip_address: str) -> Optional[str]:
        """Reverse DNS lookup"""
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            return hostname
        except socket.herror:
            return None
            
    def get_local_ip(self) -> Optional[str]:
        """Obtém IP local"""
        try:
            # Cria socket e conecta a servidor externo
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            self.logger.error(f"Erro ao obter IP local: {e}")
            return None
            
    def check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Verifica reputação de IP (simplificado)"""
        # Implementação básica - na prática usaria APIs específicas
        suspicious_ranges = [
            "10.0.0.0/8",      # Private
            "172.16.0.0/12",   # Private
            "192.168.0.0/16",  # Private
            "127.0.0.0/8"      # Loopback
        ]
        
        return {
            "ip": ip_address,
            "is_private": self._is_private_ip(ip_address),
            "is_loopback": ip_address.startswith("127."),
            "reputation": "unknown"  # Requer API específica
        }
        
    def _is_private_ip(self, ip_address: str) -> bool:
        """Verifica se IP é privado"""
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            return ip_obj.is_private
        except:
            return False