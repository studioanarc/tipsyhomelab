#!/usr/bin/env python3
"""
Simulate iSpindel and bubble sensor data for testing.
Publishes realistic fermentation data to MQTT broker.
"""

import json
import os
import random
import time
from datetime import datetime
from typing import Dict

import paho.mqtt.client as mqtt


class SensorSimulator:
    """Simulates wine fermentation sensors."""

    def __init__(self, broker: str = "localhost", port: int = 1883):
        """Initialize sensor simulator."""
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.connected = False

        # Fermentation state
        self.fermentation_day = 0
        self.current_gravity = 1.085
        self.target_gravity = 1.010

        # iSpindel state
        self.ispindel_battery = 4.1
        self.ispindel_angle = 25.0

        # Bubble sensor state
        self.bubble_count = 0

    def on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {self.broker}:{self.port}")
            self.connected = True
        else:
            print(f"✗ Connection failed with code {rc}")

    def connect(self):
        """Connect to MQTT broker."""
        self.client.on_connect = self.on_connect
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            if not self.connected:
                raise ConnectionError("Failed to connect to MQTT broker")
        except Exception as e:
            print(f"✗ Error connecting to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        print("Disconnected from MQTT broker")

    def calculate_fermentation_state(self) -> Dict:
        """Calculate realistic fermentation state based on day."""
        # Fermentation phases:
        # Day 0-1: Lag phase (slow start)
        # Day 1-3: Exponential phase (rapid fermentation)
        # Day 3-10: Stationary phase (slowing down)
        # Day 10+: Finishing (almost done)

        if self.fermentation_day < 1:
            # Lag phase
            gravity_drop = 0.002 * self.fermentation_day
            bubble_rate = random.randint(0, 10)
            temperature = 20.0 + random.uniform(-0.5, 0.5)
        elif self.fermentation_day < 3:
            # Exponential phase
            gravity_drop = 0.002 + 0.015 * (self.fermentation_day - 1)
            bubble_rate = random.randint(50, 80)
            temperature = 21.0 + random.uniform(-1.0, 1.0)
        elif self.fermentation_day < 10:
            # Stationary phase
            progress = (self.fermentation_day - 3) / 7
            gravity_drop = 0.032 + 0.040 * progress
            bubble_rate = int(70 * (1 - progress))
            temperature = 20.5 + random.uniform(-0.5, 0.5)
        else:
            # Finishing
            gravity_drop = 0.072 + min(0.003 * (self.fermentation_day - 10), 0.005)
            bubble_rate = random.randint(0, 5)
            temperature = 20.0 + random.uniform(-0.3, 0.3)

        current_gravity = max(self.target_gravity, 1.085 - gravity_drop)
        self.current_gravity = current_gravity

        return {
            "gravity": current_gravity,
            "temperature": temperature,
            "bubble_rate": bubble_rate,
        }

    def generate_ispindel_message(self) -> Dict:
        """Generate realistic iSpindel message."""
        state = self.calculate_fermentation_state()

        # Calculate angle from gravity (inverse relationship)
        # As gravity decreases, angle increases
        gravity_range = 1.085 - 1.010
        current_drop = 1.085 - state["gravity"]
        angle_progress = current_drop / gravity_range
        self.ispindel_angle = 25.0 + (65.0 - 25.0) * angle_progress

        # Battery slowly drains
        self.ispindel_battery = max(3.5, 4.1 - 0.02 * self.fermentation_day)

        message = {
            "name": "iSpindel001",
            "ID": "12345678",
            "token": "test_token",
            "angle": round(self.ispindel_angle + random.uniform(-1, 1), 2),
            "temperature": round(state["temperature"], 2),
            "temp_units": "C",
            "battery": round(self.ispindel_battery, 2),
            "gravity": round(state["gravity"], 3),
            "interval": 900,
            "RSSI": random.randint(-75, -45),
        }

        return message

    def generate_bubble_sensor_message(self) -> Dict:
        """Generate realistic bubble sensor message."""
        state = self.calculate_fermentation_state()

        # Bubble count in last 60 seconds
        bubble_count = state["bubble_rate"] + random.randint(-5, 5)
        bubble_count = max(0, bubble_count)

        message = {
            "sensor_id": "bubble_001",
            "timestamp": datetime.now().isoformat() + "Z",
            "bubble_count": bubble_count,
            "interval_seconds": 60,
            "bubble_rate_per_minute": float(bubble_count),
            "battery_percent": max(75, 100 - 2 * self.fermentation_day),
            "signal_strength": random.randint(-70, -50),
        }

        return message

    def publish_ispindel(self):
        """Publish iSpindel data."""
        topic = "ispindel/iSpindel001"
        message = self.generate_ispindel_message()
        payload = json.dumps(message)

        result = self.client.publish(topic, payload, qos=0, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"→ iSpindel: Gravity={message['gravity']:.3f}, "
                  f"Temp={message['temperature']}°C, "
                  f"Angle={message['angle']}°")
        else:
            print(f"✗ Failed to publish iSpindel data: {result.rc}")

    def publish_bubble_sensor(self):
        """Publish bubble sensor data."""
        topic = "bubble/bubble_001"
        message = self.generate_bubble_sensor_message()
        payload = json.dumps(message)

        result = self.client.publish(topic, payload, qos=0, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"→ Bubble: Rate={message['bubble_rate_per_minute']:.0f}/min")
        else:
            print(f"✗ Failed to publish bubble sensor data: {result.rc}")

    def run_simulation(self, duration_days: int = 14, interval_seconds: int = 60):
        """Run sensor simulation."""
        print(f"\n{'='*60}")
        print("Wine Fermentation Sensor Simulator")
        print(f"{'='*60}")
        print(f"Simulating {duration_days} days of fermentation")
        print(f"Publishing every {interval_seconds} seconds")
        print(f"Target: {self.target_gravity:.3f} SG")
        print(f"{'='*60}\n")

        try:
            self.connect()
            time.sleep(2)

            iterations = 0
            max_iterations = duration_days * 24 * 60 * 60 // interval_seconds

            while iterations < max_iterations:
                # Update fermentation day (each iteration = interval_seconds)
                self.fermentation_day = iterations * interval_seconds / (24 * 60 * 60)

                print(f"\nDay {self.fermentation_day:.2f}")

                # Publish sensor data
                self.publish_ispindel()
                self.publish_bubble_sensor()

                # Check if fermentation is complete
                if self.current_gravity <= self.target_gravity:
                    print(f"\n{'='*60}")
                    print("✓ Fermentation complete!")
                    print(f"Final Gravity: {self.current_gravity:.3f} SG")
                    print(f"Days elapsed: {self.fermentation_day:.1f}")
                    print(f"{'='*60}\n")
                    break

                time.sleep(interval_seconds)
                iterations += 1

        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user")
        except Exception as e:
            print(f"\n✗ Error during simulation: {e}")
        finally:
            self.disconnect()


def main():
    """Main entry point."""
    # Get configuration from environment
    broker = os.getenv("MQTT_BROKER", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    duration_days = int(os.getenv("SIMULATION_DAYS", "14"))
    interval = int(os.getenv("SIMULATION_INTERVAL", "60"))

    simulator = SensorSimulator(broker=broker, port=port)
    simulator.run_simulation(duration_days=duration_days, interval_seconds=interval)


if __name__ == "__main__":
    main()
