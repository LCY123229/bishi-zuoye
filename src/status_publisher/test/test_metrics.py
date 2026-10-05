from types import SimpleNamespace
from unittest.mock import patch

from status_publisher.metrics import MIB, SystemSampler


def test_metrics_and_cpu_warmup():
    with patch('status_publisher.metrics.psutil') as backend:
        backend.cpu_percent.side_effect = [0.0, 25.5]
        backend.virtual_memory.return_value = SimpleNamespace(
            percent=40.0, total=8192 * MIB, available=4915.2 * MIB,
        )
        backend.net_io_counters.return_value = SimpleNamespace(
            bytes_sent=12 * MIB, bytes_recv=34 * MIB,
        )
        sampler = SystemSampler()
        result = sampler.sample()
        assert result['cpu_percent'] == 25.5
        assert backend.cpu_percent.call_count == 2
        assert result['memory_percent'] == 40.0
        assert result['memory_total'] == 8192.0
        assert result['memory_available'] == 4915.2
        assert result['net_sent'] == 12.0
        assert result['net_recv'] == 34.0
        assert result['hostname']
        backend.net_io_counters.return_value = None
        backend.cpu_percent.side_effect = None
        backend.cpu_percent.return_value = 0.0
        result = sampler.sample()
        assert result['net_sent'] == result['net_recv'] == 0.0


def test_real_host_metrics():
    result = SystemSampler().sample()
    assert 0 <= result['cpu_percent'] <= 100
    assert 0 <= result['memory_percent'] <= 100
    assert 0 <= result['memory_available'] <= result['memory_total']
    assert result['memory_total'] > 0
    assert result['net_recv'] >= 0
    assert result['net_sent'] >= 0
