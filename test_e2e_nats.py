#!/usr/bin/env python3
"""
End-to-end test for NATS-based training parser pipeline
Tests: publisher -> NATS -> subscriber -> ANTLR parser
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path


class NATSPipeline:
    """Manage the NATS server and test the pipeline."""

    def __init__(self):
        self.nats_process = None
        self.subscriber_process = None

    async def start_nats_server(self):
        """Start NATS server in Docker."""
        print("🚀 Starting NATS server...")

        # Check if NATS server is already running
        try:
            import nats

            nc = await nats.connect("nats://localhost:4222", connect_timeout=1)
            await nc.close()
            print("✓ NATS server already running")
            return
        except Exception:
            pass

        # Try to start NATS with Docker
        try:
            self.nats_process = subprocess.Popen(
                ["docker", "run", "--rm", "-p", "4222:4222", "nats:latest"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("✓ NATS server started in Docker")
            await asyncio.sleep(2)  # Wait for server to start
        except Exception as e:
            print(f"⚠ Warning: Could not start NATS in Docker: {e}")
            print("Assuming NATS server is running elsewhere...")

    async def wait_for_nats(self, max_attempts=30):
        """Wait for NATS server to be ready."""
        import nats

        for attempt in range(max_attempts):
            try:
                nc = await nats.connect("nats://localhost:4222", connect_timeout=1)
                await nc.close()
                print("✓ NATS server is ready")
                return True
            except Exception:
                await asyncio.sleep(0.5)

        print("✗ NATS server did not start in time")
        return False

    def start_subscriber(self):
        """Start the NATS subscriber process."""
        print("🔄 Starting NATS subscriber...")

        parser_dir = Path.home() / "repos/training-parser-antlr4"
        subscriber_script = parser_dir / "nats_subscriber.py"

        if not subscriber_script.exists():
            print(f"✗ Subscriber script not found at {subscriber_script}")
            return False

        self.subscriber_process = subprocess.Popen(
            [sys.executable, str(subscriber_script)],
            cwd=str(parser_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        print("✓ Subscriber started")
        time.sleep(1)  # Give subscriber time to connect
        return True

    async def publish_sample(self):
        """Publish sample data."""
        print("📤 Publishing sample data...")

        publisher_script = Path(__file__).parent / "nats_publisher.py"

        if not publisher_script.exists():
            print(f"✗ Publisher script not found at {publisher_script}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(publisher_script)],
                cwd=str(Path(__file__).parent),
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

    async def collect_output(self, timeout=5):
        """Collect subscriber output."""
        print("⏱  Waiting for subscriber output...")

        try:
            output_lines = []
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self.subscriber_process and self.subscriber_process.stdout:
                    line = self.subscriber_process.stdout.readline()
                    if line:
                        output_lines.append(line.rstrip())
                await asyncio.sleep(0.1)

            return "\n".join(output_lines)
        except Exception as e:
            print(f"Error collecting output: {e}")
            return ""

    def cleanup(self):
        """Clean up processes."""
        print("\n🧹 Cleaning up...")

        if self.subscriber_process:
            try:
                self.subscriber_process.terminate()
                self.subscriber_process.wait(timeout=5)
                print("✓ Subscriber terminated")
            except Exception as e:
                print(f"⚠ Error terminating subscriber: {e}")

        if self.nats_process:
            try:
                self.nats_process.terminate()
                self.nats_process.wait(timeout=5)
                print("✓ NATS server terminated")
            except Exception as e:
                print(f"⚠ Error terminating NATS: {e}")


async def run_test():
    """Run the end-to-end test."""
    print("\n" + "=" * 70)
    print("🧪 NATS Training Parser End-to-End Test")
    print("=" * 70 + "\n")

    pipeline = NATSPipeline()

    try:
        # Start NATS server
        await pipeline.start_nats_server()
        if not await pipeline.wait_for_nats():
            print("\n✗ Test FAILED: Could not connect to NATS server")
            return False

        # Start subscriber
        if not pipeline.start_subscriber():
            print("\n✗ Test FAILED: Could not start subscriber")
            return False

        # Give subscriber time to connect
        await asyncio.sleep(1)

        # Publish sample
        if not await pipeline.publish_sample():
            print("\n✗ Test FAILED: Could not publish sample")
            return False

        # Collect and display output
        output = await pipeline.collect_output(timeout=3)

        # Verify test
        print("\n" + "=" * 70)
        print("📋 Test Results")
        print("=" * 70)

        success = all(
            marker in output
            for marker in [
                "Received message from NATS",
                "Parsing with ANTLR Training Grammar",
                "exercises",
            ]
        )

        if success:
            print("✅ TEST PASSED")
            print("\n✓ Publisher successfully sent data to NATS")
            print("✓ Subscriber received and parsed the message")
            print("✓ ANTLR parser processed the training data")
            print("\n📊 Sample output:")
            print("-" * 70)
            if output:
                print(output[-2000:] if len(output) > 2000 else output)
            return True
        else:
            print("❌ TEST FAILED")
            print("\nExpected output markers not found")
            print("\nFull output:")
            print("-" * 70)
            print(output if output else "(no output captured)")
            return False

    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        return False
    finally:
        pipeline.cleanup()


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)
