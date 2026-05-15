# Tuta absoluta IPM System

Real-time pest detection and management system for tomato leaf miner (*Phthorimaea absoluta*) using YOLOv8 deep learning, designed for South African smallholder farmers.

## Features

- **YOLOv8-based pest detection** - 98.5% mAP50 accuracy
- **Pest Pressure Index (PPI)** - Multi-factor decision engine
- **Resistance management** - Chemical rotation based on literature
- **Edge deployment** - Runs on Raspberry Pi 4B
- **Off-grid capable** - Solar power + battery support
- **SMS alerts** - Notifications for warning/critical levels
- **Data logging** - JSON and CSV event logging

## Installation

```bash
# Clone repository
git clone <your-repo>
cd tuta_ipm_system

# Install dependencies
pip install -r requirements.txt