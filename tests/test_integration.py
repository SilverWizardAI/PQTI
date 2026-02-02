#!/usr/bin/env python3
"""
Integration test for PyQt Instrument.

This script dogfoods the instrumentation by:
1. Launching the simple test app with instrumentation
2. Connecting via IPC client
3. Testing snapshot, click, and type commands
4. Verifying responses
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

# Add parent directory to path to import mcp_server
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.qt_client import QtInstrumentClient


class TestRunner:
    def __init__(self):
        self.app_process = None
        self.client = QtInstrumentClient()

    async def launch_app(self):
        """Launch the simple test app."""
        app_path = Path(__file__).parent.parent / "examples" / "simple_app.py"
        venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python"

        print(f"🚀 Launching test app: {app_path}")
        self.app_process = subprocess.Popen(
            [str(venv_python), str(app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for app to start and instrumentation to be ready
        print("⏳ Waiting for app to initialize...")
        await asyncio.sleep(3)

        if self.app_process.poll() is not None:
            stdout, stderr = self.app_process.communicate()
            print(f"❌ App failed to start!")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False

        print("✅ App launched")
        return True

    async def connect(self):
        """Connect to the instrumented app."""
        print("🔌 Connecting to app via IPC...")
        success = await self.client.connect("qt_instrument")

        if success:
            print("✅ Connected to app")
            return True
        else:
            print("❌ Failed to connect")
            return False

    async def test_ping(self):
        """Test ping command."""
        print("\n📡 Testing ping...")
        result = await self.client.send_request("ping", {})

        if result.get("status") == "ok":
            print("✅ Ping successful")
            return True
        else:
            print(f"❌ Ping failed: {result}")
            return False

    async def test_snapshot(self):
        """Test snapshot command."""
        print("\n📸 Testing snapshot...")
        result = await self.client.send_request("snapshot", {})

        if "type" in result and result["type"] == "SimpleTestApp":
            print("✅ Snapshot successful")
            print(f"   Widget tree root: {result['type']}")
            print(f"   Children count: {len(result.get('children', []))}")

            # Print some widget info
            for child in result.get("children", [])[:3]:
                obj_name = child.get("objectName", "unnamed")
                widget_type = child.get("type")
                print(f"   - {obj_name} ({widget_type})")

            return True
        else:
            print(f"❌ Snapshot failed: {result}")
            return False

    async def test_type(self):
        """Test typing text."""
        print("\n⌨️  Testing type text...")
        result = await self.client.send_request(
            "type", {"ref": "root/text_input", "text": "Hello from test!", "submit": False}
        )

        if result.get("success"):
            print("✅ Type successful")
            return True
        else:
            error = result.get("error", "Unknown error")
            print(f"❌ Type failed: {error}")
            return False

    async def test_click(self):
        """Test clicking a button."""
        print("\n🖱️  Testing click button...")
        result = await self.client.send_request(
            "click", {"ref": "root/copy_button", "button": "left"}
        )

        if result.get("success"):
            print("✅ Click successful")
            return True
        else:
            error = result.get("error", "Unknown error")
            print(f"❌ Click failed: {error}")
            return False

    async def test_counter_click(self):
        """Test clicking counter button multiple times."""
        print("\n🔢 Testing counter button (3 clicks)...")
        for i in range(3):
            result = await self.client.send_request(
                "click", {"ref": "root/counter_button", "button": "left"}
            )
            if result.get("success"):
                print(f"   Click {i+1}/3 ✓")
            else:
                print(f"❌ Counter click {i+1} failed")
                return False

        print("✅ Counter clicks successful")
        return True

    def cleanup(self):
        """Clean up resources."""
        print("\n🧹 Cleaning up...")

        if self.client:
            self.client.disconnect()
            print("   Disconnected from app")

        if self.app_process:
            self.app_process.terminate()
            try:
                self.app_process.wait(timeout=5)
                print("   App terminated")
            except subprocess.TimeoutExpired:
                self.app_process.kill()
                print("   App killed (timeout)")

    async def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("PyQt Instrument - Integration Test")
        print("=" * 60)

        results = []

        # Launch app
        if not await self.launch_app():
            self.cleanup()
            return False

        # Connect
        if not await self.connect():
            self.cleanup()
            return False

        # Run tests
        tests = [
            ("Ping", self.test_ping),
            ("Snapshot", self.test_snapshot),
            ("Type Text", self.test_type),
            ("Click Button", self.test_click),
            ("Counter Clicks", self.test_counter_click),
        ]

        for test_name, test_func in tests:
            try:
                success = await test_func()
                results.append((test_name, success))
            except Exception as e:
                print(f"❌ {test_name} threw exception: {e}")
                results.append((test_name, False))

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")

        print(f"\nResults: {passed}/{total} tests passed")
        print("=" * 60)

        self.cleanup()

        return passed == total


async def main():
    """Main entry point."""
    runner = TestRunner()
    try:
        success = await runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        runner.cleanup()
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        runner.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
