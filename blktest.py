import argparse
import subprocess
import os
import numpy as np
import json


def run_fio_test(test_name, filename):
    """Run fio tests and return the results"""
    iodepths = range(1, 257, 16) # step 16
    results = []

    for iodepth in iodepths:
        for rw in ['randread', 'randwrite']:
            output = f'{test_name}_{rw}_{iodepth}.json'
            command = [
                'fio',
                '--name', 'test_name',
                '--filename', filename,
                '--ioengine', 'libaio',
                '--direct', '1',
                '--bs', '4k',
                '--size', '1G',
                '--numjobs', '1',
                '--rw', rw,
                '--iodepth', str(iodepth),
                '--output-format', 'json',
                '--output', output
            ]

            subprocess.run(command, check=True)

            with open(output) as f:
                data = json.load(f)
                latency = data['jobs'][0]['latency']['mean']
                results.append((iodepth, rw, latency))

    return results


def plot_results(results, output_file):
    """Plot results by gnuplot"""
    data = {}
    for iodepth, rw, latency in results:
        if rw not in data:
            data[rw] = []

        data[rw].append((iodepth, latency))

    # Write data to file
    with open('latency_data.txt', 'w') as f:
        for rw in data:
            for iodepth, latency in data[rw]:
                f.write(f'{iodepth} {latency} {rw}\n')

    gnuplot_commands = f"""
        set terminal png
        set output '{output_file}'
        set title 'Latency vs I/O Depth'
        set xlabel 'I/O Depth'
        set ylabel 'Latency (ms)'
        plot 'latency_data.txt' using 1:2 title 'randread' with linespoints, \
            " using 1:2 title 'randwrite' with linespoints
    """

    # Run gnuplot
    with open('plot_commands.gp', 'w') as f:
        f.write(gnuplot_commands)

    subprocess.run(['gnuplot', 'plot_commands.gp'], check=True)


def main():
    parser = argparse.ArgumentParser(description='Тестирование производительности блочного устройства')
    parser.add_argument('-name', required=True, type=str, help='Имя теста')
    parser.add_argument('-filename', required=True, type=str, help='Путь до файла тестирования')
    parser.add_argument('-output', required=True, type=str, help='Путь до png-файла с графиком')

    args = parser.parse_args()

    results = run_fio_test(args.name, args.filename)

    plot_results(results, args.output)


if __name__ == '__main__':
    main()
    