"""Verify the C044 matrix against the published reference archive, offline."""
import argparse
from bisect import bisect_right
import json
import math
from pathlib import Path
import re
from statistics import mean
from zipfile import ZipFile

GAINS = (4, 8, 16, 32)
PATTERNS = ('up_and_down', 'lift_and_drop', 'sin_sin-90pct', 'sin_time_square', 'brutal')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def verify(path, expected_name, archive):
    trace = json.loads(path.read_text())
    state = json.loads(path.with_name('status.json').read_text())
    name = path.stem
    require(name == expected_name and name in state['completed'], 'unexpected or incomplete pattern')
    p_gain, pattern = name.split('-', 1)
    gain = int(p_gain[1:])
    scale = .9 if pattern == 'sin_sin-90pct' else 1
    spec = state[name]
    require((spec['p'], spec['d'], spec['scale']) == (gain, 32, scale), 'gain or amplitude mismatch')
    source = json.loads(archive.read(spec['member']))
    require(source['mass'] == 0 and source['kp'] == gain and
            source['trajectory'] == pattern.removesuffix('-90pct'), 'reference mismatch')
    ref = source['entries']
    times = [entry['timestamp'] for entry in ref]
    require(trace and trace[0]['timestamp'] < .05 and trace[-1]['timestamp'] >= times[-1] - .05,
            'trace does not cover complete reference timing')
    require(all(0 < b['timestamp'] - a['timestamp'] < .1 for a,b in zip(trace,trace[1:])),
            'trace has non-monotonic timestamps or a gap of 100 ms')
    zero = state['zero_ticks']
    errors = []
    for row in trace:
        require(math.isfinite(row['volts']) and 4.9 <= row['volts'] <= 8.4 and
                row['temp_C'] < 45 and row['current_raw'] < 150, 'out-of-bounds measurement')
        target = ref[max(0,bisect_right(times,row['command_timestamp'])-1)]
        expected = zero + round(target['goal_position'] * scale * 4096/(2*math.pi))
        require(row['goal_ticks'] == expected and row['enabled'] == target['torque_enable'],
                'target or torque schedule differs from the reference')
        if row['enabled']:
            errors.append(abs(row['goal_ticks']-row['ticks'])*360/4096)
    if pattern == 'lift_and_drop':
        require(any(not row['enabled'] for row in trace), 'missing unpowered phase')
    original, final = state['original'], state['final']
    require(all(final[k] == original[k] for k in ('21','22','23','55')), 'original settings not restored')
    if final['40'] != 0:
        recovery = json.loads(path.with_name('recovery.json').read_text())
        require(recovery['verified_after_second_off_command'] == 0, 'torque off not verified')
    return len(trace), mean(errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    matrix = Path(__file__).resolve().parents[1] / 'measurements/C044/horn-only-matrix.md'
    rows = {line.split('|')[1].strip(): line.split('|')[2:6]
            for line in matrix.read_text().splitlines() if line.startswith('|')}
    missing = []
    with ZipFile(args.archive) as archive:
        for pattern in PATTERNS:
            require(len(rows[pattern]) == len(GAINS), 'unexpected matrix width')
            for gain, cell in zip(GAINS,rows[pattern]):
                name = f'p{gain}-{pattern}'
                match = re.search(r'\[Complete\]\(([^)]+)\)',cell)
                if match is None:
                    missing.append(name)
                    continue
                path = matrix.parent / match[1]
                try:
                    count, error = verify(path,name,archive)
                except ValueError as exc:
                    raise SystemExit(f'{name}: {exc}') from exc
                print(f'{name}: {count} samples; powered tracking MAE {error:.2f}°')
    print(f'Verified {20-len(missing)} / 20; missing: {", ".join(missing) or "none"}')
    if missing and args.require_complete:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
