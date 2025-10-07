#!/usr/bin/env python3
"""
Test Smart V6 RIG Generator with MetaFFI repository.

This test validates the smart V6 approach with a large, complex repository:
- Smart phase selection for complex repositories
- Context isolation for large codebases
- Tool efficiency with many components
- Adaptive approach based on repository complexity
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from llm0.v6.llm0_rig_generator_v6_smart import LLMRIGGeneratorV6Smart

async def test_v6_smart_metaffi():
    """Test Smart V6 with MetaFFI repository."""
    print("🔍 Testing Smart V6 RIG Generator with MetaFFI")
    
    # Setup
    repository_path = Path("C:/src/github.com/MetaFFI")
    model_settings = {
        "temperature": 0,
        "max_tool_calls": 200,
        "request_limit": 500
    }
    
    # Create smart V6 generator
    generator = LLMRIGGeneratorV6Smart(repository_path, model_settings)
    
    try:
        # Generate RIG with smart adaptation
        print("🚀 Starting Smart V6 RIG generation for MetaFFI...")
        phase_results = await generator.generate_rig()
        
        # Get results
        rig_summary = generator.get_rig_summary()
        adaptation_info = generator.get_adaptation_info()
        
        print(f"✅ Smart V6 completed successfully!")
        print(f"📊 Executed phases: {rig_summary['executed_phases']}")
        print(f"📈 Total phases: {rig_summary['total_phases']}")
        print(f"🧠 Smart adaptation ratio: {adaptation_info['adaptation_ratio']:.2%}")
        
        # Validate results
        if rig_summary['total_phases'] > 0:
            print(f"✅ Smart V6 generated {rig_summary['total_phases']} phase results")
            print(f"🎯 Final result: {rig_summary['final_result']}")
            return True
        else:
            print("❌ No phases executed")
            return False
            
    except Exception as e:
        print(f"❌ Smart V6 failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_v6_smart_metaffi())
    if success:
        print("🎉 Smart V6 MetaFFI test passed!")
    else:
        print("💥 Smart V6 MetaFFI test failed!")
        sys.exit(1)
