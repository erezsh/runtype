# Run this script from the root directory of the repo
# Generate benchmarks JSONS:
mkdir tmp
pytest --benchmark-only --benchmark-json=tmp/bench_validation.json -k test_validation -x
pytest --benchmark-only --benchmark-json=tmp/bench_dispatch.json -k test_dispatch -x
python docs/plot_benchmarks.py tmp/bench_validation.json - docs/bench_validation.jpg
python docs/plot_benchmarks.py tmp/bench_dispatch.json A docs/bench_dispatch.jpg
python docs/plot_benchmarks.py tmp/bench_dispatch.json B docs/bench_dispatch_union.jpg