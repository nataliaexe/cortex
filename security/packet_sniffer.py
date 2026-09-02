#!/usr/bin/env python3
"""
Gênesis Córtex - Packet Sniffer
Análise de pacotes de rede (modo promíscuo)
"""

import logging
import socket
import struct
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import threading


class PacketSniffer:
    """Sniffer de pacotes de rede"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.is_sniffing = False
        self.sniff_thread = None
        self.packet_callback = None
        self.captured_packets = []
        self.max_packets = 1000
        
    def start_sniffing(self, interface: str = None, callback: Optional[Callable] = None) -> bool:
        """Inicia captura de pacotes"""
        if self.is_sniffing:
            self.logger.warning("Sniffer já está ativo")
            return False
            
        self.is_sniffing = True
        self.packet_callback = callback
        self.interface = interface
        
        self.sniff_thread = threading.Thread(target=self._sniff_loop, daemon=True)
        self.sniff_thread.start()
        
        self.logger.info(f"Packet sniffer iniciado na interface {interface or 'padrão'}")
        return True
        
    def stop_sniffing(self):
        """Para captura de pacotes"""
        self.is_sniffing = False
        
        if self.sniff_thread:
            self.sniff_thread.join(timeout=2)
            
        self.logger.info("Packet sniffer parado")
        
    def _sniff_loop(self):
        """Loop de captura de pacotes"""
        try:
            # Cria socket raw
            self.sniffer_socket = socket.socket(
                socket.AF_PACKET, 
                socket.SOCK_RAW, 
                socket.htons(0x0003)
            )
            
            while self.is_sniffing:
                try:
                    # Captura pacote
                    raw_packet, _ = self.sniffer_socket.recvfrom(65535)
                    
                    # Processa pacote
                    packet_info = self._parse_packet(raw_packet)
                    
                    # Adiciona à lista
                    self.captured_packets.append(packet_info)
                    
                    # Limita tamanho da lista
                    if len(self.captured_packets) > self.max_packets:
                        self.captured_packets.pop(0)
                        
                    # Chama callback se definido
                    if self.packet_callback:
                        self.packet_callback(packet_info)
                        
                except Exception as e:
                    self.logger.error(f"Erro ao capturar pacote: {e}")
                    break
                    
        except PermissionError:
            self.logger.error("Permissão negada. Execute como root ou com sudo")
        except Exception as e:
            self.logger.error(f"Erro ao criar socket: {e}")
        finally:
            if hasattr(self, 'sniffer_socket'):
                self.sniffer_socket.close()
                
    def _parse_packet(self, raw_packet: bytes) -> Dict[str, Any]:
        """Parseia pacote bruto"""
        packet_info = {
            "timestamp": datetime.now().isoformat(),
            "length": len(raw_packet),
            "protocols": []
        }
        
        try:
            # Ethernet header (14 bytes)
            eth_header = raw_packet[:14]
            eth_protocol = struct.unpack('!H', eth_header[12:14])[0]
            
            # Endereços MAC
            packet_info["src_mac"] = self._format_mac(eth_header[0:6])
            packet_info["dst_mac"] = self._format_mac(eth_header[6:12])
            
            # IP packet (20 bytes)
            if eth_protocol == 8:  # IPv4
                ip_header = raw_packet[14:34]
                packet_info["protocols"].append("IPv4")
                
                # Parse IP header
                version_ihl = ip_header[0]
                version = version_ihl >> 4
                ihl = version_ihl & 0xF
                
                protocol = ip_header[9]
                src_ip = socket.inet_ntoa(ip_header[12:16])
                dst_ip = socket.inet_ntoa(ip_header[16:20])
                
                packet_info["src_ip"] = src_ip
                packet_info["dst_ip"] = dst_ip
                packet_info["protocol"] = protocol
                
                # TCP/UDP
                if protocol == 6:  # TCP
                    packet_info["protocols"].append("TCP")
                    tcp_header = raw_packet[14 + (ihl * 4):14 + (ihl * 4) + 20]
                    src_port = struct.unpack('!H', tcp_header[0:2])[0]
                    dst_port = struct.unpack('!H', tcp_header[2:4])[0]
                    
                    packet_info["src_port"] = src_port
                    packet_info["dst_port"] = dst_port
                    
                elif protocol == 17:  # UDP
                    packet_info["protocols"].append("UDP")
                    udp_header = raw_packet[14 + (ihl * 4):14 + (ihl * 4) + 8]
                    src_port = struct.unpack('!H', udp_header[0:2])[0]
                    dst_port = struct.unpack('!H', udp_header[2:4])[0]
                    
                    packet_info["src_port"] = src_port
                    packet_info["dst_port"] = dst_port
                    
                elif protocol == 1:  # ICMP
                    packet_info["protocols"].append("ICMP")
                    
            elif eth_protocol == 0x86DD:  # IPv6
                packet_info["protocols"].append("IPv6")
                
        except Exception as e:
            self.logger.warning(f"Erro ao parsear pacote: {e}")
            packet_info["parse_error"] = str(e)
            
        return packet_info
        
    def _format_mac(self, mac_bytes: bytes) -> str:
        """Formata endereço MAC"""
        return ":".join(f"{byte:02x}" for byte in mac_bytes)
        
    def get_captured_packets(self) -> List[Dict[str, Any]]:
        """Retorna pacotes capturados"""
        return self.captured_packets.copy()
        
    def clear_captured_packets(self):
        """Limpa lista de pacotes capturados"""
        self.captured_packets.clear()
        
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas da captura"""
        if not self.captured_packets:
            return {"total": 0}
            
        protocols = {}
        src_ips = {}
        dst_ips = {}
        
        for packet in self.captured_packets:
            # Conta protocolos
            for protocol in packet.get("protocols", []):
                protocols[protocol] = protocols.get(protocol, 0) + 1
                
            # Conta IPs de origem
            if "src_ip" in packet:
                src_ips[packet["src_ip"]] = src_ips.get(packet["src_ip"], 0) + 1
                
            # Conta IPs de destino
            if "dst_ip" in packet:
                dst_ips[packet["dst_ip"]] = dst_ips.get(packet["dst_ip"], 0) + 1
                
        return {
            "total": len(self.captured_packets),
            "protocols": protocols,
            "top_src_ips": sorted(src_ips.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_dst_ips": sorted(dst_ips.items(), key=lambda x: x[1], reverse=True)[:10],
            "is_sniffing": self.is_sniffing
        }
        
    def filter_packets(self, protocol: str = None, src_ip: str = None, dst_ip: str = None) -> List[Dict[str, Any]]:
        """Filtra pacotes capturados"""
        filtered = self.captured_packets
        
        if protocol:
            filtered = [p for p in filtered if protocol in p.get("protocols", [])]
            
        if src_ip:
            filtered = [p for p in filtered if p.get("src_ip") == src_ip]
            
        if dst_ip:
            filtered = [p for p in filtered if p.get("dst_ip") == dst_ip]
            
        return filtered
        
    def export_packets(self, format: str = "json") -> str:
        """Exporta pacotes capturados"""
        if format == "json":
            return json.dumps(self.captured_packets, indent=2)
        else:
            raise ValueError(f"Formato {format} não suportado")