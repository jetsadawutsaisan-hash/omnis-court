"""
OMNIS-COURT Monte Carlo Executor
รัน Python code ที่ LLM generate ด้วย exec()
"""

import sys
import io
import traceback
from typing import Dict, Any, Optional


class MonteCarloExecutor:
    """รัน Python simulation code ที่ LLM generate"""
    
    def __init__(self, num_iterations: int = 10000, timeout_seconds: int = 300):
        self.num_iterations = num_iterations
        self.timeout_seconds = timeout_seconds
    
    def execute(self, python_code: str) -> Optional[Dict]:
        """
        รัน Python code และดึงผลลัพธ์
        
        Args:
            python_code: โค้ด Python ที่ LLM generate
        
        Returns:
            dict ผลลัพธ์จากการ simulate หรือ None ถ้า error
        """
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_out = io.StringIO()
        sys.stderr = captured_err = io.StringIO()
        
        try:
            # สร้าง namespace สำหรับ exec
            namespace = {
                '__builtins__': __builtins__,
                'result': None,  # โค้ดจะใส่ผลลัพธ์ตรงนี้
            }
            
            # เพิ่ม wrapper function ที่โค้ดควรเรียก
            wrapper_code = f"""
import numpy as np
import json
from collections import Counter
from typing import Dict, List, Tuple
from dataclasses import dataclass

{python_code}

# ========================================
# EXECUTION (เรียกโดย executor)
# ========================================
try:
    # ตรวจสอบว่า match_parameters มีอยู่
    if 'match_parameters' not in dir() and 'match_parameters' not in globals():
        raise NameError("match_parameters not defined in generated code")
    
    params = globals()['match_parameters'] if 'match_parameters' in globals() else match_parameters
    
    # ตั้ง num_iterations
    if 'simulation' in params:
        params['simulation']['num_iterations'] = {self.num_iterations}
    
    # Detect match type และรัน
    match_type = params.get('match_type', 'singles')
    
    if match_type == 'singles':
        player_a = SinglesPlayer(**params['player_a'])
        player_b = SinglesPlayer(**params['player_b'])
        context = MatchContext(**params['match_context'])
        simulator = SinglesMatchSimulator(
            player_a, player_b, context,
            best_of=params['simulation'].get('best_of', 3)
        )
    else:
        # Doubles (ถ้าโค้ด support)
        raise NotImplementedError("Doubles not yet supported in executor")
    
    # รัน simulation
    results = []
    for i in range({self.num_iterations}):
        results.append(simulator.simulate_match())
    
    # Compress results
    if 'compress_raw_data' in globals():
        result = compress_raw_data(results, params)
    else:
        result = {{'N': len(results), 'results_sample': results[:100]}}
    
except Exception as e:
    result = {{'error': str(e), 'traceback': traceback.format_exc()}}
"""
            
            # รันโค้ด
            exec(wrapper_code, namespace)
            
            # ดึงผลลัพธ์
            output = namespace.get('result')
            
            # แสดง stdout/stderr (สำหรับ debug)
            stdout_text = captured_out.getvalue()
            stderr_text = captured_err.getvalue()
            
            if stdout_text:
                print(f"[Monte Carlo stdout]: {stdout_text[:500]}")
            if stderr_text:
                print(f"[Monte Carlo stderr]: {stderr_text[:500]}")
            
            if output is None:
                print("❌ Monte Carlo: No result returned")
                return None
            
            if isinstance(output, dict) and 'error' in output:
                print(f"❌ Monte Carlo error: {output['error']}")
                return None
            
            print(f"✅ Monte Carlo: {output.get('N', 'unknown')} simulations completed")
            return output
            
        except Exception as e:
            print(f"❌ Monte Carlo execution failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
            
        finally:
            # คืนค่า stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
