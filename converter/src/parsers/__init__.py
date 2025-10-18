"""
Parser package initialization
"""

from .nif_parser import NIFParser, NIFData
from .hkx_parser import HKXParser, HKXData

__all__ = ['NIFParser', 'NIFData', 'HKXParser', 'HKXData']
