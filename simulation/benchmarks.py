"""
Performance benchmarks for system evaluation
"""

import time
from typing import Dict, List
from dataclasses import dataclass, field

from core.decision_engine import PestPressureIndex
from simulation.scenarios import ALL_SCENARIOS


@dataclass
class BenchmarkResult:
    """Result of a benchmark test"""
    name: str
    iterations: int
    total_time: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput_ops_per_sec: float


class Benchmark:
    """Benchmarking utility for system components"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def benchmark_decision_engine(self, iterations: int = 1000) -> BenchmarkResult:
        """Benchmark decision engine performance"""
        engine = PestPressureIndex()
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            engine.decide(
                pest_count=4,
                temperature=25,
                humidity=60
            )
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)
        
        return BenchmarkResult(
            name="decision_engine",
            iterations=iterations,
            total_time=sum(times),
            avg_time_ms=sum(times) / len(times),
            min_time_ms=min(times),
            max_time_ms=max(times),
            throughput_ops_per_sec=1000 / (sum(times) / len(times)) * 1000
        )
    
    def benchmark_with_scenarios(self, iterations: int = 100) -> Dict:
        """Benchmark decision engine with all scenarios"""
        engine = PestPressureIndex()
        
        scenario_times = {}
        for scenario in ALL_SCENARIOS:
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                engine.decide(
                    scenario.pest_count,
                    scenario.temperature,
                    scenario.humidity
                )
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
            
            scenario_times[scenario.name] = {
                'avg_ms': sum(times) / len(times),
                'min_ms': min(times),
                'max_ms': max(times)
            }
        
        return scenario_times
    
    def print_report(self):
        """Print benchmark report"""
        print("\n" + "=" * 50)
        print("BENCHMARK REPORT")
        print("=" * 50)
        
        for result in self.results:
            print(f"\n📊 {result.name.upper()}")
            print(f"   Iterations: {result.iterations}")
            print(f"   Avg time: {result.avg_time_ms:.3f} ms")
            print(f"   Min time: {result.min_time_ms:.3f} ms")
            print(f"   Max time: {result.max_time_ms:.3f} ms")
            print(f"   Throughput: {result.throughput_ops_per_sec:.0f} ops/sec")


def run_benchmarks():
    """Run all benchmarks and return results"""
    benchmark = Benchmark()
    
    print("Running decision engine benchmarks...")
    result = benchmark.benchmark_decision_engine(iterations=1000)
    benchmark.results.append(result)
    
    print("Running scenario benchmarks...")
    scenario_results = benchmark.benchmark_with_scenarios(iterations=100)
    
    benchmark.print_report()
    
    print("\n📊 SCENARIO BENCHMARKS:")
    for name, metrics in scenario_results.items():
        print(f"   {name}: {metrics['avg_ms']:.3f} ms avg")
    
    return benchmark.results, scenario_results


if __name__ == "__main__":
    run_benchmarks()