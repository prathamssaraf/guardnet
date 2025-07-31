#!/usr/bin/env python3
"""
DNS Client Utilities for E2E Testing
Provides standardized DNS query functionality for all tests
"""

import socket
import struct
import time
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class DNSResponseCode(Enum):
    """DNS response codes"""
    NOERROR = 0    # No error
    FORMERR = 1    # Format error
    SERVFAIL = 2   # Server failure
    NXDOMAIN = 3   # Non-existent domain
    NOTIMP = 4     # Not implemented
    REFUSED = 5    # Query refused

class DNSQueryType(Enum):
    """DNS query types"""
    A = 1      # IPv4 address
    AAAA = 28  # IPv6 address
    CNAME = 5  # Canonical name
    MX = 15    # Mail exchange
    TXT = 16   # Text record

@dataclass
class DNSQueryResult:
    """Result of a DNS query"""
    domain: str
    query_type: str
    status: str  # ALLOWED, BLOCKED, ERROR, TIMEOUT
    response_code: int
    response_time_ms: float
    timestamp: float
    error_message: Optional[str] = None
    ip_addresses: Optional[List[str]] = None
    server_used: Optional[str] = None
    
    @property
    def ip_address(self) -> Optional[str]:
        """Get the first IP address from the response"""
        return self.ip_addresses[0] if self.ip_addresses else None

class DNSClient:
    """DNS client for testing GuardNet services"""
    
    def __init__(self, server: str = "127.0.0.1", port: int = 8053, timeout: float = 5.0):
        self.default_server = server
        self.default_port = port
        self.timeout = timeout
        
    def create_dns_query(self, domain: str, query_type: DNSQueryType = DNSQueryType.A) -> bytes:
        """Create a DNS query packet"""
        transaction_id = random.randint(1, 65535)
        flags = 0x0100  # Standard query with recursion desired
        questions = 1
        answer_rrs = 0
        authority_rrs = 0
        additional_rrs = 0
        
        # DNS header
        header = struct.pack('!HHHHHH', 
                           transaction_id, flags, questions,
                           answer_rrs, authority_rrs, additional_rrs)
        
        # DNS question section
        question = b''
        for part in domain.split('.'):
            if part:  # Handle empty parts
                question += bytes([len(part)]) + part.encode('ascii')
        question += b'\x00'  # End of domain name
        question += struct.pack('!HH', query_type.value, 1)  # Type and Class (IN)
        
        return header + question
    
    def parse_dns_response(self, response: bytes) -> Tuple[int, List[str]]:
        """Parse DNS response and extract response code and IP addresses"""
        if len(response) < 12:
            raise ValueError("DNS response too short")
        
        # Parse header
        header = struct.unpack('!HHHHHH', response[:12])
        transaction_id, flags, questions, answers, authority, additional = header
        
        response_code = flags & 0x000F
        ip_addresses = []
        
        # If we have answers and no error, try to parse IP addresses
        if answers > 0 and response_code == 0:
            # Skip question section first
            offset = 12
            
            # Skip question section
            for _ in range(questions):
                # Skip domain name (compressed or uncompressed)
                while offset < len(response):
                    length_byte = response[offset]
                    if length_byte == 0:
                        offset += 1
                        break
                    elif (length_byte & 0xC0) == 0xC0:  # Compressed name
                        offset += 2
                        break
                    else:
                        offset += 1 + length_byte
                
                # Skip QTYPE and QCLASS
                offset += 4
            
            # Parse answer section
            for _ in range(answers):
                if offset >= len(response):
                    break
                
                # Skip name (may be compressed)
                if offset < len(response) and (response[offset] & 0xC0) == 0xC0:
                    offset += 2  # Compressed name
                else:
                    # Uncompressed name
                    while offset < len(response) and response[offset] != 0:
                        offset += 1 + response[offset]
                    offset += 1  # Skip the zero byte
                
                if offset + 10 > len(response):
                    break
                
                # Parse TYPE, CLASS, TTL, RDLENGTH
                rr_type, rr_class, ttl, rdlength = struct.unpack('!HHIH', response[offset:offset+10])
                offset += 10
                
                # If it's an A record (IPv4), extract the IP
                if rr_type == 1 and rdlength == 4:
                    if offset + 4 <= len(response):
                        ip_bytes = response[offset:offset+4]
                        ip_address = '.'.join(str(b) for b in ip_bytes)
                        ip_addresses.append(ip_address)
                
                offset += rdlength
        
        return response_code, ip_addresses
    
    def query(self, domain: str, 
              server: Optional[str] = None, 
              port: Optional[int] = None,
              query_type: DNSQueryType = DNSQueryType.A,
              timeout: Optional[float] = None) -> DNSQueryResult:
        """Perform a DNS query and return structured result"""
        
        server = server or self.default_server
        port = port or self.default_port
        timeout = timeout or self.timeout
        
        start_time = time.time()
        timestamp = start_time
        
        try:
            # Create query packet
            query_packet = self.create_dns_query(domain, query_type)
            
            # Send query
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            sock.sendto(query_packet, (server, port))
            response, addr = sock.recvfrom(512)
            sock.close()
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Parse response
            response_code, ip_addresses = self.parse_dns_response(response)
            
            # Determine status
            if response_code == DNSResponseCode.NOERROR.value:
                status = "ALLOWED"
            elif response_code == DNSResponseCode.NXDOMAIN.value:
                status = "BLOCKED"
            else:
                status = "ERROR"
            
            return DNSQueryResult(
                domain=domain,
                query_type=query_type.name,
                status=status,
                response_code=response_code,
                response_time_ms=round(response_time_ms, 2),
                timestamp=timestamp,
                ip_addresses=ip_addresses,
                server_used=f"{server}:{port}"
            )
            
        except socket.timeout:
            return DNSQueryResult(
                domain=domain,
                query_type=query_type.name,
                status="TIMEOUT",
                response_code=-1,
                response_time_ms=timeout * 1000,
                timestamp=timestamp,
                error_message="Query timed out",
                server_used=f"{server}:{port}"
            )
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return DNSQueryResult(
                domain=domain,
                query_type=query_type.name,
                status="ERROR",
                response_code=-1,
                response_time_ms=round(response_time_ms, 2),
                timestamp=timestamp,
                error_message=str(e),
                server_used=f"{server}:{port}"
            )
    
    def batch_query(self, domains: List[str], 
                   server: Optional[str] = None,
                   port: Optional[int] = None,
                   query_type: DNSQueryType = DNSQueryType.A) -> List[DNSQueryResult]:
        """Perform multiple DNS queries"""
        results = []
        for domain in domains:
            result = self.query(domain, server, port, query_type)
            results.append(result)
        return results
    
    def benchmark_query(self, domain: str, iterations: int = 10,
                       server: Optional[str] = None,
                       port: Optional[int] = None) -> Dict:
        """Benchmark DNS query performance"""
        results = []
        
        for _ in range(iterations):
            result = self.query(domain, server, port)
            results.append(result)
        
        # Calculate statistics
        response_times = [r.response_time_ms for r in results if r.status != "ERROR"]
        successful_queries = len([r for r in results if r.status in ["ALLOWED", "BLOCKED"]])
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        return {
            'domain': domain,
            'iterations': iterations,
            'successful_queries': successful_queries,
            'success_rate': (successful_queries / iterations) * 100,
            'avg_response_time_ms': round(avg_response_time, 2),
            'min_response_time_ms': round(min_response_time, 2),
            'max_response_time_ms': round(max_response_time, 2),
            'results': results
        }

class DNSTestUtils:
    """Utility functions for DNS testing"""
    
    @staticmethod
    def is_blocked(result: DNSQueryResult) -> bool:
        """Check if a DNS query was blocked"""
        return result.status in ["BLOCKED", "TIMEOUT"]
    
    @staticmethod
    def is_allowed(result: DNSQueryResult) -> bool:
        """Check if a DNS query was allowed"""
        return result.status == "ALLOWED"
    
    @staticmethod
    def calculate_block_rate(results: List[DNSQueryResult]) -> float:
        """Calculate the percentage of blocked queries"""
        if not results:
            return 0.0
        
        blocked_count = len([r for r in results if DNSTestUtils.is_blocked(r)])
        return (blocked_count / len(results)) * 100
    
    @staticmethod
    def calculate_success_rate(results: List[DNSQueryResult]) -> float:
        """Calculate the percentage of successful queries (not errors)"""
        if not results:
            return 0.0
        
        successful_count = len([r for r in results if r.status != "ERROR"])
        return (successful_count / len(results)) * 100
    
    @staticmethod
    def get_average_response_time(results: List[DNSQueryResult]) -> float:
        """Calculate average response time for successful queries"""
        successful_results = [r for r in results if r.status != "ERROR"]
        if not successful_results:
            return 0.0
        
        total_time = sum(r.response_time_ms for r in successful_results)
        return total_time / len(successful_results)
    
    @staticmethod
    def format_results_table(results: List[DNSQueryResult]) -> str:
        """Format DNS query results as a readable table"""
        if not results:
            return "No results to display"
        
        lines = []
        lines.append("DNS Query Results")
        lines.append("=" * 80)
        lines.append(f"{'Domain':<30} {'Status':<10} {'Response Time':<15} {'Server':<20}")
        lines.append("-" * 80)
        
        for result in results:
            lines.append(f"{result.domain:<30} {result.status:<10} {result.response_time_ms:<15.1f} {result.server_used:<20}")
        
        # Summary statistics
        block_rate = DNSTestUtils.calculate_block_rate(results)
        success_rate = DNSTestUtils.calculate_success_rate(results)
        avg_response_time = DNSTestUtils.get_average_response_time(results)
        
        lines.append("-" * 80)
        lines.append(f"Summary: {len(results)} queries, {block_rate:.1f}% blocked, {success_rate:.1f}% success rate, {avg_response_time:.1f}ms avg response")
        
        return "\n".join(lines)