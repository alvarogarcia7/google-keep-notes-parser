#!/usr/bin/env python3
"""
Full End-to-end test for NATS-based training parser pipeline
Tests: publisher -> NATS -> subscriber -> ANTLR parser

This uses a real NATS server via Docker
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path


class NATSPipelineTest:
    """Manage the NATS server and test the complete pipeline."""

    def __init__(self):
        self.nats_container_id = None
        self.subscriber_process = None
        self.output_buffer = []

    async def start_nats_server(self):
        """Start NATS server in Docker."""
        print("🚀 Checking NATS server...")

        try:
            # Check if NATS server is already running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=nats", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.stdout.strip():
                print("✓ NATS server already running")
                self.nats_container_id = result.stdout.strip()
                return True

            # Try to start a new NATS container
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    "nats-test",
                    "-p",
                    "4223:4222",
                    "nats:latest",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.nats_container_id = result.stdout.strip()
                print(f"✓ NATS container started on port 4223: {self.nats_container_id[:12]}")
                await asyncio.sleep(2)  # Wait for server to start
                return True
            else:
                print(f"ℹ Could not start new NATS container: {result.stderr}")
                print("ℹ Attempting to use existing NATS server on port 4222")
                return True  # Continue anyway, existing server may work

        except Exception as e:
            print(f"⚠ Error checking NATS: {e}")
            print("ℹ Continuing with existing NATS server...")
            return True

    async def wait_for_nats(self, max_attempts=30):
        """Wait for NATS server to be ready."""
        import nats

        print("⏳ Waiting for NATS to be ready...")

        for attempt in range(max_attempts):
            try:
                nc = await nats.connect("nats://localhost:4222", connect_timeout=1)
                await nc.close()
                print("✓ NATS server is ready")
                return True
            except Exception:
                await asyncio.sleep(0.5)

        print("✗ NATS server did not respond in time")
        return False

    def start_subscriber(self):
        """Start the NATS subscriber process."""
        print("🔄 Starting NATS subscriber...")

        parser_dir = Path.home() / "repos/training-parser-antlr4"
        subscriber_script = parser_dir / "nats_subscriber.py"

        if not subscriber_script.exists():
            print(f"✗ Subscriber script not found at {subscriber_script}")
            return False

        try:
            self.subscriber_process = subprocess.Popen(
                ["uv", "run", "python3", str(subscriber_script)],
                cwd=str(parser_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            print("✓ Subscriber started (PID: {})".format(self.subscriber_process.pid))
            time.sleep(2)  # Give subscriber time to connect to NATS
            return True
        except Exception as e:
            print(f"✗ Failed to start subscriber: {e}")
            return False

    async def publish_sample(self):
        """Publish sample data."""
        print("📤 Publishing sample data...")

        publisher_script = Path.cwd() / "nats_publisher.py"

        if not publisher_script.exists():
            print(f"✗ Publisher script not found at {publisher_script}")
            return False

        try:
            result = subprocess.run(
                ["uv", "run", "python3", str(publisher_script)],
                cwd=str(Path.cwd()),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                print(f"✗ Publisher failed: {result.stderr}")
                return False

            print("✓ Sample published successfully")
            return True
        except subprocess.TimeoutExpired:
            print("✗ Publisher timed out")
            return False

    async def collect_subscriber_output(self, timeout=5):
        """Collect subscriber output from the running process."""
        print("⏱  Collecting subscriber output...")

        start_time = time.time()
        output = ""

        try:
            while time.time() - start_time < timeout and self.subscriber_process:
                try:
                    line = self.subscriber_process.stdout.readline()
                    if line:
                        output += line
                        print(f"  {line.rstrip()}")
                except Exception:
                    pass

                await asyncio.sleep(0.1)

            return output
        except Exception as e:
            print(f"⚠ Error collecting output: {e}")
            return output

    def cleanup(self):
        """Clean up processes and containers."""
        print("\n🧹 Cleaning up...")

        if self.subscriber_process:
            try:
                self.subscriber_process.terminate()
                self.subscriber_process.wait(timeout=5)
                print("✓ Subscriber terminated")
            except Exception as e:
                print(f"⚠ Error terminating subscriber: {e}")

        if self.nats_container_id:
            try:
                # Only clean up if we started it (nats-test container)
                result = subprocess.run(
                    ["docker", "ps", "-a", "--filter", "name=nats-test", "--format", "{{.ID}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout.strip():
                    subprocess.run(
                        ["docker", "stop", "nats-test"],
                        capture_output=True,
                        timeout=10,
                    )
                    subprocess.run(
                        ["docker", "rm", "nats-test"],
                        capture_output=True,
                        timeout=10,
                    )
                    print("✓ Test NATS container stopped and removed")
                else:
                    print("ℹ Using existing NATS server (not cleaning up)")
            except Exception as e:
                print(f"⚠ Error cleaning up NATS: {e}")


async def run_test():
    """Run the end-to-end test."""
    print("\n" + "=" * 70)
    print("🧪 NATS Training Parser - Full End-to-End Test")
    print("=" * 70 + "\n")

    pipeline = NATSPipelineTest()

    try:
        # Start NATS server
        if not await pipeline.start_nats_server():
            print("\n✗ Test FAILED: Could not start NATS server")
            return False

        # Wait for NATS to be ready
        if not await pipeline.wait_for_nats():
            print("\n✗ Test FAILED: NATS server not ready")
            return False

        # Start subscriber
        if not pipeline.start_subscriber():
            print("\n✗ Test FAILED: Could not start subscriber")
            return False

        # Publish sample
        if not await pipeline.publish_sample():
            print("\n✗ Test FAILED: Could not publish sample")
            return False

        # Collect output
        output = await pipeline.collect_subscriber_output(timeout=5)

        # Verify test
        print("\n" + "=" * 70)
        print("📋 Test Results")
        print("=" * 70)

        # Check for expected markers in output
        required_markers = [
            "Received message from NATS",
            "Parsing with ANTLR Training Grammar",
        ]

        all_found = all(marker in output for marker in required_markers)

        if all_found and (
            "exercises" in output.lower() or "set" in output.lower()
        ):
            print("✅ TEST PASSED")
            print("\n✓ All acceptance criteria met:")
            print("  ✓ Publisher sent data to NATS")
            print("  ✓ Subscriber received message from NATS")
            print("  ✓ ANTLR parser processed training data")
            print("  ✓ Results printed to console")
            return True
        else:
            print("❌ TEST FAILED")
            print("\nExpected output markers not found:")
            for marker in required_markers:
                found = "✓" if marker in output else "✗"
                print(f"  {found} {marker}")
            print("\nFull output captured:")
            print("-" * 70)
            print(output if output else "(no output)")
            return False

    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        return False
    finally:
        pipeline.cleanup()


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)
