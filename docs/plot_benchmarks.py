# Create JSON using:
#
#   pytest --benchmark-only --benchmark-json=bench.json -x
#
# OR:
#   pytest --benchmark-only --benchmark-json=bench_validation.json -k test_validation -x
#   pytest --benchmark-only --benchmark-json=bench_dispatch.json -k test_dispatch -x
#

import sys
import json
import matplotlib.pyplot as plt

# Step 1: Read the JSON file
def read_benchmark_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# Step 2: Parse the JSON data
def parse_benchmarks(data, group_mod):
    grouped_data: dict[str, list] = {}

    for bench in data['benchmarks']:
        group = bench['group']
        if '$$' in group:
            name, mods = group.split('$$')
        else:
            name = group or bench['name']
            mods = ""
        libname = bench['params'].get('libname', '?')
        value = bench['stats']['median']
        skip = False
        if mods:
            for mod in mods.split():
                mod_name, mod_value = mod.split(':')
                if mod_name == 'div':
                    value /= float(mod_value)
                elif mod_name == 'group':
                    if group_mod and group_mod != mod_value:
                        skip = True
                else:
                    raise RuntimeError()

        if skip:
            continue
        value *= 1000000
        grouped_data.setdefault(name, []).append((name, value, libname))
    return grouped_data

LIB_NAME_ORDER = [
    "runtype",
    "beartype",
    "plum",
    "stdlib",
]
COLOR_BY_LIBNAME = {
    "plum": "purple",
    "beartype": "brown",
    "runtype": "green",
    "stdlib": "lightgrey",
}

# Step 3: Plot the data using matplotlib
def plot_benchmarks(data):
    groups = sorted(data.keys(), reverse=True)

    plt.figure(figsize=(10, 8))
    # plt.barh(names, values, color='skyblue')
    
    bars = []
    
    i = 0
    for group in groups:
        data[group].sort(key=lambda x: LIB_NAME_ORDER.index(x[2].split()[0]), reverse=True)
        for name, median, libname in data[group]:
            bars.append((name, libname, median, COLOR_BY_LIBNAME[libname.split()[0]]))
            i += 1
        bars.append(None)


    labels = []

    # Creating the horizontal bar chart
    for i, x in enumerate(bars):
        if x is None:
            labels.append('')
            continue
        (name, label, value, color) = x
        label = label if label not in plt.gca().get_legend_handles_labels()[1] else ""
        plt.barh(i, value, color=color, label=label)
        plt.text(value, i, '%.2f' % value, color=color, fontweight='bold', verticalalignment='center')
        labels.append(name)

    # Setting the y-ticks to show the labels correctly
    prev = None
    for i, l in reversed(list(enumerate(labels))):
        if prev == l:
            labels[i] = ''
        prev = l
        
    # Adding legend
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3, fancybox=True, shadow=True)
    plt.yticks(ticks=range(len(labels)), labels=labels)
    plt.xlabel('Median Duration in microseconds')  # Adjust label as per the metric used
    plt.title('Benchmark Results')
    plt.tight_layout(pad=1)

def main():
    file_path = sys.argv[1]
    group = sys.argv[2] if len(sys.argv) > 2 else None
    if group == '-':
        group = None
    save_to_file = sys.argv[3] if len(sys.argv) > 3 else None
    data = read_benchmark_json(file_path)
    data = parse_benchmarks(data, group)
    plot_benchmarks(data)
    if save_to_file:
        plt.savefig(save_to_file)
    else:
        plt.show()

if __name__ == '__main__':
    main()