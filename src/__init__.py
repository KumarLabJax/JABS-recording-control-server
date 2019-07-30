"""
Root of Long-Term Monitoring System Control Service
"""
import os

from src.app import create_app

APP = create_app()

# src directory
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
